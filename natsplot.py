#!/usr/bin/env python
#
# NavPlot - Download NOTAMs from www.ais.org.uk and generate PDF viewer file.
# Copyright (C) 2005  Alan Sparrow
# alan at freeflight dot org dot uk
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import notamdoc
import getopt
import datetime
import re
import sys
import time
import HTMLParser
import urllib2

# Try Python 2.4 built in cookielib, else fallback to 3rd party ClientCookie
cookielib = None
try:
    import cookielib
except ImportError:
    import ClientCookie

#------------------------------------------------------------------------------
# Modify stuff here as required

# Username and password for AIS self-briefing
USERNAME=''
PASSWORD=''

# Flight information regions for area briefing
FIRS = ('EGTT', )

# Map origin and scaling
DFLT_LATITUDE = 50.2
DFLT_LONGITUDE = -4.5
DFLT_WIDTH = 6.0

# Regex for the Q-line and NOTAM text
QGroupRe = re.compile(r'^Q\)'
    r'(?P<fir>[A-Z]+)/'
    r'(?P<qcode>Q[A-Z]+)/'
    r'(?P<traffic>[IV]+)/'
    r'(?P<purpose>[NBOM]+)/'
    r'(?P<scope>[AEW]+)/'
    r'(?P<lower>\d+)/'
    r'(?P<upper>\d+)/'
    r'(?P<centre>\d{4}[NS]\d{5}[EW])(?P<radius>\d{3})[ ]*\n'
    r'(?P<text>(?:[ \t]*\S.*\n)+)', re.MULTILINE)

ENROUTE_HEADER = 'E N - R O U T E - I N F O R M A T I O N'

COPYRIGHT_HOLDER = 'NATS Ltd'

#------------------------------------------------------------------------------
# HMTL parser for AIS area briefing

class PibHtmlParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.preTag = False
        self.pibData = False
        self.notams = {}
        self.badCount = False

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.preTag = True
        elif tag == 'a':
            if self.preTag and attrs:
                if attrs[0][0] == 'name' and attrs[0][1] == 'notampib':
                    self.pibData = True

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.preTag = False

    def handle_data(self, data):
        if self.pibData:
            sdata = data.replace('\r', '')
            self.header = sdata[:sdata.find('--------')]
            ndata = sdata[sdata.find(ENROUTE_HEADER):]

            # Count number of Q-lines
            qcount = ndata.count('\nQ)')

            # Iterrate through NOTAMs storing only the NAVWs
            ncount = 0
            self.notams = []
            for notam in QGroupRe.finditer(ndata):
                ncount += 1
                ndict = notam.groupdict()
                self.notams.append(ndict)

            self.pibData = False
            if qcount != ncount:
                self.badCount = True

#-----------------------------------------------------------------------------
# Returns number of NOTAMS displayed. Zero if no notams can be retreived and
# -1 if there is an inconsistancy in the NOTAM count

def navplot(filename, firs, start_date, num_days, username, password, mapinfo):
    if cookielib:
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    else:
        cj = ClientCookie.CookieJar()
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))

    # Login to AIS (and get the security cookie)
    url = 'http://www.ais.org.uk/aes/j_security_check?'\
          'j_username=%s&j_password=%s'
    opener.open(url % (username, password))

    # Get NOTAM information
    url = 'http://www.ais.org.uk/aes/control/briefing?'\
          'HF_ACTION=send&'\
          'VF_STARTTIME=0001&'\
          'VF_STARTDATE=%(startdate)s&'\
          'VF_ENDTIME=2359&'\
          'VF_ENDDATE=%(enddate)s&'\
          'VF_FIR0=%(fir0)s&'\
          'VF_FIR1=%(fir1)s&'\
          'VF_LEVLOW=000&'\
          'VF_LEVUP=100&'\
          'VF_ARCID=NPLT&'\
          'VF_ADES=EGDM&'\
          'VF_ADEP=EGDM&'\
          'VF_EOBT=&'\
          'VF_EOBD=&'\
          'VF_NOTAMPIB=NOTAMPIB&'\
          'VF_METEOPIB=&'\
          'VF_PURPOSE=+NBO+BO+B+M+NM&'\
          'VF_TRAFFIC=+V+IV&'\
          'VF_MAXVALID=&'\
          'HF_PAGEID=briefing_area&'\
          'HF_PAGETYPE=briefing_area&'\
          'HF_IS_DOMESTIC=true&'\
          'HF_FORMAT=ASCII&'\
          'HF_DOM_ICAO_CD=EG&'\
          'HF_HELPFIELD='

    if len(firs)>1:
        fir1 = firs[1]
    else:
        fir1 = ''
    start_str = start_date.strftime('%y%m%d')
    end_str = (start_date + datetime.timedelta(num_days-1)).strftime('%y%m%d')
    url = url % {'startdate': start_str,
                 'enddate': end_str,
                 'fir0': firs[0],
                 'fir1': fir1}

    # Filter the NAVW's
    pibParser = PibHtmlParser()
    pibParser.feed(opener.open(url).read())

    if pibParser.notams:
        notamdoc.notamdoc(pibParser.notams, pibParser.header, firs, start_date,
                          num_days, filename, mapinfo, COPYRIGHT_HOLDER)

    if pibParser.badCount:
        return -1
    else:
        return len(pibParser.notams)

#------------------------------------------------------------------------------

def usage():
    print 'usage: navplot [options] PDF_filename'
    print ''
    print 'Options:'
    print '    -d    Number of days offset from today'
    print '    -n    Number of days to get (default 1)'
    print '    -p    AIS password'
    print '    -u    AIS username'
    print '    -x    Proxy http server, e.g. garlic:80'

#------------------------------------------------------------------------------

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:n:p:u:h')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Get any options
    day_delta = 0
    ndays = 1
    username = USERNAME
    password = PASSWORD
    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit()
        if o == '-d':
            # Convert days to seconds
            day_delta = int(a)
        if o == '-n':
            ndays = int(a)
        if o == '-u':
            username = a
        if o == '-p':
            password = a

    # Get the PDF filename
    if len(args) != 1:
        usage()
        sys.exit(2)
    else:
        pdf = args[0]

    # Work with UTC times/dates
    start_date = datetime.datetime.utcnow().date() +\
                 datetime.timedelta(day_delta)

    n = navplot(pdf, FIRS, start_date, ndays, username, password,
                (DFLT_LATITUDE, DFLT_LONGITUDE, DFLT_WIDTH))
    if n==0:
        sys.stderr.write("Can't get any NOTAMS, check user name and password\n")
    elif n==-1:
        sys.stderr.write('WARNING: Inconsistent NOTAM/QLINE count\n')

if __name__ == '__main__':
    main()
