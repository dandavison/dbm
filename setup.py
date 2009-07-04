#!/usr/bin/env python

from distutils.core import setup
import sys, py2exe
import dbm

sys.argv.append('py2exe')

setup(
    name=dbm.__progname__,
    version=dbm.__version__,
#    author=dbm.__author__,
#    author_email=dbm.__email__,
#    url=dbm.__url__,
#    license="GNU General Public License (GPL)",
#    packages=['dbm','mutagen','pylast','python-musicbrainz2'],
#    package_data={"dbm": ["images/*"]},
#       scripts=["bin/dbm"],
#       windows=[{"script": "bin/dbm"}],
#    data_files = [('..\Python26\DLLs',['MSVCP90.dll'])],
    data_files = [('.',['MSVCP90.dll'])],
    windows=[{"script": "dbm.pyw"}],
    options={"py2exe": {"bundle_files": 1, "includes": ["sip"]}},
    zipfile=None)
