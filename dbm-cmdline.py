from cmdline.cmdline import CommandLineApp

class Dbm(CommandLineApp):

    def __init__(self):
        CommandLineApp.__init__(self)

        op = self.option_parser
        usage = 'usage: [options] %s -i %s -o %s' % (
            __progname__,
            os.path.sep.join(['location','of','music', 'library']),
            os.path.sep.join(['folder','to','receive','output']))
        op.set_usage(usage)

        op.add_option('-i', '--library', dest='libdir', type='string', default=None,
                      help='Location of root of music library')

        op.add_option('-o', '--outdir', dest='outdir', type='string', default='.',
                      help='Folder to receive output, defaults to current folder.')

        # op.add_option('-u', '--update', dest='update', default=False, action='store_true',
        #               help='Don\'t re-scan whole library; instead update saved dbm data base.')

        op.add_option('-f', '--libfile', dest='savefile', type='string', default='library.dbm',
                      help="Saved library file, defaults to 'library.dbm'")

        op.add_option('-r', '--rockbox', dest='path_to_rockbox', type='string', default=None,
                      help='Location of rockbox digital audio player.')

        op.add_option('', '--mintracks', dest='minArtistTracks', default=0, type='int',
                      help='Playlists and linkfiles will only be generated for artists with' + \
                          ' more than this number of tracks in the library.')

        op.add_option('', '--numtries', dest='numtries', default=3, type='int',
                      help='Number of times to attempt web query for an artist before giving up.')

        op.add_option('', '--noweb', dest='query_lastfm', default=True, action='store_false',
                      help="Don't query last.fm similar artists.")

        op.add_option('-n', '', dest='create_files', default=True, action='store_false',
                      help='Don\'t create any playlists or link files')

        op.add_option('', '--version', dest='show_version', default=False, action='store_true',
                      help='Print out version information and exit')

        op.add_option('', '--show-library', dest='show_tree', default=False, action='store_true',
                      help='Print sparse representation of library, and exit')

        op.add_option('', '--show-tracks', dest='show_tracks', default=False, action='store_true',
                      help='Include track information when using --show')

        op.add_option('', '--show-artists', dest='show_artists', default=False, action='store_true',
                      help='Print information on artists in library, and exit')

        op.add_option('-s', '--musicspace', dest='music_space_file', type='string', default=None,
                      help='Music space file')

        op.add_option('', '--show-musicspace', dest='show_musicspace', default=False, action='store_true',
                      help="Print summary of neighbouring artists in musicspace, and exit")

        op.add_option('', '--dropoff', dest='musicspace_dropoff_param', type='float', default=3.0,
                      help="Parameter controlling rate at which probability of inclusion falls away with distance in music space. When generating playlists for artist X, a value of 0 means that all other artists will be included with equal probability; a value of more than 5 or so means that you'll rarely get anybody but X. Default is 3.0")
        op.add_option('', '--create-musicspace-skeleton', dest='write_music_space', default=False,
                      action='store_true',
                      help='create skeleton music space spreadsheet file and exit')

        op.add_option('-t', '--target', dest='target', default='rockbox', type='string',
                      help="Specify target platform: defaults to rockbox; " +\
                          "in the future you will be able to use --target=native " +\
                          "to create playlists and links for use on the local machine.")

        # self.log.setLevel(logging.DEBUG)

    def check_settings(self):
        if not settings.savefile and not settings.libdir:
            raise DbmError('Either -f LIBFILE, or -i LIBDIR, or both, must be given' % settings.libdir)

        if settings.libdir:
            if not (os.path.isdir(settings.libdir) or os.path.islink(settings.libdir)):
                raise DbmError('library folder %s is not a valid folder' % settings.libdir)

        if settings.savefile:
            if not (os.path.isfile(settings.savefile) or os.path.islink(settings.savefile)):
                raise DbmError('Saved library file %s is not valid' % settings.savefile)

    def main(self):
        global settings
        global root

        settings = Settings(dbm.options)
        decode_strings(settings)

        # dbm_dir = os.path.join(settings.outdir, '%s_files' % __progname__)
        for d in [settings.outdir]:
            if not os.path.exists(d): os.mkdir(d)
        # settings.savefile = os.path.join(dbm_dir, 'library.dbm')
        settings.logfile = codecs.open('dbmlog.txt', 'w', 'utf-8')
        settings.musicspace_ready = False
        settings.musicspace_dimension = None
        settings.albumartdir = '/tmp/albumart'

        if settings.show_version:
            log('dbm version %s' % __version__)
            self.exit(2)

        elog('dbm version %s' % __version__)
        elog(time.ctime())

        if settings.libdir:
            # settings.libdir = os.path.splitdrive(settings.libdir)[1]
            settings.libdir = os.path.abspath(settings.libdir) # also strips any trailing '/'

        if settings.path_to_rockbox:
            settings.path_to_rockbox = os.path.abspath(settings.path_to_rockbox) # also strips any trailing '/'

        self.check_settings()
        settings.show()

        if not settings.libdir:
            print 'loading saved library'
            log('Loading saved library file %s' % settings.savefile)
            try:
                root = load_pickled_object(settings.savefile)
                # Pickles made by previous versions may have stored
                # paths as strings a.o.t. unicode
                if isinstance(root.path, str):
                    root.decode_strings()
            except:
                raise DbmError('Could not load saved dbm library file %s' % settings.savefile)
            log('Loaded library with %d artists' % len(root.artists))
            if settings.libdir:
                log('Updating library subtree rooted at %s' % settings.libdir)
                new_subtree = Root(settings.libdir, None)
                root.graft_subtree(new_subtree)
            root.artists = {}
            root.artistids = {}
            root.artistnames = {}
        else:
            log('Scanning library rooted at %s' % settings.libdir)
            root = Root(settings.libdir, None)

        if settings.create_files and settings.libdir:
            # was and (settings.libdir or not settings.update):
            log('Saving library to %s' % settings.savefile)
            pickle_object(root, settings.savefile)

        settings.libdir = None # Not used subsequently! Use root.path instead.

        log('Constructing database of artists in library')
        root.create_artist_name_to_mbid_mapping()
        root.set_dbm_artistids()
        root.create_artists()

        if settings.show_tree or settings.show_tracks:
            root.show()
            self.exit(0)

        if settings.show_artists:
            root.show_artists()
            self.exit(0)

        if settings.write_music_space:
            with codecs.open('__musicspace.csv', 'w', 'utf-8') as f:
                root.write_musicspace_file(f)

        if settings.music_space_file:
            log('Populating musicspace')
#            with codecs.open(settings.music_space_file, 'r', 'utf-8') as f:
            with open(settings.music_space_file, 'r') as f:
                root.populate_musicspace(f, settings.musicspace_dropoff_param)
            settings.musicspace_ready = True

        if settings.show_musicspace:
            root.show_musicspace()
            self.exit(0)

        if settings.query_lastfm:
            log('Retrieving similar artist lists from last.fm')
        root.download_lastfm_data() # Call this even if not making web queries

        if settings.create_files:
            log('Saving library to %s' % settings.savefile)
            pickle_object(root, settings.savefile)

            log('Creating playlists and rockbox database')

            links_dir = os.path.join(settings.outdir, 'Links')
            lastfm_similar_links_dir = os.path.join(links_dir, 'Last.fm_Similar')
            musicspace_similar_links_dir = os.path.join(links_dir, 'Musicspace_Similar')
            az_links_dir = os.path.join(links_dir, 'A-Z')

            playlists_dir = os.path.join(settings.outdir, 'Playlists')
            single_artists_playlists_dir = os.path.join(playlists_dir, 'Single_Artists')
            all_artists_playlists_dir = os.path.join(playlists_dir, 'All_Artists')
            lastfm_similar_playlists_dir = os.path.join(playlists_dir, 'Last.fm_Similar')
            musicspace_similar_playlists_dir = os.path.join(playlists_dir, 'Musicspace_Similar')

            rec_dir = os.path.join(settings.outdir, 'Recommended')

            for d in [links_dir, rec_dir, playlists_dir,
                      az_links_dir, lastfm_similar_links_dir, musicspace_similar_links_dir,
                      single_artists_playlists_dir, all_artists_playlists_dir,
                      lastfm_similar_playlists_dir, musicspace_similar_playlists_dir]:
                if not os.path.exists(d):
                    os.mkdir(d)

            root.write_lastfm_similar_and_present_linkfiles(lastfm_similar_links_dir)
            if settings.musicspace_ready:
                root.write_musicspace_similar_artists_linkfiles(musicspace_similar_links_dir)
            root.write_similar_but_absent_linkfiles(rec_dir)
            root.write_a_to_z_linkfiles(az_links_dir)

            if settings.musicspace_ready:
                root.write_musicspace_similar_artists_playlists(musicspace_similar_playlists_dir)
            root.write_lastfm_similar_and_present_playlists(lastfm_similar_playlists_dir)
            root.write_single_artists_playlists(single_artists_playlists_dir)
            root.write_all_artists_playlist(all_artists_playlists_dir)

            log('Done')
            self.exit(0)

    def usage(self):
        print('dbm version %s' % __version__)
        print('Use -i and -o options to specify location of music library and output folder. E.g.\n')

        if os.name == 'posix':
            print('./dbm.py -i /media/ipod/music -o ~/music/ipod-dbm-output')
        else:
            print('python dbm.py -i E:\Music -o dbm-output')

        print('If you want to re-use saved database files in an existing output')
        print('directory rather than scanning your music library again, use -u.')
        print('To see information on available options, use -h.')
        self.exit(2)

    def exit(self, code):
        settings.logfile.close()
        sys.exit(code)

if __name__ == '__main__':
    def log(msg, dummy_arg=None):
        try:
            sys.stdout.write(msg.encode('utf-8') + '\n')
        except:
            sys.stdout.write('ERROR: Failed to encode log message\n')
    dbm = Dbm()
    dbm.run()
