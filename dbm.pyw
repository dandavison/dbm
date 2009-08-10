#!/usr/bin/env python

#    dbm : A music library tool : GUI

#    Dan Davison davison@stats.ox.ac.uk
#
#   dbm does a variety of useful things with a library of music
#   files:
#   - It generates random similar-music playlists for every artist in
#     the library.
#   - It creates a system of links to music by similar
#     artists, thus providing suggestions when choosing music to listen
#     to.
#   - It can report on albums that have untagged files or missing tracks.
#   - It can create lists of recommended similar artists that are not in
#     your library.
#   - It creates an alphabetical index of links to artists in your
#     music library

#    Please contact me [davison at stats dot ox dot ac dot uk] with
#    any questions about this software.

#    ---------------------------------------------------------------------
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program; if not, a copy is available at
#    http://www.gnu.org/licenses/gpl.txt
#    ---------------------------------------------------------------------

# This GUI code is based on example code distributed with the
# (excellent) book Rapid GUI Programming with Python and QT, by Mark
# Summerfield. Specifically, the MainWindow class is based on class
# MainWindow in chap06/imagechanger.pyw; the NewThread class is based
# on class Walker in chap19/walker.py, and the communication between
# the two follows class Form in chap19/pageindexer.pyw. I highly
# recommend that book.

# Notes

# The code in this file (the 'dbmg' module) implements a GUI for the
# core dbm code in module 'dbm'. dbm itself can be run as a command
# line program without this GUI.

# Program options are kept in a global Settings instance called
# settings. This class inherits from dbm.Settings, which in practice
# just means it inherits some static variables. dbm also works with a
# global variable called 'settings'; when running under the GUI,
# dbm.settings is a reference to dbmg.settings. When running alone,
# dbm.settings receives the command line options.

# Important variables

# dbm.root                the root of the data structure representing the library
# dbm.root.path           the path to the root of the library on disk
# settings.savefile       the file in which the scanned library is saved

from __future__ import with_statement
import os, sys, time, codecs
import platform
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import ui_settings_dlg
import qrc_resources
import dbm
import util

__version__ = dbm.__version__
__progname__ = dbm.__progname__
__author__ = 'Dan Davison'
__email__ = 'davison@stats.ox.ac.uk'
__doc__ = 'A tool for intelligent music playlist generation and library navigation.'
__url__ = 'http://www.stats.ox.ac.uk/~davison/software/dbm/dbm.php'
__log_to_file__ = True

# The following is a hack/solution that allows objects to be unpickled
# if they were pickled in a namespace in which these were not
# qualified by a module name. I.e. without the following lines,
# unpickling such an object would result in complaints that no global
# object named e.g. 'Root' exists.
Root = dbm.Root
Node = dbm.Node
Artist = dbm.Artist
ArtistNode = dbm.ArtistNode
# How come we don't need Track in track.py? There are Track instances
# in the pickled library trees.

class MainWindow(QMainWindow):
    """Class code descended from MainWindow in
    rgpwpyqt/chap06/imagechanger.pyw."""

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

# -----------------------------------------------
# dbm variables

        global settings
        settings = Settings()
        settings.savefile = None
        if __log_to_file__:
            dbm.sys.stdout = sys.stdout = settings.logfile
            dbm.sys.stderr = sys.stderr = settings.logfile
        dbm.settings = settings
        dbm.log = self.log
        dbm.root = None

# -----------------------------------------------
        self.dirty = False

        # self.listWidget = QListWidget()
        # if settings.disk_tree_view:
        #     self.diskTreeWidget = DiskTreeWidget()
        #     self.setCentralWidget(self.diskTreeWidget)

        #     logDockWidget = QDockWidget("Log", self)
        #     logDockWidget.setObjectName("LogDockWidget")
        #     logDockWidget.setAllowedAreas(Qt.TopDockWidgetArea|
        #                                   Qt.BottomDockWidgetArea)
        #     logDockWidget.setWidget(self.listWidget)
        #     self.addDockWidget(Qt.BottomDockWidgetArea, logDockWidget)

        # else:
        #     self.setCentralWidget(self.listWidget)

        # new configuration

        self.listWidget = QListWidget()
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        self.diskTreeWidget = DiskTreeWidget()
        self.artistsTreeWidget = ArtistsTreeWidget()

        self.view = None
        # self.setDiskViewDockWidget()
        self.setLogDockWidget()

        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.showMessage("%s version %s" % (__progname__,__version__), 5000)
        dbm.elog('dbm version %s\t%s' % (__version__, time.ctime()))


# Actions -- file

        libraryScanAction = self.createAction(
            "Sca&n library...", self.libraryScan,
            QKeySequence.New, "filenew",
            "Scan a music library and download last.fm similar artist data")
        libraryOpenAction = self.createAction(
            "&Open saved library...", self.libraryOpen,
            QKeySequence.Open, "fileopen",
            "Open a music library file saved previously by %s" % __progname__)
        libraryAddAction = self.createAction(
            "Add &folder to library...", self.libraryAdd,
            None, "add-folder",
            "Update the current library to reflect the addition of a new folder")
        libraryRefreshAction = self.createAction(
            "&Refresh library...", self.libraryRefresh,
            None, None,
            "Re-scan the entire library, but keep any downloaded last.fm data")
        librarySaveAction = self.createAction(
            "&Save library", self.librarySave,
            QKeySequence.Save, "filesave",
            "Save the current library and associated similar artist data")
        librarySaveAsAction = self.createAction(
            "Save &As...",
            self.librarySaveAs, icon="filesaveas",
            tip="Save the current library, and associated similar artist data, to a different file")
        musicspaceOpenAction = self.createAction(
            "Open &musicspace file...",
            self.musicspaceOpen,
            None, None, "Open csv format musicspace file")
        musicspaceSaveAction = self.createAction(
            "Save m&usicspace file...",
            self.musicspaceSave,
            None, None, "Write musicspace to file in csv format")
        fileQuitAction = self.createAction(
            "&Quit", self.close,
            "Ctrl+Q", "filequit", "Close %s" % __progname__)

# Actions -- actions
        setSimilarArtistsAction = self.createAction(
            "Retrieve &Last.fm similar artists",
            self.setLastfmSimilarArtists,
            None, 'last.fm', "Download last.fm similar artists if lacking")
        createLinksAction = self.createAction(
            "Generate Rockbox music &navigation links",
            self.createLinks,
            None, 'rockbox', "Create system of links for navigating the library on a Rockbox player")
        generatePlaylistsAction = self.createAction(
            "Generate &playlists",
            self.generatePlaylists,
            None, 'playlists', "Generate all playlists")
        albumArtDownloadAction = self.createAction(
            "Download album art", self.albumArtDownload,
            None, "None",
            "Download all album art")

# Actions -- settings
#         setPathToRockboxAction = self.createAction("Set path to &Rockbox player",
#                 self.setPathToRockbox,
#                 None, 'rockbox',
#                 "Set path to rockbox player to ensure that file paths are constructed correctly")
        setSettingsAction = self.createAction("&Settings",
                                              self.setSettings,
                                              None, 'settings',
                                              "Set %s options" % __progname__)

# Actions -- view
        diskTreeWidgetToggleExpansionAction = self.createAction(
            "Expand / Collapse",
            self.diskTreeWidget.toggleExpansion,
            None, None, "Expand / Hide all nodes in the disk tree view")

        diskTreeWidgetAction = self.createAction(
            "File view",
            self.setDiskViewDockWidget,
            None, None, "View the library as it is stored on disk, with tag information")

        artistsTreeWidgetAction = self.createAction(
            "Artists view",
            self.setArtistsViewDockWidget,
            None, None, "View the library by artists")

# Actions -- etc
        abortThreadAction = self.createAction(
            "Abort",
            self.abortThread,
            "Ctrl+C", "dialog-cancel", "Abort current process")

        helpAboutAction = self.createAction("&About %s" % __progname__,
                                            self.helpAbout)
        helpHelpAction = self.createAction("&Help", self.helpHelp,
                                           QKeySequence.HelpContents)

# Menus -- file
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenuActions = (libraryScanAction, libraryOpenAction,
                                librarySaveAction, librarySaveAsAction,
                                None,
                                libraryAddAction, libraryRefreshAction,
                                None,
                                musicspaceOpenAction, musicspaceSaveAction,
                                None,
                                fileQuitAction)
        self.connect(self.fileMenu, SIGNAL("aboutToShow()"), self.updateFileMenu)

# Menus -- view
        viewMenu = self.menuBar().addMenu("&View")
        self.addActions(viewMenu,
                        (diskTreeWidgetAction, diskTreeWidgetToggleExpansionAction,
                         None,
                         artistsTreeWidgetAction))

# Menus -- actions
        self.libMenu = self.menuBar().addMenu("&Tasks")
        self.addActions(self.libMenu,
                        (setSimilarArtistsAction, None,
                         createLinksAction, generatePlaylistsAction, None,
                         albumArtDownloadAction, None,
                         setSettingsAction))

# # Menus -- settings
#         self.settingsMenu = self.menuBar().addMenu("&Settings")
#         self.addActions(self.settingsMenu,
#                         (setSettingsAction,)) # setPathToRockboxAction

# Menus -- help
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpAboutAction, helpHelpAction))

        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        self.addActions(fileToolbar, (libraryScanAction, libraryOpenAction, librarySaveAsAction,
                                      libraryAddAction, setSettingsAction,
                                      setSimilarArtistsAction, createLinksAction, generatePlaylistsAction))

# Etc
        qSettings = QSettings()
        self.recentFiles = qSettings.value("RecentFiles").toStringList()
        size = qSettings.value("MainWindow/Size",
                               QVariant(QSize(600, 500))).toSize()
        self.resize(size)
        position = qSettings.value("MainWindow/Position",
                                   QVariant(QPoint(0, 0))).toPoint()
        self.move(position)
        self.restoreState(
            qSettings.value("MainWindow/State").toByteArray())

        self.setWindowTitle("%s" % __progname__)
        self.updateFileMenu()
        # QTimer.singleShot(0, self.loadInitialFile)

        # persistent_settings is a list of
        # (setting_name, QVariant_cast_method) tuples
        dbm.elog('Loading previous settings')
        for setting in settings.persistent_settings:
            if qSettings.contains(setting[0]):
                name = setting[0]
                val = setting[1](qSettings.value(setting[0])) or None
                try:
                    print_val = str(val)
                except:
                    val = 'Unprintable value'
                dbm.elog('%s:  %s' % (name, print_val))
                setattr(settings, name, val)

# Run actions in a new thread
# code descended from Form.__init__() rgpwpyqt/chap19/pageindexer.pyw
# self.lock = QReadWriteLock() # Not using this

        self.threads = [
            ('albumArtDownloader', AlbumArtDownloader, self.finishedDownloadingAlbumArt),
            ('libraryScanner', LibraryScanner, self.finishedScanningLibrary),
            ('libraryLoader', LibraryLoader, self.finishedLoadingLibrary),
            ('librarySaver', LibrarySaver, self.finishedSavingLibrary),
            ('libraryGrafter', LibraryGrafter, self.finishedGraftingLibrary),
            ('lastfmSimilarArtistSetter', LastfmSimilarArtistSetter,
             self.finishedSettingLastfmSimilarArtists),
            ('linksCreator', LinksCreator, self.finishedCreatingLinks),
            ('playlistGenerator', PlaylistGenerator, self.finishedGeneratingPLaylists)]

        for attr_name, constructor, finisher in self.threads:
            thread = constructor()
            setattr(self, attr_name, thread)
            self.connect(thread, SIGNAL("log(QString)"), self.log)
            self.connect(thread, SIGNAL("logi(QString)"), self.logi)
            self.connect(thread, SIGNAL("finished(bool)"), finisher)

    def setDiskViewDockWidget(self):
        if self.view == 'Disk':
            return
        # if self.view == 'Artists':
        #     self.removeDockWidget(self.viewDockWidget)
        self.viewDockWidget = QDockWidget("File view", self)
        self.viewDockWidget.setObjectName("DiskViewDockWidget")
        self.viewDockWidget.setAllowedAreas(Qt.TopDockWidgetArea)
        self.viewDockWidget.setWidget(self.diskTreeWidget)
        self.addDockWidget(Qt.TopDockWidgetArea, self.viewDockWidget)
        self.view = 'Disk'

    def setArtistsViewDockWidget(self):
        if self.view == 'Artists':
            return
        # if self.view == 'Disk':
        #     self.removeDockWidget(self.viewDockWidget)
        self.viewDockWidget = QDockWidget("Artists view", self)
        self.viewDockWidget.setObjectName("ArtistsViewDockWidget")
        self.viewDockWidget.setAllowedAreas(Qt.TopDockWidgetArea)
        self.viewDockWidget.setWidget(self.artistsTreeWidget)
        self.addDockWidget(Qt.TopDockWidgetArea, self.viewDockWidget)
        self.view = 'Artists'

    def setLogDockWidget(self):
        logDockWidget = QDockWidget("Log", self)
        logDockWidget.setObjectName("LogDockWidget")
        # logDockWidget.setAllowedAreas(Qt.TopDockWidgetArea|
        #                               Qt.BottomDockWidgetArea)
        # logDockWidget.setWidget(self.listWidget)
        logDockWidget.setAllowedAreas(Qt.BottomDockWidgetArea)
        logDockWidget.setWidget(self.listWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, logDockWidget)

    def loadInitialFile(self):
        qSettings = QSettings()
        fname = unicode(qSettings.value("LastFile").toString(), 'utf-8')
        if fname and QFile.exists(fname):
            self.libraryLoad(fname)

    def updateStatus(self, message):
        self.log(message)
        if dbm.root is not None:
            if settings.savefile is not None:
                self.setWindowTitle("%s - %s[*]" %
                                    (__progname__, os.path.basename(settings.savefile)))
            else:
                self.setWindowTitle("%s - %s[*]" % (__progname__, dbm.root.path))
        else:
            self.setWindowTitle("%s[*]" % __progname__)

        self.setWindowModified(self.dirty)

    def log(self, message, colour=None, inplace=False):
        #        self.statusBar().showMessage(message, 5000)
        if inplace and self.listWidget.currentItem():
            self.listWidget.currentItem().setText(message)
        else:
            new_item = QListWidgetItem(message)
            self.listWidget.addItem(new_item)
            self.listWidget.scrollToItem(new_item)
            self.listWidget.setCurrentItem(new_item)
            self.listWidget.currentItem().setSelected(False)
        if colour:
            self.listWidget.currentItem().setTextColor(colour)

    def logi(self, message, colour=None):
        self.log(message, colour, inplace=True)

    def okToContinue(self):
        if self.libraryScanner.isRunning() or \
                self.lastfmSimilarArtistSetter.isRunning() or \
                self.linksCreator.isRunning() or \
                self.playlistGenerator.isRunning():
            reply = QMessageBox.question(self,
                                         "%s - Warning" % __progname__,
                                         "%s is busy -- OK to continue?\n(Abort will quit the program)" % __progname__,
                                         QMessageBox.Ok|QMessageBox.Abort)
            if reply == QMessageBox.Ok:
                return False
            elif reply == QMessageBox.Abort:
                self.close()
        if self.dirty:
            reply = QMessageBox.question(self,
                            "%s - Unsaved Changes" % __progname__,
                            "Save unsaved changes to library data?",
                            QMessageBox.Yes|QMessageBox.No|
                            QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                self.librarySave()
                return False
        return True

    def setSettings(self):
        if not self.okToContinue():
            return
        dialog = SettingsDlg(self)
        if dialog.exec_():
            self.updateStatus("New settings recorded")

    def updateFileMenu(self):
        self.fileMenu.clear()
        self.addActions(self.fileMenu, self.fileMenuActions[:-1])
        current = QString(settings.savefile) \
                if settings.savefile is not None else None
        recentFiles = []
        for fname in self.recentFiles:
            if fname != current and QFile.exists(fname):
                recentFiles.append(fname)
        if recentFiles:
            self.fileMenu.addSeparator()
            for i, fname in enumerate(recentFiles):
                action = QAction(QIcon(":/folder-sound.png"), "&%d %s" % (
                        i + 1, QFileInfo(fname).fileName()), self)
                action.setData(QVariant(fname))
                self.connect(action, SIGNAL("triggered()"),
                             self.libraryLoad)
                self.fileMenu.addAction(action)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.fileMenuActions[-1])


    def addRecentFile(self, fname):
        if fname is None:
            return
        if not self.recentFiles.contains(fname):
            self.recentFiles.prepend(QString(fname))
            while self.recentFiles.count() > 9:
                self.recentFiles.takeLast()


    def closeEvent(self, event):
        if self.okToContinue():
            # TMP
            self.diskTreeWidget.close()
            qSettings = QSettings()
            filename = QVariant(QString(settings.savefile)) \
                    if settings.savefile is not None else QVariant()
            qSettings.setValue("LastFile", filename)
            recentFiles = QVariant(self.recentFiles) \
                    if self.recentFiles else QVariant()
            qSettings.setValue("RecentFiles", recentFiles)
            qSettings.setValue("MainWindow/Size", QVariant(self.size()))
            qSettings.setValue("MainWindow/Position",
                    QVariant(self.pos()))
            qSettings.setValue("MainWindow/State",
                    QVariant(self.saveState()))

            # persistent_settings is a list of
            # (setting_name, QVariant_cast_method) tuples
            for setting in [x[0] for x in settings.persistent_settings]:
                qSettings.setValue(setting,
                                   QVariant(getattr(settings, setting)))
        else:
            event.ignore()

    def libraryScan(self):
        # descended from Form.setPath() in rgpwpyqt/chap019/pageindexer.pyw
        # Ultimately one might want a separate library scan dialog,
        # with its own scan log. Maybe. See the Form.setPath() code
        # for ideas on doing that.
        if not self.okToContinue(): return
        path = QFileDialog.getExistingDirectory(
            self, "%s - Choose a music library to scan" % __progname__,
            settings.path_to_rockbox or QDir.homePath())
        if path.isEmpty(): return
        path = processPath(path)

        self.libraryScanner.initialize(path)
        self.libraryScanner.start()

    def libraryRefresh(self):
        # descended from libraryScan()
        if not self.okToContinue(): return
        self.libraryScanner.initialize(dbm.root.path, dbm.root.simartists)
        self.libraryScanner.start()

    def libraryOpen(self):
        if not self.okToContinue():
            return
        dir = os.path.dirname(settings.savefile) \
                if settings.savefile is not None else "."
        formats = ['*.dbm']
        savefile = QFileDialog.getOpenFileName(self,
                        "%s - Choose a saved music library" % __progname__, dir,
                        "%s library files (%s)" % (__progname__, " ".join(formats)))
        savefile = processPath(savefile)
        if savefile:
            self.libraryLoad(savefile)

    def libraryLoad(self, savefile=None):
        """This is based, to some extent, on MainWindow.loadFile() in
        imagechanger.pyw. I don't really understand the initial stuff."""
        if savefile is None:
            action = self.sender()
            if isinstance(action, QAction):
                savefile = unicode(action.data().toString())
                if not self.okToContinue():
                    return
            else:
                return
        if not savefile: return
        # end don't really understand
        self.log('Loading saved library file %s...' % savefile)
        self.libraryLoader.initialize(savefile)
        self.libraryLoader.start()

    def librarySave(self, fname=None):
        if self.alertIfNoLibrary(): return
        fname = fname or settings.savefile
        if fname is None:
            self.librarySaveAs()
        else:
            self.log("Saving library to %s..." % fname)
            self.librarySaver.initialize(fname)
            self.librarySaver.start()

    def librarySaveAs(self):
        if self.alertIfNoLibrary(): return
        fname = settings.savefile or "."
        fname = QFileDialog.getSaveFileName(
            self,
            "%s - Save Library" % __progname__, fname)
        if fname.isEmpty(): return
        fname = processPath(fname)
        if "." not in fname: fname += '.dbm'
        self.librarySave(fname)

    def musicspaceOpen(self):
        if self.alertIfNoLibrary():
            return
        if not self.okToContinue():
            return
        path = QFileDialog.getOpenFileName(
            self, "%s - Open musicspace csv file" % __progname__,
            os.path.dirname(settings.musicspace_file) \
                if settings.musicspace_file else QDir.homePath(),
            "*.csv")
        if not path.isEmpty():
            path = processPath(path)
            self.populate_musicspace(path)

    def populate_musicspace(self, path):
        self.log('Opening musicspace file %s...' % path)
        try:
            with open(path, 'r') as f:
                dbm.root.populate_musicspace(f)
            settings.musicspace_file = path
            settings.musicspace_ready = True
            self.log('Loaded %d-dimensional music space' % settings.musicspace_dimension)
        except:
            self.log('Failed!')
            raise

    def musicspaceSave(self):
        if not self.okToContinue():
            return
        path = QFileDialog.getSaveFileName(
            self, "%s - Save musicspace to file" % __progname__,
            os.path.dirname(settings.musicspace_file) \
                if settings.musicspace_file else QDir.homePath(),
            "*.csv")
        if not path.isEmpty():
            path = processPath(path)
            self.log('Saving musicspace to %s...' % path)
            try:
                with codecs.open(path, 'w', 'utf-8') as f:
                    dbm.root.write_musicspace_file(f)
                settings.musicspace_file = path
                self.log('Done')
            except:
                self.log('Failed!')
                raise

    def albumArtDownload(self):
        if self.alertIfNoLibrary(): return
        if not self.okToContinue(): return
        path = QFileDialog.getExistingDirectory(
            self,
            "%s - Choose a folder to receive the album art" % __progname__,
            QDir.homePath())
        if path.isEmpty(): return
        settings.albumartdir = processPath(path)
        if not os.path.exists(settings.albumartdir):
            os.mkdir(settings.albumartdir)
        self.albumArtDownloader.initialize()
        self.albumArtDownloader.start()

    def libraryAdd(self):
        if not self.okToContinue(): return
        if self.alertIfNoLibrary(): return
        path = QFileDialog.getExistingDirectory(self,
                   "%s - Choose a music folder to add to the library" % __progname__,
                                                dbm.root.path)
        if path.isEmpty(): return
        path = processPath(path)
        self.libraryGrafter.initialize(path)
        self.libraryGrafter.start()

    def alertIfNoLibrary(self):
        if dbm.root is None:
            QMessageBox.warning(self,
                                "%s - Warning" % __progname__,
                                "There is no active library.\n" + \
                                    "Please load a saved library or initiate a new scan.")
            return True
        return False


    def alertIfDirNotEmpty(self, path, title='Directory not empty'):
        if os.listdir(path):
            QMessageBox.warning(self,
                                "%s - %s" % (__progname__, title),
                                "The folder %s is not empty. Please choose an empty folder for output." %
                                path)
            return True
        return False

    def ensure_output_dir_exists(self):
        if settings.output_dir is None:
            path = QFileDialog.getExistingDirectory(
                self,
                "Choose a location for %s to save folders containing" % __progname__ +
                "links, playlists, biographies etc.",
                settings.path_to_rockbox)
            if path.isEmpty(): return False
            settings.output_dir = processPath(path)
        return True

    def setLastfmSimilarArtists(self):
        if not self.okToContinue(): return
        if self.alertIfNoLibrary(): return
        self.lastfmSimilarArtistSetter.initialize()
        self.lastfmSimilarArtistSetter.start()


    def createLinks(self):
        if self.alertIfNoLibrary(): return
        if not self.ensure_output_dir_exists(): return
        if not self.okToContinue(): return
        
        if settings.path_to_rockbox is None:
            QMessageBox.information(self,
              "%s - Set location of Rockbox player." % __progname__,
              "Please set the location of your Rockbox music player (Tasks -> Settings).")
            return

        prev_val = settings.links_path
        settings.links_path = os.path.join(settings.output_dir, 'Links')

        if not os.path.exists(settings.links_path):
            try:
                os.mkdir(settings.links_path)
            except:
                msg = 'Failed to make new directory %s' % settings.links_path
                self.log(msg)
                dbm.elog(msg)
                return
        elif self.alertIfDirNotEmpty(settings.links_path, 'Navigation links folder not empty'):
            settings.links_path = prev_val
            return

        self.log('Creating rockbox library navigation links...')
        dirs = dict(lastfm_similar='Last.fm Similar',
                    musicspace_similar='Musicspace Similar',
                    AtoZ='A-Z',
                    tags='Artist Tags')
        dirs = dict(zip(dirs.keys(),
                        [os.path.join(settings.links_path, d) for d in dirs.values()]))
        dirs['bios'] = os.path.join(os.path.dirname(settings.output_dir), 'Biographies')
        for d in dirs.values():
            try:
                if not os.path.exists(d): os.mkdir(d)
            except:
                dbm.elog('ERROR: Failed to create output directory %s' % d)

        self.linksCreator.initialize(dirs)
        self.linksCreator.start()
        
    def generatePlaylists(self):
        if self.alertIfNoLibrary(): return
        if not self.ensure_output_dir_exists(): return
        if not self.okToContinue(): return
        if settings.path_to_rockbox is None:
            QMessageBox.information(self,
              "%s - Set location of Rockbox player." % __progname__,
              "Please set the location of your Rockbox music player (Tasks -> Settings).")
            return

        prev_val = settings.playlists_path
        settings.playlists_path = os.path.join(settings.output_dir, 'Playlists')        
        if not os.path.exists(settings.playlists_path):
            try:
                os.mkdir(settings.playlists_path)
            except:
                msg = 'Failed to make new directory %s' % settings.playlists_path
                self.log(msg)
                dbm.elog(msg)
                return
        elif self.alertIfDirNotEmpty(settings.playlists_path, 'Playlist folder not empty'):
            settings.playlists_path = prev_val
            return

        self.log('Generating playlists...')
        dirs = dict(lastfm_similar='Last.fm_Similar',
                    musicspace_similar='Musicspace_Similar',
                    single_artists='Single_Artists',
                    all_artists='All_Artists',
                    tags = 'Artist Tags')
        
        dirs = dict(zip(dirs.keys(),
                        [os.path.join(settings.playlists_path, d) for d in dirs.values()]))
        for d in dirs.values():
            if not os.path.exists(d): os.mkdir(d)
        self.playlistGenerator.initialize(dirs)
        self.playlistGenerator.start()

    # The following is an unsatisfactory arrangement because of the
    # code duplication in the finishedDoingSomething()
    # methods. However, I couldn't easily / be bothered to work out
    # how to do it. The problem is I don't currently know how to make
    # an signal connect to a slot and pass that slot multiple
    # arguments, but I haven't really RTFM. So, it just gets passed
    # the 'completed' flag. I tried passing the QThread instance
    # (which would allow access to thread.completed and
    # thread.wait()), but got an error message:

    # QObject::connect: Cannot queue arguments of type 'QThread'
    # (Make sure 'QThread' is registered using qRegisterMetaType().)

    def finishedScanningLibrary(self, completed):
        # descended from Form.finished() and Form.finishedIndexing()
        # rgpwpyqt/chap19/pageindexer.pyw
        settings.savefile = None
        self.updateStatus("Done" if completed else "Stopped")
        self.dirty = True
        if completed:
            self.artistsTreeWidget.populate(sorted(dbm.root.artists.values()))
            self.setArtistsViewDockWidget()
            self.diskTreeWidget.populate(dbm.root)
            self.setDiskViewDockWidget()
        self.libraryScanner.wait()

    def finishedLoadingLibrary(self, completed):
        if completed:
            self.diskTreeWidget.populate(dbm.root)
            self.artistsTreeWidget.populate(sorted(dbm.root.artists.values()))
            self.setArtistsViewDockWidget()
            self.setDiskViewDockWidget()
            self.dirty = False
            self.addRecentFile(settings.savefile)
        else:
            self.dirty = True
        self.updateStatus("Loaded library with %d artists" % len(dbm.root.artists) \
                              if completed else "Stopped")
        self.libraryLoader.wait()

    def finishedSavingLibrary(self, completed):
        if completed:
            self.dirty = False
            self.addRecentFile(settings.savefile)
        else:
            self.dirty = True
        self.updateStatus("Done" if completed else "Stopped")
        self.librarySaver.wait()

    def finishedDownloadingAlbumArt(self, completed):
        self.updateStatus("Done" if completed else "Stopped")
        self.albumArtDownloader.wait()

    def finishedGraftingLibrary(self, completed):
        self.updateStatus("Done" if completed else "Stopped")
        self.dirty = True
        self.libraryGrafter.wait()

    def finishedSettingLastfmSimilarArtists(self, completed):
        # amalgamation of Form.finished() and Form.finishedIndexing()
        # rgpwpyqt/chap19/pageindexer.pyw
        self.updateStatus("Done" if completed else "Stopped")
        self.dirty = True
        self.lastfmSimilarArtistSetter.wait()

    def finishedCreatingLinks(self, completed):
        # amalgamation of Form.finished() and Form.finishedIndexing()
        # rgpwpyqt/chap19/pageindexer.pyw
        self.updateStatus("Done" if completed else "Stopped")
        self.linksCreator.wait()

    def finishedGeneratingPLaylists(self, completed):
        # amalgamation of Form.finished() and Form.finishedIndexing()
        # rgpwpyqt/chap19/pageindexer.pyw
        self.updateStatus("Done" if completed else "Stopped")
        self.playlistGenerator.wait()

    def abortNewThread(self):
        # Form.reject() in pageindexer.pyw so accept method is Form
        # specific and without analog here?

        # This doesn't work currently -- it freezes the UI.

        if self.newThread.isRunning():
            self.newThread.stop()
            self.finishedNewThread(False)
#         else:
#             self.accept()

    def abortThread(self):
        for attr_name, constructor, finisher in self.threads:
            thread = getattr(self, attr_name)
            if thread.isRunning():
                self.log("Aborting %s" % attr_name)
                thread.stop()
                thread.terminate()
                # thread.wait()
                # finisher(False)

    def helpAbout(self):
        QMessageBox.about(self, "About %s" % __progname__,
                          """<b>%s</b> v %s <p>Copyright
                &copy; Dan Davison davison@stats.ox.ac.uk
                <p>Intelligent playlist generation, and music library
                navigation system for Rockbox.  <p>Python %s - Qt %s - PyQt %s on %s
                <p>
                %s is free software released under the GNU General Public License
                """ % (
                __progname__, __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system(), __progname__))


    def helpHelp(self):
        form = helpform.HelpForm("index.html", self)
        form.show()


    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None,
                     checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action



    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


class DiskTreeWidget(QTreeWidget):
    def toggleExpansion(self):
        if self.is_expanded:
            self.collapseAll()
            self.topLevelItem(0).setExpanded(True)
            self.is_expanded = False
        else:
            self.expandAll()
            self.is_expanded = True

    def node_attributes(self, item):
        attr_names = ['', 'Artist', 'Album', 'Album artist']
        att = dict(zip(attr_names, [''] * len(attr_names)))
        att[''] = os.path.basename(item.path)
        if isinstance(item, dbm.Node):
            node = item
            att['Artist'] = str(len(node.dbm_artistids))
        elif isinstance(item, dbm.track.Track):
            track = item
            att['Artist'] = track.artistname
            att['Album'] = track.releasename
            ## We only show Albumartist if it differs from Artist
            if track.albumartistid:
                if track.albumartistid != track.artistid:
                    att['Album artist'] = track.albumartistname or track.albumartistid
            elif track.albumartistname:
                if track.albumartistname != track.artistname:
                    att['Album artist'] = track.albumartistname
            else:
                att['Album artist'] = '?'

        return [(name, att[name]) for name in attr_names]

    def addNode(self, node, parent):
        # parent =  node.parent.diskTreeWidgetItem \
        #     if node.parent else self
        node.diskTreeWidgetItem = QTreeWidgetItem(
            parent,
            [a[1] for a in self.node_attributes(node)])
        for track in sorted(node.tracks):
            attrs = self.node_attributes(track)
            attr_names = [a[0] for a in attrs]
            attrs = [a[1] for a in attrs]
            trackItem = QTreeWidgetItem(node.diskTreeWidgetItem, attrs)
            column = dict(zip(attr_names, range(len(attr_names))))
            trackItem.setTextColor(column['Artist'],
                                   Qt.darkGreen if track.artistid else Qt.red)
            trackItem.setTextColor(column['Album'],
                                   Qt.darkGreen if track.releaseid else Qt.red)
            trackItem.setTextColor(column['Album artist'],
                                   Qt.darkGreen if track.albumartistid else Qt.red)

        for subtree in sorted(node.subtrees):
            self.addNode(subtree, node.diskTreeWidgetItem)


    def populate(self, root, selectedNode = None):
        # descended from populateTree() in rgpwpyqt/chap14/ships-dict.pyw
        selected = None # not maintaining selectedness at the moment
        self.clear()
        item_attrs = self.node_attributes(root)
        self.setColumnCount(len(item_attrs))
        self.setHeaderLabels([a[0] for a in item_attrs])
        self.setItemsExpandable(True)
        self.addNode(root, self)
        self.topLevelItem(0).setExpanded(True)
        self.is_expanded = False
        for i in range(len(item_attrs)):
            self.resizeColumnToContents(i)
        if selected is not None:
            selected.setSelected(True)
            self.setCurrentItem(selected)

class ArtistsTreeWidget(DiskTreeWidget):
    def artist_attributes(self, artist):
        attr_names = ['', 'Similar Artists']
        att = dict(zip(attr_names, [''] * len(attr_names)))
        att[''] = artist.name
        att['Similar Artists'] = str(len(artist.simartists))
        return [(name, att[name]) for name in attr_names]

    def populate(self, artists):
        self.clear()
        if len(artists) == 0: return
        self.setItemsExpandable(True)
        first = True
        for artist in artists:
            attrs = self.artist_attributes(artist)
            attr_names = [a[0] for a in attrs]
            attrs = [a[1] for a in attrs]
            if first:
                self.setColumnCount(len(attrs))
                self.setHeaderLabels(attr_names)
                first = False
            artistItem = QTreeWidgetItem(self, attrs)
            for artist_node in artist.subtrees:
                self.addNode(artist_node.node, parent=artistItem)

class Settings(dbm.Settings):
    def __init__(self):
        dbm.Settings.__init__(self)
        self.gui = True
        self.disk_tree_view = True
        self.savefile = None
        self.path_to_rockbox = None
        self.output_dir = None
        self.links_path = None
        self.playlists_path = None
        self.musicspace_ready = False
        self.musicspace_file = None
        self.musicspace_dropoff_param = 3.0
        if __log_to_file__:
            self.logfile = codecs.open('dbmlog.txt', 'w', 'utf-8')
        else:
            self.logfile = sys.stderr
        self.query_lastfm = True
        self.lastfm_user_names = []
        self.lastfm_user_history_nweeks = 4
        self.numtries = 5

        self.minTagArtists = 1 # min artists per tag for tag to get links and lists
        self.minArtistTracks = 1 # min tracks per artist for artist to get links and lists

        self.target = 'rockbox'
        self.quiet = False
        self.albumartdir = None

        ## This is fairly obscure.
        ## See the code [[for%20setting%20in%20settings%20persistent_settings][here]]
        self.persistent_settings = \
            [('path_to_rockbox', lambda(qv): unicode(qv.toString(), 'utf-8')),
             ('output_dir', lambda(qv): unicode(qv.toString(), 'utf-8')),
             ('musicspace_file', lambda(qv): unicode(qv.toString(), 'utf-8')),
             ('musicspace_dropoff_param', lambda(qv): qv.toDouble()[0]),
             ('minArtistTracks', lambda(qv): qv.toInt()[0]),
             ('minTagArtists', lambda(qv): qv.toInt()[0]),
             ('numtries', lambda(qv): qv.toInt()[0]),
             ('lastfm_user_names', lambda(qv): map(str, qv.toStringList())),
             ('target', lambda(qv): unicode(qv.toString(), 'utf-8'))]

class SettingsDlg(QDialog, ui_settings_dlg.Ui_Dialog):

    def __init__(self, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle("%s - Settings" % __progname__)

        for text in ['rockbox']: self.targetComboBox.addItem(text)

        self.lastfmQueriesComboBox.addItems(map(str, range(1, 11)))
        self.minArtistTracksComboBox.addItems(map(str, range(1, 11)))
        self.minTagArtistsComboBox.addItems(map(str, range(1, 20)))

        self.update()
        
        connections = [
            ('targetComboBox', "currentIndexChanged(int)", 'setTarget'),
            ('targetDevHelpButton', '', 'targetDevHelp'),

            ('rockboxPathChangeButton', '', 'setPathToRockbox'),
            ('rockboxPathHelpButton', '', 'rockboxPathHelp'),

            ('outputFolderChangeButton', '', 'setPathToOutputFolder'),
            ('outputFolderHelpButton', '', 'outputFolderHelp'),

            ('musicspaceFileChangeButton', '', 'setMusicspaceFile'),
            ('musicspaceFileHelpButton', '', 'musicspaceFileHelp'),

            ('minArtistTracksComboBox', 'currentIndexChanged(int)', 'setMinArtistTracks'),
            ('minArtistTracksHelpButton', '', 'minArtistTracksHelp'),

            ('minTagArtistsComboBox', 'currentIndexChanged(int)', 'setMinTagArtists'),
            ('minTagArtistsHelpButton', '', 'minTagArtistsHelp'),

            ('lastfmUsersLineEdit', 'editingFinished()', 'setLastfmUsers'),
            ('lastfmUsersHelpButton', '', 'lastfmUsersHelp'),

            ('lastfmQueriesComboBox', 'currentIndexChanged(int)', 'setLastfmNumTries'),
            ('lastfmQueriesHelpButton', '', 'lastfmQueriesHelp'),

            ('musicspaceDropoffSpinBox', 'valueChanged(double)', 'setMusicspaceDropoff'),
            ('musicspaceDropoffHelpButton', '', 'musicspaceDropoffHelp')]
        
        for ui_element, signal, action in connections:
            try:
                self.connect(getattr(self, ui_element),
                             SIGNAL(signal or 'clicked()'),
                             getattr(self, action))
            except:
                print('%s %s %s\n' % (ui_element, signal, action))
                raise

    def update(self):
        if settings.target != 'rockbox':
            settings.path_to_rockbox = None
        elif settings.output_dir is None:
            settings.output_dir = settings.path_to_rockbox

        if settings.output_dir is not None:
            settings.links_path = os.path.join(settings.output_dir, 'Links')
            settings.playlists_path = os.path.join(settings.output_dir, 'Playlists')

        self.rockboxPathChangeButton.setText(settings.path_to_rockbox or 'None')
        self.outputFolderChangeButton.setText(settings.output_dir or 'None')

        self.lastfmUsersLineEdit.setText(', '.join(settings.lastfm_user_names))
        self.musicspaceFileChangeButton.setText(settings.musicspace_file or 'None')
        self.musicspaceDropoffSpinBox.setValue(settings.musicspace_dropoff_param)

        self.lastfmQueriesComboBox.setCurrentIndex(settings.numtries - 1)
        self.minArtistTracksComboBox.setCurrentIndex(settings.minArtistTracks - 1)
        self.minTagArtistsComboBox.setCurrentIndex(settings.minTagArtists - 1)

    def setTarget(self):
        settings.target = unicode(self.targetComboBox.currentText(), 'utf-8')
        self.update()
        self.parent.log('Set target device to %s' % settings.target)

    def setPathToRockbox(self):
        if settings.target != 'rockbox':
            return
        path = QFileDialog.getExistingDirectory(self,
                   "%s - Select location of rockbox device" % __progname__,
                   os.path.dirname(dbm.root.path) if dbm.root else QDir.homePath())
        if path.isEmpty(): return
        settings.path_to_rockbox = processPath(path)
        self.update()
        self.parent.log('Set location of Rockbox device to %s' % settings.path_to_rockbox)

    def setPathToOutputFolder(self):
        path = QFileDialog.getExistingDirectory(self,
                   "%s - Select output folder" % __progname__,
                   os.path.dirname(dbm.root.path) if dbm.root else QDir.homePath())
        if path.isEmpty(): return
        path = processPath(path)
        # if self.parent.alertIfDirNotEmpty(path, 'Selected output folder not empty'):
        #     return
        settings.output_dir = path
        self.update()
        self.parent.log('Set output folder to %s' % settings.output_dir)

    def setLastfmUsers(self):
        text = unicode(self.lastfmUsersLineEdit.text())
        names = [s.strip() for s in text.split(',')]
        settings.lastfm_user_names = names
        self.update()
        for name in names:
            self.parent.log('Added last.fm username %s' % name)

    def setMusicspaceFile(self):
        path = QFileDialog.getOpenFileName(self,
                                            "%s - Select musicspace .tsv file" % __progname__,
                                            os.path.dirname(dbm.root.path) if dbm.root else QDir.homePath(),
                                            "*.csv")
        if path.isEmpty(): return
        settings.musicspace_file = processPath(path)
        self.update()
        self.parent.log('Set musicspace file to %s' % settings.musicspace_file)

    def setLastfmNumTries(self):
        settings.numtries = int(self.lastfmQueriesComboBox.currentText())
        self.parent.log('Set maximum number of last.fm queries to %d' % settings.numtries)

    def setMinArtistTracks(self):
        settings.minArtistTracks = int(self.minArtistTracksComboBox.currentText())
        self.parent.log('Set minimum tracks for artist to get links/lists to %d' \
                            % settings.minArtistTracks)

    def setMinTagArtists(self):
        settings.minTagArtists = int(self.minTagArtistsComboBox.currentText())
        self.parent.log('Set minimum artists for tag to get links/lists to %d' \
                            % settings.minTagArtists)

    def setMusicspaceDropoff(self):
        settings.musicspace_dropoff_param = float(self.musicspaceDropoffSpinBox.value())

    def targetDevHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "If you want to create links and playlists that will work on a music player running rockbox, then select 'rockbox'. The alternative would be to create links and playlists that will work on your computer, although that's not available yet (let me know if you want it).")

    def rockboxPathHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "If you have selected rockbox as your target, then use this button to indicate the location of your rockbox device. So, on Windows that might be something like E:, and on linux it might be something like /media/disk")

    def outputFolderHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "This is where %s will store the various folders of links and playlists that it creates. It would make sense for this to be a folder at the root of your rockbox player's file system; so something like E:\%s on Windows, or /media/mp3player/%s on linux." % 
            (__progname__,__progname__,__progname__))

    def minArtistTracksHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "How many tracks does an artist have to have in your collection in order for similar music links and playlists to be created for that artist? This option might be used to avoid making similar artist links and playlists for obscure artists that you've never actually heard of.")

    def minTagArtistsHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "How many artists must have been tagged with tag X in order for links and playlists to be created for tag X? A tag might only have been given to one artist in your collection, or it might group together many artists in your collection. This option allows you to cut down the number of tags for which links and playlists are created.")

    def lastfmQueriesHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "How many times do you want %s to attempt to download an artist's data from last.fm before giving up?" % __progname__)

    def lastfmUsersHelp(self):
        QMessageBox.information(
            self, "%s - help" % __progname__,
            """Enter the names of last.fm users for whom you want to create links and playlists, separated by commas. Two types of links are created: 'listened' contains locally available music that has been listened to recently by the user in question; 'unlistened' is locally available music that has not been listened to recently by the user in question. The first might be of more interest when the user is not you (explore someone else's music), whereas the opposite is true of the second (explore music you own but have not been listening to).""")

    def musicspaceFileHelp(self):
        QMessageBox.information(
            self,
            "%s - help" % __progname__,
            "A musicspace file allows you to create playlists and links based on your personal notions of music similarity, rather than using similarity data from e.g. last.fm. If you have created a musicspace file, then select it here.\n\nA musicspace file is a .csv spreadsheet file: i.e. it's a plain text file with one row per artist, and with columns separated by commas. The first two columns contain the artist name and the artist MusicBrainz ID. You can leave the MusicBrainz ID empty, and %s will do its best to work out what artist you are referring to. The subsequent columns are where you define the position of artists relative to each other. There can be an arbitrary number of these columns, each corresponding to some axis in a multi-dimensional music space. The axes can be anything you like. One possibility is associating each axis with a musical genre. Or perhaps each axis should be defined by what lies at its opposite ends. However you define your dimensions, each artist must have a numeric entry in each of the columns, indicating that artist's position in music space." % __progname__)

    def musicspaceDropoffHelp(self):
        QMessageBox.information(self,
                                "%s - help" % __progname__,
                                "The drop-off parameter controls musicspace playlist generation (it has no effect on Last.fm playlists). Let's say you're creating a musicspace playlist for artist X. If you set the drop-off parameter to zero, then the tracks in the playlist will come from all artists in musicspace, without regard to their proximity to artist X. And if you set it to a large enough number, then the tracks in the playlist will only come from artists that occupy exactly the same position in musicspace as artist X. So, you want something in between. To start off with, try a value somewhere between 2.5 and 4.0. If you want to know the details, read on.\n\nA track in the playlist for artist X is chosen by picking an artist, and then picking a track at random from that artist's tracks (so there's no bias towards artists with many tracks). Artist Y is chosen to contribute a track to artist X's playlist with probability proportional to (1+Dxy)^(-a), where Dxy is the Euclidean distance between artists X and Y, and a is the dropoff parameter.")




class NewThread(QThread):
    """class code descended from class Walker
    rgpwpyqt/chap19/walker.py. This is a base class for action to be
    carried out in a new execution thread. This class cannot actually
    run anything, as it lacks a run() method; the subclasses implement
    run()."""

    def __init__(self, parent=None):
        super(NewThread, self).__init__(parent)
        self.stopped = False
        self.mutex = QMutex()
        self.path = None
        self.completed = False

    def initialize(self):
        # I think the point here is that the new threads should not be
        # trying to randomly access variables like settings and dbm
        # that 'belong' to the parent thread.
        self.stopped = False
        self.completed = False
        self.settings = settings
        self.dbm = dbm
        # Text output during dbm activity is logged to the listWidget,
        # rather than stdout or whatever as it would be under the CLI
        dbm.log = self.log

    def stop(self):
        try:
            self.mutex.lock()
            self.stopped = True
        except:
            print('Exception in NewThread.stop()')
        finally:
            self.mutex.unlock()

    def finishUp(self):
        self.completed = True
        self.stop()
        self.emit(SIGNAL("finished(bool)"), self.completed)
        # the following is not allowed, apparently
        # self.emit(SIGNAL("finished(QThread)"), self)

    def isStopped(self):
        try:
            self.mutex.lock()
            return self.stopped
        finally:
            self.mutex.unlock()

    def log(self, message):
        try:
            self.emit(SIGNAL('log(QString)'), message)
        except:
            sys.stderr.write(message + '\n' if message else 'Empty message!\n')

    def logi(self, message):
        try:
            self.emit(SIGNAL('logi(QString)'), message)
        except:
            sys.stderr.write(message + '\n' if message else 'Empty message!\n')

class LibraryScanner(NewThread):
    def initialize(self, path, simartists={}):
        NewThread.initialize(self)
        self.path = path
        self.simartists = simartists

    def run(self):
        self.log('Scanning library rooted at %s' % self.path)
        self.dbm.root = dbm.Root(self.path, None)
        self.log('Constructing database of artists in library')
        self.dbm.root.create_artist_name_to_mbid_mapping()
        self.dbm.root.set_dbm_artistids()
        self.dbm.root.create_artists()
        self.dbm.root.simartists = self.simartists
        self.dbm.root.download_lastfm_data()
        self.finishUp()

class LibraryLoader(NewThread):
    def initialize(self, path):
        NewThread.initialize(self)
        self.path = path

    def run(self):
        try:
            self.dbm.root = util.load_pickled_object(self.path)
            if isinstance(self.dbm.root.path, str):
                self.log('Converting from old %s format...' % __progname__)
                self.dbm.root.decode_strings()
            self.settings.savefile = self.path
        except:
            self.log('Failed to load library at %s' % self.path)
            raise
        self.finishUp()

class LibrarySaver(NewThread):
    def initialize(self, path):
        NewThread.initialize(self)
        self.path = path

    def run(self):
        try:
            self.dbm.root.delete_attributes(['diskTreeWidgetItem'])
            util.pickle_object(self.dbm.root, self.path)
            self.settings.savefile = self.path
        except:
            self.log('Failed to save library to %s' % self.path)
            raise
        self.finishUp()

class AlbumArtDownloader(NewThread):
    def run(self):
        self.log('Downloading album art to %s' % self.settings.albumartdir)
        self.dbm.root.download_albumart()
        self.finishUp()

class LibraryGrafter(NewThread):
    def initialize(self, path):
        NewThread.initialize(self)
        self.path = path

    def run(self):
        self.log('Scanning library subtree rooted at %s for addition to library' % self.path)
        self.dbm.root.graft_subtree(dbm.Root(self.path, None))
        self.log('Reconstructing database of artists in library')
        self.dbm.root.artists = {}
        self.dbm.root.artistids = {}
        self.dbm.root.artistnames = {}
        self.dbm.root.create_artist_name_to_mbid_mapping()
        self.dbm.root.set_dbm_artistids()
        self.dbm.root.create_artists()
        self.dbm.root.download_lastfm_data()
        self.finishUp()

class LastfmSimilarArtistSetter(NewThread):
    def run(self):
        self.log('Retrieving similar artist lists from last.fm')
        self.dbm.root.download_lastfm_data()
        self.finishUp()

class PlaylistGenerator(NewThread):
    def initialize(self, dirs):
        NewThread.initialize(self)
        self.dirs = dirs
        dbm.log = self.logi

    def run(self):
        self.log('Generating Last.fm tag playlists...')
        self.dbm.root.write_lastfm_tag_playlists(self.dirs['tags'])

        if self.settings.musicspace_ready:
            self.log('Generating musicspace similar artists playlists...')
            self.dbm.root.write_musicspace_similar_artists_playlists(self.dirs['musicspace_similar'])
        self.log('Generating Last.fm similar artists playlists...')
        self.dbm.root.write_lastfm_similar_artists_playlists(self.dirs['lastfm_similar'])
        self.log('Generating single artist random playlists...')
        self.dbm.root.write_single_artists_playlists(self.dirs['single_artists'])
        self.log('Generating whole-library random playlists...')
        self.dbm.root.write_all_artists_playlist(self.dirs['all_artists'])
        self.finishUp()

class LinksCreator(NewThread):
    def initialize(self, dirs):
        NewThread.initialize(self)
        self.dirs = dirs
        dbm.log = self.logi

    def run(self):
        self.log('Creating last.fm tag links')
        self.dbm.root.write_lastfm_tag_linkfiles(self.dirs['tags'])

        self.log('Creating alphabetical index')
        self.dbm.root.write_a_to_z_linkfiles(self.dirs['AtoZ'])

        self.log('Writing artist biographies')
        self.dbm.root.write_lastfm_artist_biographies(self.dirs['bios'])

        self.log('Creating last.fm user links')
        self.dbm.root.lastfm_users = {}
        for name in settings.lastfm_user_names:
            user = dbm.LastFmUser(name, settings.lastfm)
            self.dbm.root.lastfm_users[name] = user
            if user is None:
                self.log('Failed to find last.fm user %s' % name)
                continue
            self.log(name)
            user.get_artist_counts()

            user_dir = os.path.join(settings.links_path, name)
            util.mkdirp(user_dir)

            self.log('%s listened music' % name)
            d = os.path.join(user_dir, 'Present-Listened')
            util.mkdirp(d)
            user.write_listened_artists_linkfile(d)

            self.log('%s unlistened music' % name)
            d = os.path.join(user_dir, 'Present-Unlistened')
            util.mkdirp(d)
            user.write_unlistened_artists_linkfile(d)

            self.log('%s absent music' % name)
            path = os.path.join(user_dir, "Absent.link")
            user.write_absent_artists_linkfile(path)

        if settings.musicspace_ready:
            self.log('Creating links to musicspace similar artists')
            self.dbm.root.write_musicspace_similar_artists_linkfiles(
                self.dirs['musicspace_similar'])

        self.log('Creating links to lastfm similar artists')
        self.dbm.root.write_lastfm_similar_artists_linkfiles(self.dirs['lastfm_similar'])

        self.finishUp()


def processPath(path):
    """path is either a QDir or a Qstring"""
    try:
        return os.path.abspath(unicode(QDir.toNativeSeparators(path)))
    except:
        print repr(path)
        raise
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setOrganizationName(__progname__)
#    app.setOrganizationDomain('')
    app.setApplicationName(__progname__)
    app.setWindowIcon(QIcon(":/Python_reticulatus.png"))

    if len(sys.argv) > 1 and sys.argv[1] == '-e':
        __log_to_file__ = False

    mainWindow = MainWindow()
    mainWindow.show()
    try:
        app.exec_()
    except Exception, e:
        print 'Caught exception in app.exec()'
        mainWindow.log(e)
