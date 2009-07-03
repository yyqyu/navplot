from distutils.core import setup
import py2exe

data_files = []

# Add Navplot related data files
data_files += [('.', ('map.dat', 'navplot.ico', 'gpl.txt', 'readme.txt'))]

# Additional DLL's required for Python v2.5
data_files += [('.',
    ('C:\Python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll',
     'C:\Python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll'))]

setup(windows=["gnavplot.py"], data_files=data_files)
