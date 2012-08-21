from distutils.core import setup
import py2exe

setup(console=['cbhealthchecker'],
         options={'py2exe': {'bundle_files': 1}},
         zipfile=None)