NavPlot
Copyright (C) 2005-8 Alan Sparrow
alan at freeflight dot org dot uk

1. Running the program -
    From the command line - python navplot.py [options] pdf_file
    Or use the Windows standalone executable

2. Requirements (for command line version) -
    Python 2.4 or greater (www.python.org)
    ReportLab Open Source PDF library (www.reportlab.org)
    (For Windows GUI) wxPython GUI toolkit (www.wxpython.org)

3. Build instructions for Windows standalone executable -
    python setup.py py2exe - builds windows executable in dist directory.
    (Requires py2exe from www.py2exe.org)

    To build a windows installation program run the Inno Setup script
    navplot.iss. (Requires the Inno Setup installer program from
    http://www.jrsoftware.org)

Acknowledgements:
  Airspace data from Rory O'Conor - http://www.btinternet.com/~rory.oconor
  Coast line from http://rimmer.ngdc.noaa.gov/mgg/coast/getcoast.html

Upload instructions

0. Change version number in gnavplot.py and navplot.iss

1. Generate example navplot.pdf and copy to /htdocs/freeflight/dist/navplot/

2. Make navplot.tar.gz and copy to .../dist/navplot

3. Make setup.exe and copy to .../dist/navplot

4. Update /htdocs/freeflight/software/index.htm
