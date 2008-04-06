from distutils.core import setup
import py2exe

setup(windows=["gnavplot.py"],
      data_files=[('.',
                  ('map.dat',
                   'navplot.ico',
                   'gpl.txt',
                   'readme.txt'))])
