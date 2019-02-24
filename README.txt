NavPlot
Copyright (C) 2005-14 Alan Sparrow
navplot at freeflight dot org dot uk

1. Running the program -
    From the command line - python eadplot.py [options] pdf_file
    Or use the Windows standalone executable

2. Requirements (for command line version) -
    Python 2.4 or greater (www.python.org)
    ReportLab Open Source PDF library (www.reportlab.org)use: pip install reportlab
    (For Windows GUI) wxPython GUI toolkit (www.wxpython.org) use: pip install -U wxPython

3. Build instructions for Windows standalone executable -
    pyinstaller gnavplot.spec - builds windows executable in dist directory.
    (Requires pyinstaller from www.pyinstaller.org)use: pip install pyinstaller

    To build a windows installation program run the Inno Setup script
    navplot.iss. (Requires the Inno Setup installer program from
    http://www.jrsoftware.org)

Acknowledgements:
  Airspace data from Geoff Brown
  Coast line from http://rimmer.ngdc.noaa.gov/mgg/coast/getcoast.html

Upload instructions

0. Change version number in gnavplot.py, setup.py and navplot.iss

1. Generate example navplot.pdf and copy to .../assets/navplot/

2. Make setup.exe and copy to .../assets/navplot/

4. Update website
