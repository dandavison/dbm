# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './settings_dlg.ui'
#
# Created: Tue Nov  3 17:52:20 2009
#      by: PyQt4 UI code generator 4.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(516, 576)
        Dialog.setMaximumSize(QtCore.QSize(600, 16777215))
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.targetComboBox = QtGui.QComboBox(Dialog)
        self.targetComboBox.setObjectName("targetComboBox")
        self.gridLayout.addWidget(self.targetComboBox, 0, 2, 1, 1)
        self.targetDevHelpButton = QtGui.QPushButton(Dialog)
        self.targetDevHelpButton.setObjectName("targetDevHelpButton")
        self.gridLayout.addWidget(self.targetDevHelpButton, 0, 3, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 1, 1, 1, 1)
        self.rockboxPathChangeButton = QtGui.QPushButton(Dialog)
        self.rockboxPathChangeButton.setObjectName("rockboxPathChangeButton")
        self.gridLayout.addWidget(self.rockboxPathChangeButton, 1, 2, 1, 1)
        self.rockboxPathHelpButton = QtGui.QPushButton(Dialog)
        self.rockboxPathHelpButton.setObjectName("rockboxPathHelpButton")
        self.gridLayout.addWidget(self.rockboxPathHelpButton, 1, 3, 1, 1)
        self.label_6 = QtGui.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.label_7 = QtGui.QLabel(Dialog)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 2, 1, 1, 1)
        self.outputFolderChangeButton = QtGui.QPushButton(Dialog)
        self.outputFolderChangeButton.setObjectName("outputFolderChangeButton")
        self.gridLayout.addWidget(self.outputFolderChangeButton, 2, 2, 1, 1)
        self.outputFolderHelpButton = QtGui.QPushButton(Dialog)
        self.outputFolderHelpButton.setObjectName("outputFolderHelpButton")
        self.gridLayout.addWidget(self.outputFolderHelpButton, 2, 3, 1, 1)
        self.label_8 = QtGui.QLabel(Dialog)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 3, 1, 1, 1)
        self.label_11 = QtGui.QLabel(Dialog)
        self.label_11.setObjectName("label_11")
        self.gridLayout.addWidget(self.label_11, 4, 0, 1, 1)
        self.musicspaceFileChangeButton = QtGui.QPushButton(Dialog)
        self.musicspaceFileChangeButton.setObjectName("musicspaceFileChangeButton")
        self.gridLayout.addWidget(self.musicspaceFileChangeButton, 4, 2, 1, 1)
        self.musicspaceFileHelpButton = QtGui.QPushButton(Dialog)
        self.musicspaceFileHelpButton.setObjectName("musicspaceFileHelpButton")
        self.gridLayout.addWidget(self.musicspaceFileHelpButton, 4, 3, 1, 1)
        self.line = QtGui.QFrame(Dialog)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 5, 0, 1, 1)
        self.minArtistTracksComboBox = QtGui.QComboBox(Dialog)
        self.minArtistTracksComboBox.setObjectName("minArtistTracksComboBox")
        self.gridLayout.addWidget(self.minArtistTracksComboBox, 6, 2, 1, 1)
        self.minArtistTracksHelpButton = QtGui.QPushButton(Dialog)
        self.minArtistTracksHelpButton.setObjectName("minArtistTracksHelpButton")
        self.gridLayout.addWidget(self.minArtistTracksHelpButton, 6, 3, 1, 1)
        self.label_13 = QtGui.QLabel(Dialog)
        self.label_13.setObjectName("label_13")
        self.gridLayout.addWidget(self.label_13, 6, 0, 1, 1)
        self.label_14 = QtGui.QLabel(Dialog)
        self.label_14.setObjectName("label_14")
        self.gridLayout.addWidget(self.label_14, 7, 0, 1, 1)
        self.minTagArtistsComboBox = QtGui.QComboBox(Dialog)
        self.minTagArtistsComboBox.setObjectName("minTagArtistsComboBox")
        self.gridLayout.addWidget(self.minTagArtistsComboBox, 7, 2, 1, 1)
        self.minTagArtistsHelpButton = QtGui.QPushButton(Dialog)
        self.minTagArtistsHelpButton.setObjectName("minTagArtistsHelpButton")
        self.gridLayout.addWidget(self.minTagArtistsHelpButton, 7, 3, 1, 1)
        self.label_12 = QtGui.QLabel(Dialog)
        self.label_12.setObjectName("label_12")
        self.gridLayout.addWidget(self.label_12, 8, 0, 1, 1)
        self.lastfmUsersLineEdit = QtGui.QLineEdit(Dialog)
        self.lastfmUsersLineEdit.setObjectName("lastfmUsersLineEdit")
        self.gridLayout.addWidget(self.lastfmUsersLineEdit, 8, 1, 1, 2)
        self.lastfmUsersHelpButton = QtGui.QPushButton(Dialog)
        self.lastfmUsersHelpButton.setObjectName("lastfmUsersHelpButton")
        self.gridLayout.addWidget(self.lastfmUsersHelpButton, 8, 3, 1, 1)
        self.label_10 = QtGui.QLabel(Dialog)
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 9, 0, 1, 1)
        self.lastfmQueriesComboBox = QtGui.QComboBox(Dialog)
        self.lastfmQueriesComboBox.setObjectName("lastfmQueriesComboBox")
        self.gridLayout.addWidget(self.lastfmQueriesComboBox, 9, 2, 1, 1)
        self.lastfmQueriesHelpButton = QtGui.QPushButton(Dialog)
        self.lastfmQueriesHelpButton.setObjectName("lastfmQueriesHelpButton")
        self.gridLayout.addWidget(self.lastfmQueriesHelpButton, 9, 3, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 10, 0, 1, 1)
        self.musicspaceDropoffSpinBox = QtGui.QDoubleSpinBox(Dialog)
        self.musicspaceDropoffSpinBox.setDecimals(1)
        self.musicspaceDropoffSpinBox.setSingleStep(0.1)
        self.musicspaceDropoffSpinBox.setObjectName("musicspaceDropoffSpinBox")
        self.gridLayout.addWidget(self.musicspaceDropoffSpinBox, 10, 2, 1, 1)
        self.musicspaceDropoffHelpButton = QtGui.QPushButton(Dialog)
        self.musicspaceDropoffHelpButton.setObjectName("musicspaceDropoffHelpButton")
        self.gridLayout.addWidget(self.musicspaceDropoffHelpButton, 10, 3, 1, 1)
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 11, 0, 1, 1)
        self.numSimArtBiogsComboBox = QtGui.QComboBox(Dialog)
        self.numSimArtBiogsComboBox.setObjectName("numSimArtBiogsComboBox")
        self.gridLayout.addWidget(self.numSimArtBiogsComboBox, 11, 2, 1, 1)
        self.numSimArtBiogsHelpButton = QtGui.QPushButton(Dialog)
        self.numSimArtBiogsHelpButton.setObjectName("numSimArtBiogsHelpButton")
        self.gridLayout.addWidget(self.numSimArtBiogsHelpButton, 11, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(17, 144, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 12, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 13, 2, 1, 2)
        self.label.setBuddy(self.targetComboBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Target device", None, QtGui.QApplication.UnicodeUTF8))
        self.targetDevHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Location of rockbox device", None, QtGui.QApplication.UnicodeUTF8))
        self.rockboxPathChangeButton.setText(QtGui.QApplication.translate("Dialog", "None", None, QtGui.QApplication.UnicodeUTF8))
        self.rockboxPathHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Dialog", "Output folder", None, QtGui.QApplication.UnicodeUTF8))
        self.outputFolderChangeButton.setText(QtGui.QApplication.translate("Dialog", "None", None, QtGui.QApplication.UnicodeUTF8))
        self.outputFolderHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("Dialog", "Musicspace file", None, QtGui.QApplication.UnicodeUTF8))
        self.musicspaceFileChangeButton.setText(QtGui.QApplication.translate("Dialog", "None", None, QtGui.QApplication.UnicodeUTF8))
        self.musicspaceFileHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.minArtistTracksHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_13.setText(QtGui.QApplication.translate("Dialog", "Minimum tracks per artist", None, QtGui.QApplication.UnicodeUTF8))
        self.label_14.setText(QtGui.QApplication.translate("Dialog", "Minimum artists per tag", None, QtGui.QApplication.UnicodeUTF8))
        self.minTagArtistsHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("Dialog", "Last.fm users", None, QtGui.QApplication.UnicodeUTF8))
        self.lastfmUsersHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("Dialog", "Last.fm queries before giving up", None, QtGui.QApplication.UnicodeUTF8))
        self.lastfmQueriesHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Musicspace probability drop-off parameter", None, QtGui.QApplication.UnicodeUTF8))
        self.musicspaceDropoffHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Similar artist biographies per artist", None, QtGui.QApplication.UnicodeUTF8))
        self.numSimArtBiogsHelpButton.setText(QtGui.QApplication.translate("Dialog", "?", None, QtGui.QApplication.UnicodeUTF8))

