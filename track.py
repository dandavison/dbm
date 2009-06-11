import sys, os
import mutagen.oggvorbis
import mutagen.flac
import mutagen.mp3
import mutagen.mp4
import mutagen.musepack
import util

mutagen_readtags_function = {'ogg'  : lambda(x): mutagen.oggvorbis.Open(x),
                             'mp3'  : lambda(x): mutagen.mp3.Open(x),
                             'mpc'  : lambda(x): mutagen.musepack.Open(x),
                             'mp4'  : lambda(x): mutagen.mp4.Open(x),
                             'm4a'  : lambda(x): mutagen.mp4.Open(x),
                             'flac' : lambda(x): mutagen.flac.Open(x)}

def elog(msg, end='\n'):
    try:
        sys.stderr.write(msg.encode('utf-8') + end)
    except:
        sys.stderr.write('ERROR: Failed to write elog message\n')
    

def is_music(path):
    return (os.path.isfile(path) or os.path.islink(path)) \
        and os.path.splitext(path)[1] in ['.ogg','.flac','.mp3','.mpc','.m4a']

class Track:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            raise Exception("path does not exist: %s" % path)
            
        self.format = os.path.splitext(path)[1][1:]

        self.dbm_artistid = u''
        self.artistid = u''
        self.artistname = u''

        self.dbm_albumartistid = u''

        self.albumartistid = u''
        self.albumartistname = u''

        self.releasename = u''
        self.releaseid = u''

        self.artist = None
        self.albumartist = None
        
        try:
            self.set_tags() # TMP
        except:
            elog('failed to read tags for %s' % self.path)

        try:
            self.set_tags()
            util.decode_strings(self)
        except:
            elog('failed to read tags for %s' % self.path)
        self.valid = True if (self.artistid or self.artistname) else False

    def set_tags(self):
        """Read metadata tags from music file at `path' using
        mutagen. This creates a rather complicated list structure,
        especially for mp3s, which I parse further using the
        parse_mutagen_* functions."""
        tags = mutagen_readtags_function[self.format](self.path)
        if self.format == 'mp3':
            self.parse_mutagen_tags_mp3(tags)
        if self.format == 'mpc':
            self.parse_mutagen_tags_mpc(tags)
        elif self.format == 'm4a':
            try:
                self.parse_mutagen_tags_m4a(tags)
            except MP4StreamInfoError, msg:
                elog('m4a tag read problem: %s', msg)
                raise
        elif self.format in ['ogg', 'flac']:
            self.parse_mutagen_tags_ogg_flac(tags)
            
    def show(self):
        for att in dir(self):
            if att[0] == '_': continue
            try:
                print('\t%s %s' % (att.ljust(25), repr(getattr(self, att))))
            except (UnicodeEncodeError, UnicodeDecodeError):
                print('Couldn\'t print unicode data')
                
    # >>> tags = mutagen.oggvorbis.Open('/media/disk/music/Joanna_Newsom/Ys/01_Emily.ogg')

    # >>> for k in tags:
    # ... 	
    # ... 
    # albumartistsort                     [u'Newsom, Joanna']
    # producer                            [u'Van Dyke Parks', u'Joanna Newsom']
    # releasecountry                      [u'GB']
    # albumartist                         [u'Joanna Newsom']
    # musicbrainz_albumartistid           [u'cb69e1f1-bc76-4df5-93c9-cf97dd8a3b5c']
    # catalognumber                       [u'DC303CD']
    # tracknumber                         [u'1']
    # label                               [u'Drag City']
    # album                               [u'Ys']
    # asin                                [u'B000I2K9M4']
    # musicbrainz_artistid                [u'cb69e1f1-bc76-4df5-93c9-cf97dd8a3b5c']
    # discid                              [u'490d0e05']
    # title                               [u'Emily']
    # performer                           [u'Van Dyke Parks (accordion)', u'Don Heffington (percussion instruments)', u'Matt Cartsonis (banjo and mandolin)', u'Peter Kent (violin)', u'Leland Sklar (electric bass guitar)', u'Grant Geissman (electric guitar)']
    # tracktotal                          [u'5']
    # musicbrainz_trackid                 [u'e01a4a1e-337e-4161-8968-5cf1bf321a13']
    # musicbrainz_discid                  [u'W_mwVNeYnVTlD1E1Hw7qTFKAvRc-']
    # artistsort                          [u'Newsom, Joanna']
    # conductor                           [u'Van Dyke Parks']
    # format                              [u'CD']
    # barcode                             [u'781484030324']
    # releasestatus                       [u'official']
    # date                                [u'2006-11-06']
    # language                            [u'eng']
    # artist                              [u'Joanna Newsom']
    # script                              [u'Latn']
    # releasetype                         [u'album']
    # mixer                               [u"Jim O'Rourke"]
    # musicbrainz_albumid                 [u'894ff003-8e94-4faf-bdc0-b9a1a3349d16']
    # totaltracks                         [u'5']
    # arranger                            [u'Van Dyke Parks']

    #------------------------------------------------------------------------------------------------
    # tags = mutagen.flac.Open('/media/Apus/All/Arvo_Part/2005_-_Lamentate/02_Lamentate__I._Minacciando.flac')

    # >>> for k in tags:
    # ... 	print k.ljust(35), tags[k]
    # ... 
    # album                               [u'Lamentate']
    # asin                                [u'B000A69QCW']
    # albumartistsort                     [u'P\xe4rt, Arvo']
    # musicbrainz_artistid                [u'ae0b2424-d4c5-4c54-82ac-fe3be5453270']
    # language                            [u'ita']
    # artist                              [u'Arvo P\xe4rt']
    # title                               [u'Lamentate: I. Minacciando']
    # releasetype                         [u'album']
    # releasecountry                      [u'US']
    # musicbrainz_albumid                 [u'1db96e72-3213-4c07-aec3-c0537abe8ce1']
    # releasestatus                       [u'official']
    # totaltracks                         [u'11']
    # script                              [u'Latn']
    # albumartist                         [u'Arvo P\xe4rt']
    # musicbrainz_albumartistid           [u'ae0b2424-d4c5-4c54-82ac-fe3be5453270']
    # artistsort                          [u'P\xe4rt, Arvo']
    # date                                [u'2005-08-30']
    # tracknumber                         [u'2']
    # musicbrainz_trackid                 [u'47cb7f4e-f93b-4716-913d-f1c5c6a6dc5d']


    def parse_mutagen_tags_ogg_flac(self, tags):
        mkeys = tags.keys()
        # artist name
        k = 'artist'
        self.artistname = tags.has_key(k) and tags[k][0] or ''
        # artist id
        k = 'musicbrainz_artistid'
        self.artistid = tags.has_key(k) and tags[k][0] or ''
        # album artist id
        k = 'musicbrainz_albumartistid'
        self.albumartistid = tags.has_key(k) and tags[k][0] or ''
        # album artist name
        k = 'albumartist'
        self.albumartistname = tags.has_key(k) and tags[k][0] or ''
        # release name
        k = 'album'
        self.releasename = tags.has_key(k) and tags[k][0] or ''
        # release id
        k = 'musicbrainz_albumid'
        self.releaseid = tags.has_key(k) and tags[k][0] or ''
        # track name
        k = 'title'
        self.trackname = tags.has_key(k) and tags[k][0] or ''
        # track id
        k = 'musicbrainz_trackid'
        self.trackid = tags.has_key(k) and tags[k][0] or ''


    # tags = mutagen.mp4.Open('/media/Apus/All/Sun_Kil_Moon/April/02_The_Light.m4a')

    # >>> for k in tags:
    # ... 	print k.ljust(35), tags[k]
    # ... 
    # trkn                                [(2, 11)]
    # ----:com.apple.iTunes:MusicBrainz Artist Id ['ef2c6449-d02b-415b-ad8c-c14c08266552']
    # ----:com.apple.iTunes:MusicBrainz Track Id ['45c051d8-e2cb-4fb8-82fc-8a952cf6ea72']
    # disk                                [(1, 2)]
    # ----:com.apple.iTunes:iTunNORM      [' 00000416 000004E4 000043E1 000042DB 000687E7 000687FE 00007EDD 00007F69 00065552 000668FF']
    # soaa                                [u'Sun Kil Moon']
    # \xa9too                                [u'iTunes v7.5.0.20, QuickTime 7.3']
    # ----:com.apple.iTunes:iTunSMPB      [' 00000000 00000840 00000100 00000000013BF6C0 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000']
    # ----:com.apple.iTunes:iTunes_CDDB_IDs ['11+81F6936C87F6D2FFE224AD4ABAAC27F5+10743450']
    # soar                                [u'Sun Kil Moon']
    # \xa9alb                                [u'April']
    # tmpo                                [0]
    # \xa9day                                [u'2008-04-01']
    # aART                                [u'Sun Kil Moon']
    # cpil                                False
    # ----:com.apple.iTunes:MusicBrainz Album Artist Id ['ef2c6449-d02b-415b-ad8c-c14c08266552']
    # ----:com.apple.iTunes:MusicBrainz Album Release Country ['US']
    # ----:com.apple.iTunes:MusicBrainz Album Id ['5ef112fd-8b07-4808-9877-b38651c52e86']
    # ----:com.apple.iTunes:CATALOGNUMBER ['CV 006']
    # ----:com.apple.iTunes:MusicIP PUID  ['018caa19-2687-0a8b-066e-bf4280b9b140']
    # \xa9ART                                [u'Sun Kil Moon']
    # ----:com.apple.iTunes:MusicBrainz Album Type ['album']
    # ----:com.apple.iTunes:MusicBrainz Album Status ['official']
    # ----:com.apple.iTunes:ASIN          ['B00158FK42']
    # \xa9nam                                [u'The Light']
    # ----:com.apple.iTunes:LABEL         ['Caldo Verde Records']
    # pgap                                False
    # \xa9gen                                [u'Rock']

    def parse_mutagen_tags_m4a(self, tags):
        mkeys = tags.keys()
        # artist name
        k = '\xa9ART'
        self.artistname = tags.has_key(k) and tags[k][0] or ''
        # artist id
        k = '----:com.apple.iTunes:MusicBrainz Artist Id'
        self.artistid = tags.has_key(k) and tags[k][0] or ''
        # album artist name
        key = 'aART'
        self.albumartistname = tags.has_key(key) and tags[key][0] or ''
        # album artist id
        key = '----:com.apple.iTunes:MusicBrainz Album Artist Id'
        self.albumartistid = tags.has_key(key) and tags[key][0] or ''
        # release name
        k = '\xa9alb'
        self.releasename = tags.has_key(k) and tags[k][0] or ''
        # release id
        k = '----:com.apple.iTunes:MusicBrainz Album Id'
        self.releaseid = tags.has_key(k) and tags[k][0] or ''
        # track name
        k = '\xa9nam'
        self.trackname = tags.has_key(k) and tags[k][0] or ''
        # track id
        k = '----:com.apple.iTunes:MusicBrainz Track Id'
        self.trackid = tags.has_key(k) and tags[k][0] or ''
        
        
# >>> for k in tags:
# ... 	print k.ljust(35), repr(tags[k])
# ... 
# TSSE                                TSSE(encoding=0, text=[u'LAME v3.97'])
# TCMP                                TCMP(encoding=3, text=[u'1'])
# TIPL                                TIPL(encoding=3, people=[[u'DJ-mix', u'Luke Slater']])
# UFID:http://musicbrainz.org         UFID(owner=u'http://musicbrainz.org', data='6a22f258-12cc-4ff9-b28a-62cb1ce07531')
# TDRC                                TDRC(encoding=3, text=[u'2001-09-24'])
# TXXX:ALBUMARTISTSORT                TXXX(encoding=3, desc=u'ALBUMARTISTSORT', text=[u'Slater, Luke'])
# TIT2                                TIT2(encoding=3, text=[u'Birdland'])
# TXXX:MusicBrainz Album Type         TXXX(encoding=3, desc=u'MusicBrainz Album Type', text=[u'compilation'])
# TXXX:MusicBrainz Album Id           TXXX(encoding=3, desc=u'MusicBrainz Album Id', text=[u'846e784c-81bd-48bd-a684-cd9d291033d4'])
# TSOP                                TSOP(encoding=3, text=[u'Birdland'])
# TXXX:MusicBrainz Artist Id          TXXX(encoding=3, desc=u'MusicBrainz Artist Id', text=[u'29238808-01a7-48bc-847b-8749ed034c77'])
# TRCK                                TRCK(encoding=0, text=[u'1/24'])
# TPE2                                TPE2(encoding=3, text=[u'Luke Slater'])
# TPE1                                TPE1(encoding=3, text=[u'Birdland'])
# TALB                                TALB(encoding=3, text=[u'Luke Slater: Fear and Loathing (disc 1)'])
# TXXX:MusicBrainz Album Artist Id    TXXX(encoding=3, desc=u'MusicBrainz Album Artist Id', text=[u'2dea2870-5f17-42f7-ac32-d76ccde70dbd'])
# TXXX:MusicBrainz Album Release Country TXXX(encoding=3, desc=u'MusicBrainz Album Release Country', text=[u'GB'])
# TCON                                TCON(encoding=0, text=[u'Vocal'])
# TXXX:MusicBrainz Album Status       TXXX(encoding=3, desc=u'MusicBrainz Album Status', text=[u'official'])

        
    def parse_mutagen_tags_mp3(self, tags):
        # artist name
        k = 'TPE1' # how is 'TSOP' different?
        self.artistname = tags.has_key(k) and tags[k].text[0] or ''
        # artist id
        k = 'TXXX:MusicBrainz Artist Id'
        self.artistid = tags.has_key(k) and tags[k].text[0] or ''
        # album artist name
        k = 'TPE2'
        self.albumartistname = tags.has_key(k) and tags[k].text[0] or ''
        # album artist id
        k = 'TXXX:MusicBrainz Album Artist Id'
        self.albumartistid = tags.has_key(k) and tags[k].text[0] or ''
        # release name
        k = 'TALB'
        self.releasename = tags.has_key(k) and tags[k].text[0] or ''
        # release id
        k = 'TXXX:MusicBrainz Album Id'
        self.releaseid = tags.has_key(k) and tags[k].text[0] or ''
        # track name
        k = 'TIT2'
        self.trackname = tags.has_key(k) and tags[k].text[0] or ''
        # track id
        k = 'UFID:http://musicbrainz.org'
        self.trackid = tags.has_key(k) and tags[k].data or ''



#     >>> tags = mutagen.musepack.Open('/home/dan/music/dbm/03_Plush.mpc')
# >>> for k in tags:
# ... 	print k.ljust(35), repr(tags[k].value)
# ... 
# Comment                             ' '
# Album                               'Unplugged'
# Albumartistsort                     'Stone Temple Pilots'
# Musicbrainz_Artistid                '8c32bb01-58a3-453b-8050-8c0620edb0e5'
# MUSICBRAINZ_ALBUMSTATUS             'official'
# Language                            'eng'
# Title                               'Plush'
# Track                               '3/7'
# Script                              'Latn'
# Album Artist                        'Stone Temple Pilots'
# Musicbrainz_Trackid                 '8941a4aa-c502-44e0-b157-b074f706e506'
# Musicbrainz_Albumid                 '9fdff304-7380-474f-b8fe-5e346e8541b7'
# Artistsort                          'Stone Temple Pilots'
# Musicbrainz_Albumartistid           '8c32bb01-58a3-453b-8050-8c0620edb0e5'
# MUSICBRAINZ_ALBUMTYPE               'live'
# Year                                '1993 - 1999'
# Genre                               'Acoustic'
# Artist                              'Stone Temple Pilots'

    def parse_mutagen_tags_mpc(self, tags):
        # artist name
        k = 'Artist' # how is 'TSOP' different?
        self.artistname = tags.has_key(k) and tags[k].value or ''
        # artist id
        k = 'Musicbrainz_Artistid'
        self.artistid = tags.has_key(k) and tags[k].value or ''
        # album artist name
        k = 'Album Artist'
        self.albumartistname = tags.has_key(k) and tags[k].value or ''
        # album artist id
        k = 'Musicbrainz_Albumartistid'
        self.albumartistid = tags.has_key(k) and tags[k].value or ''
        # release name
        k = 'Album'
        self.releasename = tags.has_key(k) and tags[k].value or ''
        # release id
        k = 'Musicbrainz_Albumid'
        self.releaseid = tags.has_key(k) and tags[k].value or ''
        # track name
        k = 'Title'
        self.trackname = tags.has_key(k) and tags[k].value or ''
        # track id
        k = 'Musicbrainz_Trackid'
        self.trackid = tags.has_key(k) and tags[k].value or ''
