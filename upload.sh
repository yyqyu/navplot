#!/bin/bash

tar czf navplot.tar.gz eadplot.py gnavplot.py gpl.txt map.dat navplot.ico \
navplot.iss notamdoc.py readme.txt setup.py

# HTML
DEST=ftp://digbyhouse:sdfjkl11@ftp.plus.net/htdocs/freeflight/dist/navplot
wput Output/setup.exe $DEST/setup.exe
wput navplot.pdf $DEST/
wput navplot.tar.gz $DEST/
