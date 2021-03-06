#!/usr/bin/env python

#    dbm : A music library tool

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

from __future__ import with_statement
import sys, os, re, time, urllib, codecs, shutil
import random, csv, math
import optparse, logging
import pylast.pylast as pylast
import track
from dedpy.ded import *
__version__ = '0.9.50'
__progname__ = 'dbm'
__root_path__ = None

class Node(object):
    """A tree representation of a music library."""
    def __init__(self, path, parent):
        self.path = path
        self.parent = parent
        self.subtrees = set([])
        self.tracks = []
        self.dbm_artistids = {}
        try:
            self.grow()
        except Exception, e:
            error('Failed to scan library: %s' % e)
        self.mtime = None

    def grow(self):
        # contents = [x.decode('utf-8') for x in os.listdir(self.path)]

        # print 'self.path %s unicode' % isinstance(self.path, unicode)
        # x = filter(lambda(xi): not isinstance(xi, unicode), os.listdir(self.path))
        # print 'not unicode:'
        # print x

        paths = os.listdir(self.path)
        # Bjork and Sigur Ros are not unicode despite self.path being unicode: ???
        paths = filter(lambda(x): isinstance(x, unicode), paths)

        paths = [os.path.join(self.path, x) for x in paths]

        if not os.path.exists(os.path.join(self.path, '.ignore')):
            if not settings.quiet:
                logi("\t\t%s" % library_relative_path(self.path))
            musicpaths = filter(track.is_music, paths)
            self.tracks = filter(lambda(t): t.valid, [track.Track(p) for p in musicpaths])
        for d in filter(os.path.isdir, paths):
            self.subtrees.add(Node(d, self))

    def is_pure_subtree(self):
        return len(self.dbm_artistids) == 1

    def show(self):
        print('%s %d %s' % (self.path.ljust(75), len(self.dbm_artistids), self.dbm_artistids))
        if settings.show_tracks:
            for t in self.tracks:
                t.show()
        for subtree in self.subtrees:
            subtree.show()

    def create_artist_name_to_mbid_mapping(self):
        """artistids is a dict of artistids keyed by artistnames, that
        is maintained at the root of the tree in an attempt to
        synonymise artists when some of their music lacks musicbrainz
        artistid tags."""
        for t in self.tracks:
            for aid, aname in [(t.artistid,     t.artistname),
                               (t.albumartistid, t.albumartistname)]:
                if aid and aname:
                    dbm_aname = canonicalise_artist_name(aname)
                    if not root.artistids.has_key(dbm_aname):
                        root.artistids[dbm_aname] = aid
                    elif root.artistids[dbm_aname] != aid:
                        warn('artistname "%s" associated with multiple artist IDs: "%s" "%s"\n' %
                            (aname, aid, root.artistids[dbm_aname]))

        for subtree in self.subtrees:
            subtree.create_artist_name_to_mbid_mapping()

    def set_dbm_artistids(self):
        """Each node has a dict node.dbm_artistids containing the counts of
        tracks by each artist in that subtree. This function traverses the
        tree to set those dicts. The dicts are keyed by dbm_artistids,
        which are MBIDs where available and otherwise artist names. This
        function also sets the dbm_artistid of the music."""

        # The design of this function is key to the behaviour of dbm

        # Set dbm_artistid and dbm_albumartistid of tracks
        for t in self.tracks:
            for aid, aname, attr in [(t.artistid, t.artistname, 'dbm_artistid'),
                                     (t.albumartistid, t.albumartistname, 'dbm_albumartistid')]:
                dbm_aid = root.make_dbm_artistid(aid, aname)
                # If MBID and name tags are lacking, this track does
                # not contribute an artist
                if dbm_aid:
                    setattr(t, attr, dbm_aid)
                    if not root.artistnames.has_key(dbm_aid):
                        root.artistnames[dbm_aid] = []
                    if aname:
                        root.artistnames[dbm_aid].append(aname)

        # Determine if we are in a pure directory
        # FIXME this is strange
        dbm_aids = unique(filter(None, [t.dbm_artistid for t in self.tracks]))
        if len(dbm_aids) == 1: self.dbm_artistids = {dbm_aids[0]:1}

        for subtree in self.subtrees:
            subtree.set_dbm_artistids()
            self.dbm_artistids = table_union(self.dbm_artistids, subtree.dbm_artistids)

    def set_track_artists(self):
        for t in self.tracks:
            # All tracks are 'valid', i.e. have artist MBID or artist
            # name, hence must have dbm_artistid
            t.artist = root.artists[t.dbm_artistid]
            if t.dbm_albumartistid:
                t.albumartist = root.artists[t.dbm_albumartistid]
        for subtree in self.subtrees:
            subtree.set_track_artists()

    def download_albumart(self):
        def isok(track):
            if not track.artistname or not track.releasename:
                return False
            aaid = track.dbm_albumartistid
            if aaid:
                if aaid != track.dbm_artistid:
                    return False
                if aaid == settings.various_artists_mbid:
                    return False
            return True

        tracks = filter(isok, self.tracks)
        art_rel = set([(t.artistname, t.releasename) for t in tracks])
        # FIXME: should check if any of those tuples have different
        # artist but same releasename.

        for ar in art_rel:
            if not ar[1] or any([c in ar[1] for c in settings.fs_bad_chars]):
                albumart_releasename = 'cover'
            else:
                albumart_releasename = ar[1]
            target = os.path.join(self.path, albumart_releasename + '.jpg')
            if(os.path.exists(target)):
                continue

            url = None
            gotit = False
            album = settings.network.get_album(*ar)
            try:
                url = album.get_cover_image() # it's unicode
            except Exception, e:
                error('Error obtaining album art URL for %s: %s' % (unicode(ar), e))
            if url:
                try:
                    urllib.urlretrieve(url, target)
                    gotit = True
                    if ar[1] == albumart_releasename:
                        logi("%s: %s" % ar)
                    else:
                        logi("%s: %s (Invalid filename: renamed as 'cover.jpg')" % ar)
                except Exception, e:
                    logi("%s: %s      Failed: %s" % (ar[0], ar[1], e))

        for subtree in self.subtrees:
            subtree.download_albumart()

    def set_artist_subtrees_and_tracks(self):
        if self.is_pure_subtree():
            if not self.parent or not self.parent.is_pure_subtree(): # At root of a maximal pure subtree
                dbm_aid = self.dbm_artistids.keys()[0]
                artist = root.artists[dbm_aid]
                artist.subtrees.add(ArtistNode(self, artist, artist, None))
        for t in self.tracks:
            if not self.dbm_artistids: # FIXME: this means non-pure folder, but is not clear
                if self not in [anode.node for anode in t.artist.subtrees]:
                    t.artist.subtrees.add(ArtistNode(self, t.artist, t.albumartist, t.releasename))
            t.artist.tracks.append(t)
            if t.albumartist:
                t.albumartist.tracks_as_albumartist.append(t)
        for subtree in self.subtrees:
            subtree.set_artist_subtrees_and_tracks()

    def gather_subtree_tracks(self, node):
        """Add all tracks in subtree to self.tracks"""
        node.subtree_tracks.extend(self.tracks)
        for subtree in self.subtrees:
            subtree.gather_subtree_tracks(node)

    def decode_strings(self):
        self.path = self.path.decode('utf-8')
        for t in self.tracks:
            decode_strings(t)
        for s in self.subtrees:
            s.decode_strings()

    def delete_attributes(self, attr_names):
        for attr_name in attr_names:
            if (hasattr(self, attr_name)):
                setattr(self, attr_name, None)
        for subtree in self.subtrees:
            subtree.delete_attributes(attr_names)

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    def gather_terminal_nodes(self):
        if len(self.subtrees) == 0:
            root.terminal_nodes.append(self)
        else:
            for subtree in self.subtrees:
                subtree.gather_terminal_nodes()

class Root(Node):
    """The root node has and does certain things that the internal
    nodes don't."""
    def __init__(self, path, parent):
        global __root_path__
        __root_path__ = path
        track.error = error
        Node.__init__(self, path, parent)
        __root_path__ = None
        # artistids is a dict of artist MBIDs, keyed by dbm_artistid
        self.artistids = {}
        # artistnames is a dict of artist names, keyed by dbm_artistid
        self.artistnames = {}
        # artists is a dict of Artist instances, keyed by dbm_artistid
        self.artists = {}
        self.all_artists = {}
        self.subtree_tracks = []
        self.similar_artists = {}
        self.tags_by_artist = {}
        self.tags = {}
        self.biographies = {}
        self.lastfm_users = {}
        self.terminal_nodes = []
        
    def prepare_library(self):
        self.create_artist_name_to_mbid_mapping()
        self.set_dbm_artistids()
        self.create_artists()

    def create_artists(self):
        dbm_artistids = self.artistnames.keys()
        self.artists = dict(zip(dbm_artistids,
                                map(Artist, dbm_artistids)))
        self.all_artists = self.artists.copy()
        self.set_track_artists()
        self.set_artist_subtrees_and_tracks()
        self.sanitise_artists()

    def sanitise_artists(self):
        bad = []

        for dbm_aid in self.artists:
            a = self.artists[dbm_aid]
            if not a.id:
                warn('Artist %s has no id: deleting\n' % \
                         a.name if a.name else '?')
                bad.append(dbm_aid)
                continue
            if not a.name:
                warn('Artist %s has no name: deleting\n' % a.id)
                bad.append(dbm_aid)
                continue
            if not a.tracks and not a.tracks_as_albumartist:
                msg = "Artist %s has no tracks (shouldn't happen!): deleting\n" % a.name
                error(msg)
                bad.append(dbm_aid)
                continue
            a.unite_spuriously_separated_subtrees()

        for dbm_aid in bad:
            # Deleting artist but not subtree here may be a bug
            self.artists.pop(dbm_aid)

    def download_artist_lastfm_data_maybe(self):
        """For each artist, the following data is stored in the .dbm library file:
        1. Similar artists data
        2. Tag data
        3. Biography contents
        Unless all three are available for an artist, the full artist data
        is (re-)downloaded from last.fm
        """
        artists = [a for a in self.artists.values() if a.subtrees]
        attrs = ['biographies', 'similar_artists', 'tags_by_artist']
        persistent_dicts_exist = all([hasattr(self, attr) for attr in attrs])
        if persistent_dicts_exist:
            persistent_dicts = [getattr(self, attr) for attr in attrs]
        n = len(artists)
        i = 1
        for artist in sorted(artists):
            persistent_dicts_contain_artist = [d.has_key(artist.id) for d in persistent_dicts]
            if persistent_dicts_exist and all(persistent_dicts_contain_artist):
                for attr, pdict in zip(attrs, persistent_dicts):
                    setattr(artist, attr, pdict[artist.id])
            else:
                try:
                    artist.download_lastfm_data(msg_prefix="\t\t[%d / %d]\t" % (i, n))
                except Exception, e:
                    error('Failed to download last.fm data for %s: %s' % (artist.name, e))
            i += 1
        self.tabulate_tags()

    def tabulate_tags(self):
        self.tags = {}
        ## FIXME: hack
        artists = [a for a in self.artists.values() if self.tags_by_artist.has_key(a.id)]
        for artist in artists:
            tags = self.tags_by_artist[artist.id][0:4]
            for tagname in [t.name for t in tags]:
                if not self.tags.has_key(tagname.lower()):
                    self.tags[tagname.lower()] = Tag(tagname)
                self.tags[tagname.lower()].artists.append(artist)

    def make_dbm_artistid(self, mbid, name):
        """Construct the dbm artist id for this (mbid, name) pair. If
        the mbid is present, then it is used as the dbm id. Otherwise,
        a look-up is performed to see if an mbid has been encountered
        associated with the name, elsewhere in the library. If not,
        then the name is used as the dbm id."""
        if mbid: return mbid
        dbm_name = canonicalise_artist_name(name)
        if self.artistids.has_key(dbm_name):
            return self.artistids[dbm_name]
        return dbm_name

    def lookup_dbm_artistid(self, (mbid, name)):
        """Return the dbm artist id, if any, that is currently in use
        for this (mbid, name) pair."""
        if mbid and self.artists.has_key(mbid): # ! added mbid 090512
            return mbid
        dbm_name = canonicalise_artist_name(name)
        if self.artists.has_key(dbm_name):
            return dbm_name
        return None

    def lookup_dbm_artist(self, (mbid, name)):
        """Return the dbm Artist object, if any, that is currently in
        use for this (mbid, name) pair. I think this should be altered
        to use tuple indexing somehow, but it's not totally trivial."""
        if mbid and self.artists.has_key(mbid): # ! added mbid 090512
            return self.artists[mbid]
        dbm_name = canonicalise_artist_name(name)
        if self.artists.has_key(dbm_name):
            return self.artists[dbm_name]
        return None

    def create_lastfm_user(self, name):
        log('')
        try:
            user = LastFmUser(name)
            user.get_artist_counts()
        except:
            error('Failed to find last.fm user %s' % name, level=2)
            return False
        user.get_artist_counts()
        self.lastfm_users[name] = user
        return True

    def write_lastfm_similar_and_present_playlists(self, direc):
        ok = lambda(a): len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, sorted(self.artists.values()))
        nok = len(artists)
        i = 0
        for artist in artists:
            i += 1
            path = os.path.join(direc, artist.clean_name() + '.m3u')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == nok:
                log('Last.fm similar artists playlists: \t[%d / %d]' % (i, nok))
            tracks = generate_playlist(artist.lastfm_similar_and_present_artists())
            try:
                write_playlist(tracks, path)
            except:
                error('Failed to create last.fm similar playlist for artist %s' % artist.name)

    def write_musicspace_similar_artists_playlists(self, direc):
        def ok(a):
            return hasattr(a, 'artists_weights') and \
                len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, sorted(self.artists.values()))
        nok = len(artists)
        i = 0
        for artist in artists:
            i += 1
            path = os.path.join(direc, artist.clean_name() + '.m3u')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == nok:
                log('\tMusicspace similar artists playlists \t[%d / %d]' % (i, nok))
            tracks = artist.musicspace_similar_artists_playlist()
            if tracks:
                write_playlist(tracks, path)

    def write_single_artists_playlists(self, direc):
        ok = lambda(a): len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, sorted(self.artists.values()))
        nok = len(artists)
        i = 0
        for artist in artists:
            i += 1
            path = os.path.join(direc, artist.clean_name() + '.m3u')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == nok:
                log('\tSingle artist playlists: \t[%d / %d]' % (i, nok))
            try:
                write_playlist(generate_playlist([artist]), path)
            except Exception, e:
                error('Failed to write single artist playlist for %s: %s' % (artist.name, e))

    def write_all_artists_playlist(self, direc, chunk_size=1000):
        self.gather_subtree_tracks(self)
        random.shuffle(self.subtree_tracks)
        num_tracks = len(self.subtree_tracks)
        chunk_end = 0
        plist = 0
        while chunk_end < num_tracks:
            plist += 1
            log('All artists playlists: \t%d' % plist)
            chunk_start = chunk_end
            chunk_end = min(chunk_start + chunk_size, num_tracks)
            path = os.path.join(direc, ('0' if plist < 10 else '') + str(plist) + '.m3u')
            if os.path.exists(path): continue
            tracks = self.subtree_tracks[chunk_start:chunk_end]
            try:
                write_playlist(tracks, path)
            except Exception, e:
                error('Failed to write all artists playlist (chunk %d): %s' % (plist, e))

    def write_lastfm_similar_and_present_linkfiles(self, direc):
        ok = lambda(a): len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, sorted(self.artists.values()))
        nok = len(artists)
        i = 0
        for artist in artists:
            i += 1
            path = os.path.join(direc, artist.clean_name() + '.link')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == nok:
                log('\tLast.fm similar artists link files: \t[%d / %d]' % (i, nok))
            try:
                write_linkfile(artist.lastfm_similar_and_present_artists(), path)
            except Exception, e:
                error('Failed to create last.fm similar link file for artist %s: %s' % (
                        artist.name, e))

    def write_lastfm_tag_linkfiles(self, direc):
        ok = lambda(tag): len(tag.artists) >= settings.minTagArtists
        tags = filter(ok, self.tags.values())
        n = len(tags)
        i = 0
        for tag in tags:
            i += 1
            path = os.path.join(direc, tag.name + '.link')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == n:
                log('\tLast.fm tag link files: \t[%d / %d]' % (i, n))
            try:
                write_linkfile(tag.artists, path)
            except Exception, e:
                error('Failed to create link file for tag %s: %s' % (tag.name, e))

    def write_lastfm_tag_playlists(self, direc):
        ok = lambda(tag): len(tag.artists) >= settings.minTagArtists
        tags = filter(ok, self.tags.values())
        n = len(tags)
        i = 0
        for tag in tags:
            i += 1
            path = os.path.join(direc, tag.name + '.m3u')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == n:
                log('\tLast.fm tag playlists: \t[%d / %d]' % (i, n))
            try:
                write_playlist(generate_playlist(tag.artists), path)
            except:
                error('Failed to create tag playlist for tag %s' % tag.name)

    def update_biographies_on_disk(self):
        artists = [a for a in self.all_artists.values()]
        n = len(artists)
        i = success = 0
        log('')

        for artist in artists:
            try:
                if artist.biography.update(msg_prefix='\t\t[%d / %d]\t' % (i, n)):
                    success += 1
                i += 1
            except Exception, e:
                error('Error updating biography for %s: %s' % (artist.name, e))
        log('%d/%d successful artist biography updates' % (success, n))

    def write_present_artist_biographies(self, filepath):
        artists = [a for a in self.artists.values() if a.is_present()]
        try:
            write_biographies_linkfile(artists, filepath, dict(In_library='Yes'))
        except Exception, e:
            error('Failed to write present artists biographies linkfile: %s' % e)
            
    def write_similar_but_absent_biographies(self, direc):
        ok = lambda(a): len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, self.artists.values())
        n = len(artists)
        i = 0
        for a in artists:
            i += 1
            path = os.path.join(direc, a.clean_name() + '.link')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == 1 or i == n:
                logi('\tSimilar but absent biography links : \t%d / %d' % (i, n))
            try:
                write_biographies_linkfile(
                    a.lastfm_similar_but_absent_artists(settings.num_simartist_biographies),
                    path,
                    metadata=dict(Similar_to=a.name, Present='No'))
            except Exception, e:
                error('Failed to write similar but absent biographies linkfile for ' + \
                          '%s: %s' % (a.name, e))
    def write_musicspace_similar_artists_linkfiles(self, direc):
        def ok(a):
            return hasattr(a, 'artists_weights') and \
                len(a.tracks) >= settings.minArtistTracks
        artists = filter(ok, sorted(self.artists.values()))
        nok = len(artists)
        i = 0
        for artist in artists:
            i += 1
            path = os.path.join(direc, artist.clean_name() + '.link')
            if os.path.exists(path): continue
            if i % 10 == 0 or i == nok:
                log('Musicspace similar artists link files: \t%d / %d' % (i, nok))
            try:
                write_linkfile(artist.musicspace_similar_artists(), path)
            except Exception, e:
                error('Failed to write musicspace similar linkfile for %s: %s' % (artist.name, e))

    def write_a_to_z_linkfiles(self, direc):
        """Create alphabetical directory of music folders. For each
        character (?) create a rockbox link file containing links to music
        folders of all artists whose name starts with that character."""
        index = unique([a.name[0].upper() for a in self.artists.values()])
        index.sort()
        for i in range(len(index)):
            c = index[i]
            path = os.path.join(direc, c + '.link')
            if os.path.exists(path): continue
            log('Artist index link files: \t%s' % ' '.join(index[0:i]))
            artists = [a for a in self.artists.values() if a.name[0].upper() == c]
            try:
                write_linkfile(sorted(artists), path)
            except Exception, e:
                error('Failed to create linkfile for index letter %s: %s' % (c, e))

    def present_artists(self):
        """Return a filtered version of self.artists, containing only
        the artists present in the library"""
        return dict([(k, v) for k, v in self.artists.iteritems() if v.is_present()])

    def show_artists(self):
        for a in self.artists.values():
            print('%s\t%s' % (
                    a.name,
                    a.id if settings.mbid_regexp.match(a.id) else ''))

    def show_musicspace(self):
        for a in sorted(self.artists.values()):
            print(a.name)
            if hasattr(a, 'artists_weights'):
                a.show_musicspace_neighbours()

    def populate_musicspace(self, fileobj, a=3.0):
        location = {}
        dimensions = set([])
        # dialect = csv.Sniffer().sniff(path)
        # csv.delimiter = '\t'
        reader = csv.reader(fileobj)
        for row in reader:
            row = [cell.decode('utf-8') for cell in row]
            dbm_aid = self.make_dbm_artistid(row[1], row[0])
            if self.artists.has_key(dbm_aid):
                loc = map(float, row[2:])
                if all(loc):
                    self.artists[dbm_aid].musicspace_location = loc
                    location[dbm_aid] = loc
                    dimensions.add(len(loc))

        settings.musicspace_dimension = max(dimensions) if dimensions else 0

        for this_id in location.keys():
            # TMP while having pickling problems
            #            self.artists[this_id].artists_weights =
            #            [(self.artists[other_id],
            self.artists[this_id].artists_weights = \
                [(other_id,
                  pow(1 + distance(location[this_id], location[other_id]), -a)) for
                 other_id in location.keys()]
            self.artists[this_id].artists_weights.sort(key=lambda(x): -x[1])

    def write_musicspace_file(self, fileobj):
        for a in self.artists.values():
            a.write_music_space_entry(fileobj)

    def graft_subtree(self, subtree):
        '''Use path of new subtree to find graft point, and graft.'''
        # All paths are absolute, so root_path and path are identical
        # up to the length of root path.
        if not subtree.path.startswith(self.path):
            raise DbmError("new subtree %s must lie within the tree rooted at %s" %
                           (path, self.path))
        path = self.path
        subdirs = subtree.path.replace(self.path, '', 1)#.split(os.path.sep)
        next_node = [self]
        for d in subdirs:
            path += os.path.sep + d
            node = next_node
            next_node = [s for s in node[0].subtrees if s.path == path]
            if len(next_node) == 0:
                # Subtree did not previously exist in the tree
                node[0].subtrees.add(subtree)
                break
            elif len(node) > 1:
                raise DbmError('More than one subtree with path %s' % p)
        subtree.parent = node[0]

    def recently_added_nodes(self):
        # I don't think this is working correctly, and I am not using
        # it currently, as sorting directories by date in rockbox has
        # the desired effect.
        
        # root.terminal_nodes = []
        # root.gather_terminal_nodes()
        anodes = artist_nodes(self.artists.values())
        # anodes = filter(lambda anode: len(anode.node.subtrees) == 0, anodes)
        return sorted(anodes, key=lambda anode: anode.node.mtime, reverse=True)
        
class ArtistNode(object):
    """A node may be associated with an artist for a variety of
    reasons. E.g.
    1. It's a folder containing several albums by that artist
    2. It's an album by that artist
    3. It's a compilation album containing a track by that album
    """
    def __init__(self, node, artist, albumartist, album):
        self.node = node
        self.artist = artist
        self.albumartist = albumartist
        self.album = album

    def make_link(self):
        """Construct rockbox format link to this node"""
        link = make_rockbox_path(self.node.path)
        link += '/\t' + self.artist.name
        if self.albumartist and self.albumartist is not self.artist:
            link += ' in '
            if self.album:
                link += self.album + ' by '
            link += self.albumartist.name or ''
        return link

    def show(self):
        print('ArtistNode: %s, %s, %s' %
              ('no node!' if not self.node else self.node.path, self.artist.name, self.albumartist.name))

    def __cmp__(self, other):
        ans = cmp(self.artist, other.artist)
        if ans == 0:
            if self.albumartist:
                if other.albumartist:
                    ans = cmp(self.albumartist, other.albumartist)
                else:
                    ans = -1
            elif other.albumartist:
                ans = 1
            if ans == 0:
                ans = cmp(self.album, other.album)
        return ans

class Artist(object):
    def __init__(self, dbm_aid, name=None):
        self.id = dbm_aid
        self.name = name or most_frequent_element(root.artistnames[dbm_aid]) or '<no name>'
        self.subtrees = set([])
        self.similar_artists = []
        self.tracks = []
        self.tracks_as_albumartist = []
        self.lastfm_name = ''
        self.musicspace_location = []
        self.tags = []
        self.biography = Biography(self)

    def download_lastfm_data(self, biography_only=False, msg_prefix=''):
        if not settings.query_lastfm: return
        waiting = True
        i = 0
        while waiting and i < settings.numtries:
            try:
                if not self.lastfm_name:
                    self.set_lastfm_name()
                name = self.lastfm_name or self.name
                self.pylast = settings.network.get_artist(name)
                
                self.biography.biography = self.pylast.get_bio_content() \
                    or 'No biography available'
                
                if not biography_only:
                    # This implies that we are working on an artist in
                    # the library. Note that we only store biographies
                    # in the .dbm file (i.e. in the root.XXX dicts)
                    # for artists in the library, in order that the
                    # .dbm file stays a reasonable size.
                    try:
                        self.similar_artists = self.query_lastfm_similar()
                    except Exception, e:
                        error('query error: %s' % e)
                    self.tags = [t.item for t in self.pylast.get_top_tags()]
                    for t in self.tags:
                        t.name = canonicalise_tag_name(t.name)
                    root.similar_artists[self.id] = self.similar_artists
                    root.tags_by_artist[self.id] = self.tags
                    root.biographies[self.id] = self.biography
                    logi(msg_prefix + self.download_message(name, True))
                else:
                    logi(msg_prefix + self.biography_download_message(name, True))
                waiting = False
                
            except Exception, e:
                self.biography.biography = 'No biography available'
                name = self.lastfm_name or self.name
                error('%s: %s' % (msg_prefix + self.download_message(name, False), e))
                i = i+1
                time.sleep(.1)
        return not waiting

    def download_message(self, name, successful):
        if successful:
            msg = "%s\t%s" % (name, self.tags[0:5])

            # msg = '%s last.fm query: %s name %s (%s) got %d artists' % (
            #     timenow(),
            #     'validated' if self.lastfm_name else 'unvalidated',
            #     name,
            #     self.id if settings.mbid_regexp.match(self.id) \
            #         else 'no MusicBrainz ID',
            #     len(self.similar_artists))
        else:
            msg = "%s\tFailed" % name
            # msg = '%s last.fm query: %s name %s (%s) FAILED: %s' % (
            #     timenow(),
            #     'validated' if self.lastfm_name else 'unvalidated',
            #     name,
            #     self.id if settings.mbid_regexp.match(self.id) else 'no MusicBrainz ID',
            #     e)

        return msg

    def biography_download_message(self, name, successful):
        if successful:
            msg = name
            # '%s last.fm query: %s name %s (%s) got biography' % (
            #     timenow(),
            #     'validated' if self.lastfm_name else 'unvalidated',
            #     name,
            #     self.id if settings.mbid_regexp.match(self.id) \
            #         else 'no MusicBrainz ID')
        else:
            msg = '%s: Biography download failed' % name

        return msg

    def set_lastfm_name(self):
        if settings.mbid_regexp.match(self.id):
            try:
                self.lastfm_name = \
                    pylast.get_artist_by_mbid(self.id, settings.network).get_name()
            except Exception, e:
                error('Last.fm error for artist %s: %s' % (self.name or self.id, e))
        else:
            self.lastfm_name = self.name

    def query_lastfm_similar(self):
        """Return list of similar artist (mbid, name) tuples. Since
        pylast doesn't currently include mbids in Artist objects, it's
        a bit convoluted to do this with the pylast public API."""

        params = {'artist': self.lastfm_name or self.name}
        doc = pylast._Request(settings.network, "artist.getSimilar", params).execute(True)
        simids = pylast._extract_all(doc, 'mbid')
        simnames = pylast._extract_all(doc, 'name')
        retval = zip(simids, simnames)
        return [(x[0] or None, x[1]) for x in retval]

    def musicspace_similar_artists_playlist(self, n=1000):
        artists = sample(n, self.artists_weights)
# TMP while pickling problems, otherwise I would use artist instance
# referencves rather than dbm_aids
        artists = [root.artists[aid] for aid in artists]
        artists = filter(lambda(a): a.tracks, artists)
        try:
            return [random.sample(artist.tracks, 1)[0] for artist in artists]
        except Exception, e:
            log('Error creating musicspace playlist for %s: %s' % (self.name, e))
            return []

    def musicspace_similar_artists_nodes(self):
        # TMP As noted elsewhere, artists_weights is a list of tuples the
        # first elements of which hold a dbm_aid, rather than a reference to
        # an Artist instance. I would do the latter, except the circular
        # references seemed to fuck up on pickling somehow.
        return [root.artists[x[0]] for x in self.artists_weights]

    def lastfm_similar_and_present_artists(self):
        artists = map(root.lookup_dbm_artist, self.similar_artists)
        artists = filter(lambda a: a and a.is_present(), artists)
        return [self] + artists

    def lastfm_similar_but_absent_artists(self, n):
        """Create Artist objects for similar but absent artists."""
        # Note that artist.similar_artists is a list of (mbid,name)
        # tuples, as returned by artist.query_lastfm_similar()
        similar_artists = filter(lambda x: x[1], self.similar_artists)
        similar_artists = [(root.make_dbm_artistid(*x), x[1]) for x in similar_artists]
        similar_artists = filter(lambda x: not root.artists.has_key(x[0]), similar_artists)
        similar_artists = similar_artists[0:n]
        for dbm_aid, name in similar_artists:
            if not root.all_artists.has_key(dbm_aid):
                root.all_artists[dbm_aid] = Artist(dbm_aid=dbm_aid, name=name)
        
        return [root.all_artists[x[0]] for x in similar_artists]
        
    def unite_spuriously_separated_subtrees(self):
        """This is a bit of a hack / heuristic. If an artist has a
        number of supposedly pure subtrees that all share the same
        parent node (which may also be in the list of pure subtrees),
        then we set the parent node to be the single pure subtree for
        this artist."""
        pure_anodes = [v for v in self.subtrees if v.albumartist is self]
        if len(pure_anodes) > 1:
            # If a single one of the parents is itself in pure_anodes,
            # then we use that as the pure_anode
            parents = [v.node.parent for v in pure_anodes]
            parent = None
            if len(set(parents)) == 1: # collection of siblings without parent
                parent = parents[0]
            else:
                pure_nodes = [v.node for v in pure_anodes]
                parents = [p for p in parents if p in pure_nodes]
                if len(set(parents)) == 1: # collection of siblings with parent
                    parent = parents[0]
            if parent:
                if False and not settings.quiet:
                    warn('uniting %d subtrees for %s' % (len(pure_anodes), self.name))
                anodes = [v for v in self.subtrees if v not in pure_anodes]
                anodes.append(ArtistNode(parent, self, self, None))
                self.subtrees = set(anodes)

    def show(self):
        print('%s %s %d tracks %d albumartist tracks' %
              (self.id.ljust(25), self.name,
               len(self.tracks), len(self.tracks_as_albumartist)))

    def show_musicspace_neighbours(self):
        i = 1
        for w in self.artists_weights:
            print('\t%s%f' % (root.artists[w[0]].name.ljust(30), w[1]))
            i += 1
            if i > 30: break

    def write_music_space_entry(self, fileobj):
        fileobj.write(
            '"%s",%s,' % (self.name,
                          self.id if settings.mbid_regexp.match(self.id) else ''))

        fileobj.write(
            ','.join(map(str, self.musicspace_location)) + \
                ',' * (settings.musicspace_dimension - len(self.musicspace_location)) + '\n')


    def is_present(self):
        "Is the artist present in the library?"
        return len(self.tracks) > 0

    def clean_name(self):
        name = self.name
        name = name.replace('"','').replace('\'','') ## "Weird Al" Yankovic, Guns 'N' Roses
        name = name.replace('/', '').replace('?', '') ## DJ /rupture, Therapy?,
        name = name.replace(':','').replace('*', '') # :wumpscut: ??!!
        name = name[0].upper() + name[1:]
        return name

    def __eq__(self, other):
        return self.id == other.id

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class Biography(object):
    """A class for artist biographies, as obtained from last.fm
    
    The metadata is a dict created by dbm containing information on
    how this artist relates to the library. An example of metadata is
    
    dict(Similar_to=['Tim Hecker', 'Jetone'],
    Listened_to_by=['davisonio', 'Myrmornis'])

    which lists LastFm similar artists for the artist, and LastFm
    Users which have listened to the artist.

    Biographies are stored on disk, and not in the save .dbm library
    object. To avoid accidentally storing biographies in memory, the
    code in this class is slightly odd in that the biography gets
    passed around using function arguments, whereas the metadata is
    stored as an instance attribute.
    """
    metadata_marker = '-------------------'
    def __init__(self, artist):
        self.artist = artist
        self.biography = ''
        self.metadata = {}

    def make_path(self):
        return os.path.join(settings.all_biographies_dir,
                            self.artist.clean_name()[0],
                            self.artist.clean_name() + '.txt')

    def update(self, msg_prefix=''):
        """Write the biography with updated metadata to disk, if
        necessary.  Download the biography if lacking."""
        if not os.path.exists(self.make_path()):
            if not self.biography:
                self.artist.download_lastfm_data(biography_only=True, msg_prefix=msg_prefix)
            if self.biography:
                self.write(strip_html_tags(self.biography))
                self.biography = ''
                return True
            return False
        elif settings.update_biography_metadata and self.metadata:
            (biography, old_metadata) = self.read()
            if self.metadata != old_metadata:
                self.write(biography)
            return True

    def read(self):
        """Read biography (and metadata, if any) from disk and return
        a (biography, metadata) tuple."""
        with codecs.open(self.make_path(), 'r', 'utf-8') as f:
            x = f.read().split(self.metadata_marker, 1)
        biography = unicode(x[0]).strip()
        metadata = self.parse_metadata(unicode(x[1])) if len(x) == 2 else {}
        return (biography, metadata)

    def write(self, biography):
        """Write instance attributes to disk"""
        try:
            mkdirp(os.path.dirname(self.make_path()))
            with codecs.open(self.make_path(), 'w', 'utf-8') as f:
                f.write('\n'.join([biography,
                                   self.metadata_marker,
                                   self.deparse_metadata()]) + '\n')
        except Exception, e:
            error('Failed to write biography for artist %s: %s' % (artist.name, e))

    def merge_metadata(self, new_metadata):
        for k in new_metadata:
            if self.metadata.has_key(k):
                self.metadata[k].add(new_metadata[k])
            else:
                self.metadata[k] = set(new_metadata[k])
    
    def parse_metadata(self, text):
        # Doesn't actually access any instance data, because biography
        # text is passed around with function arguments.
        d = {}
        lines = text.strip().split('\n')
        for l in lines:
            l = l.split(':')
            if len(l) != 2: # misformed metadata line, or colon in metadata
                continue
            key = l[0].strip()
            if not d.has_key(key): d[key] = []
            d[key].extend([s.strip() for s in l[1].split(',')])
            d[key] = sorted(unique(d[key]))
        return d

    def deparse_metadata(self):
        lines = []
        for k in self.metadata:
            lines.append('%s: %s' % (k.replace('_',' '),
                                     ', '.join(self.metadata[k])))
        return '\n'.join(lines)

    def make_link(self):
        """Construct rockbox format link to this node"""
        return make_rockbox_path(self.make_path()) + '\t' + self.artist.name

class Tag(object):
    def __init__(self, name):
        self.name = name
        self.artists = []
        
    def __cmp__(self, other):
        return cmp(self.name, other.name)

class LastFmUser(pylast.User):
    def __init__(self, name):
        pylast.User.__init__(self, name, settings.network)
        self.artist_counts = {}

    def get_weekly_artist_charts_as_dict(self, from_date = None, to_date = None):
        """A modified version of
        pylast.User.get_weekly_artist_charts. Changed to include mbids
        in return data."""

        params = self._get_params()
        if from_date and to_date:
            params["from"] = from_date
            params["to"] = to_date

            doc = self._request("user.getWeeklyArtistChart", True, params)

            mbids = []
            names = []
            counts = []
            for node in doc.getElementsByTagName("artist"):
                mbids.append(pylast._extract(node, "mbid"))
                names.append(pylast._extract(node, "name"))
                counts.append(pylast._number(pylast._extract(node, "playcount")))
            return dict(zip(zip(mbids, names), counts))

    def get_artist_counts(self):
        dates = self.get_weekly_chart_dates()
        dates = dates[-settings.lastfm_user_history_nweeks:]
        progress = ''
        for i in range(settings.lastfm_user_history_nweeks):
            logi("\t\t%s\t[week %d/%d]" % (self.name, i+1, settings.lastfm_user_history_nweeks))
            try:
                chart = self.get_weekly_artist_charts_as_dict(*dates[i])
            except:
                log('Failed to download chart %d' % (i+1))
                continue
            for key in chart:
                artist = root.lookup_dbm_artist(key) or \
                    Artist(dbm_aid=root.make_dbm_artistid(*key), name=key[1])
                if not self.artist_counts.has_key(artist):
                    self.artist_counts[artist] = 0
                self.artist_counts[artist] += chart[key]

    def listened_and_present_artists(self):
        return filter(lambda a: a.is_present(), self.artist_counts.keys())

    def listened_but_absent_artists(self):
        return filter(lambda a: not a.is_present(), self.artist_counts.keys())

    def unlistened_but_present_artists(self):
        present_artists = set(root.artists.values())
        return list(present_artists.difference(self.listened_and_present_artists()))

class Settings(object):
    various_artists_mbid = '89ad4ac3-39f7-470e-963a-56509c546377'
    lastfm = dict(api_key = 'a271d46d61c8e0960c50bec237c9941d',
                  api_secret = '680457c03625980f61e88c319c218d53')
    mbid_regexp = re.compile('[0-9a-fA-F]'*8 + '-' + \
                                 '[0-9a-fA-F]'*4 + '-' + \
                                 '[0-9a-fA-F]'*4 + '-' + \
                                 '[0-9a-fA-F]'*4 + '-' + \
                                 '[0-9a-fA-F]'*12)
    def __init__(self, options=None):
        self.gui = False
        if options:
            attributes = [a for a in dir(options) if a[0] != '_']
            for attr in attributes:
                setattr(self, attr, getattr(options, attr))
        self.network = pylast.get_lastfm_network(**self.lastfm)
    def show(self):
        public = filter(lambda(x): x[0] != '_', dir(self))
        noshow = ['read_file', 'read_module', 'show', 'ensure_value', 'mbid_regexp']
        for attr_name in public:
            if attr_name in noshow: continue
            attr = getattr(self, attr_name)
            print('%s %s %s' % (repr(attr_name), type(attr), attr))

class DbmError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def canonicalise_artist_name(name):
    r1 = re.compile('^the +')
    r2 = re.compile(' +')
    return r2.sub('_', r1.sub('', name.lower()))

def canonicalise_tag_name(name):
    """CamelCase with no hyphens"""
    n = name.replace('-', ' ').replace("'", '')
    n = n.lower().split()
    return ''.join([w[0].upper() + w[1:] for w in n])

def generate_playlist(artists, n=1000):
    artists = filter(lambda a: len(a.tracks) > 0, artists)
    if len(artists) == 0: return []
    # draw sample of artists with replacement (sample size larger than population)    
    artists = [random.sample(artists, 1)[0] for i in range(n)]
    # sample one track for each artist in the playlist
    tracks = [random.sample(a.tracks, 1)[0] for a in artists]    
    return unique(tracks)

def write_playlist(tracks, filepath):
    paths = unique([t.path for t in tracks])
    if settings.target == 'rockbox':
        paths = map(make_rockbox_path, paths)
    try:
        with codecs.open(filepath, 'w', 'utf-8') as plfile:
            plfile.write('\n'.join(paths) + '\n')
    except:
        error('write_playlist: write to file failed')
        log('Character encoding problem while writing playlist, destination file is %s.' % filepath)
        
def write_linkfile(artists, filepath):
    nodes = artist_nodes(artists)
    chunks, filepaths = dbm_split_into_chunks(nodes, filepath)
    for i in range(len(chunks)):
        with codecs.open(filepaths[i], 'w', 'utf-8') as lfile:
            lfile.write('\n'.join([v.make_link() for v in chunks[i]]) + '\n')

def write_biographies_linkfile(artists, filepath, metadata={}):
    biographies = [a.biography for a in sorted(artists)]
    if settings.update_biography_metadata and metadata:
        for b in biographies: b.merge_metadata(metadata)
    chunks, filepaths = dbm_split_into_chunks(biographies, filepath)
    for i in range(len(chunks)):
        links = [b.make_link() for b in chunks[i]]
        with codecs.open(filepaths[i], 'w', 'utf-8') as lfile:
            lfile.write('\n'.join(links) + '\n')

def dbm_split_into_chunks(objects, filepath):
    chunks = split_into_chunks(objects, settings.max_linkfile_entries)
    if len(chunks) > 1:
        warn('Splitting large linkfile %s into %d chunks' % (filepath, len(chunks)))
    filepath = filepath.rsplit('.', 1)
    chunk_labels = ['-%d' % (i+1) for i in range(len(chunks))]
    if len(chunk_labels) > 0: chunk_labels[0] = ''
    filepaths = [filepath[0] + label + '.' + filepath[1] for label in chunk_labels]
    return chunks, filepaths
        
def artist_nodes(artists):
    return flatten([sorted(list(artist.subtrees)) for artist in artists])

def library_relative_path(path):
    "Return path relative to root path"
    if __root_path__:
        return path.replace(__root_path__, '')
    else:
        return path
    
def make_rockbox_path(path):
    """Form path to music on rockboxed player from path on computer.

    If we have

    rootpath = '/media/rockbox/dir/music'
    track = '/media/rockbox/dir/music/artist/album/track.ogg'

    then what we want is '/dir/music/artist/album/track.ogg''
    which is given by

    path_to_rockbox = '/media/rockbox'
    path = track.replace(path_to_rockbox, '', 1)

    under Windows

    rootpath = 'E:\dir\music'
    track = 'E:\dir\music\artist\album\track.ogg'
    path_to_rockbox = 'E:'

    so we should treat os.path.dirname(rootpath) as a guess at path_to_rockbox
    """
    if settings.path_to_rockbox is None:
        settings.path_to_rockbox = os.path.dirname(root.path)

    path = path.replace(settings.path_to_rockbox, '', 1)

    if os.name == 'posix':
        return path
    else:
        # TMP hack: path_to_rockbox is something like 'E:\\' which
        # ends up replacing the directory separator required for
        # absolute pathname
        if path[0] != os.path.sep:
            path = os.path.sep + path
        path = path.replace('\\', '/') ## rockbox uses linux-style path separators
        return path

def make_rockbox_link(target, name):
    return make_rockbox_path(target) + '\t' + name

def make_rockbox_linkfile(targets, names, filepath):
    links = [make_rockbox_link(*tn) for tn in zip(targets, names)]
    try:
        with codecs.open(filepath, 'w', 'utf-8') as lfile:
            lfile.write('\n'.join(links) + '\n')
    except:
        error('Failed to write linkfile %s' % filepath)

def rockbox_clean_name(s):
    bad = '\/:<>?*|'
    for c in bad:
        s = s.replace(c, '_')
    s = s.replace('"', "'")
    return s

def patch_out_of_date_data_structures():
    if isinstance(root.path, str):
        root.decode_strings()
    if not hasattr(root, 'all_artists'):
        root.all_artists = root.artists.copy()
    if not hasattr(root, 'lastfm_users'):
            root.lastfm_users = {}
    if not hasattr(root, 'biographies'):
            root.biographies = {}

    for artist in root.all_artists.values():
        if not hasattr(artist, 'biography'):
            artist.biography = Biography(a)
        m = artist.biography.metadata
        for k in m: m[k] = set(m[k])

        if not hasattr(artist, 'musicspace_location'):
            artist.musicspace_location = []


