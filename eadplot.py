#!/usr/bin/env python
#
# NavPlot - Download NOTAMs from www.ead.eurocontrol.int and generate PDF viewer
# file.
# Copyright (C) 2005-2008  Alan Sparrow
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

import cookielib
import datetime
import getopt
import htmlentitydefs
import re
import sys
import time
import urllib
import urllib2
import xml.etree.ElementTree as ET

import notamdoc

#------------------------------------------------------------------------------
# Modify stuff here as required

# Username and password for EAD
USERNAME=''
PASSWORD=''

# Flight information regions for area briefing
FIRS = ('EGTT', )

# Map origin and scaling
DFLT_LATITUDE = 50.2
DFLT_LONGITUDE = -4.5
DFLT_WIDTH = 6.0

NOTAM_PROVIDER = 'EAD'
COPYRIGHT_HOLDER = 'EUROCONTROL'

class NavplotError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#------------------------------------------------------------------------------
def parse_notams(notam_root):
    """Parse XML data from EAD and produce NOTAM dictionary"""
    notam_dict = {}
    for n in notam_root.findall('FIRSection/*/NotamList/Notam'):
        # Make unique notam identifier
        id = n.findtext('Series') + n.findtext('Number') + '/' +\
             n.findtext('Year')

        # Start packing interesting stuff into a dictionary
        notam = {}
        notam['id'] = id
        notam['centre'] = n.findtext('Coordinates')
        notam['radius'] = int(n.findtext('Radius'))
        notam['qcode'] = 'Q' + n.findtext('QLine/Code23') +\
                               n.findtext('QLine/Code45')

        # Start time
        notam['start'] = datetime.datetime(
            *(time.strptime(n.findtext('StartValidity'), '%y%m%d%H%M')[0:6]))

        # End time
        if n.findtext('EndValidity') == 'PERM':
            notam['end'] = datetime.datetime(
                datetime.date.today().year, 12, 31, 23, 59)
        else:
            notam['end'] = datetime.datetime(
                *(time.strptime(n.findtext('EndValidity'), '%y%m%d%H%M')[0:6]))

        # Body text
        item_d = n.findtext('ItemD', '')
        item_e = n.findtext('ItemE', '')
        if item_d:
            body = item_d + '\n' + item_e
        else:
            body = item_e

        item_f = n.findtext('ItemF', '')
        if item_f:
            item_g = n.findtext('ItemG', '')
            body += '\n' + item_f + ' - ' + item_g
        notam['text'] = body

        # Add to overall dictionary (automatically removing duplicates)
        notam_dict[id] = notam

    return notam_dict.values()

#------------------------------------------------------------------------------
def encode_multipart_formdata(fields):
    """Convert dictionary to POST multipart form data"""
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for key in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(fields[key])
    L.append('--' + BOUNDARY + '--')
    L.append('')
    data = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, data

def unescape(text):
    """Unescape HTML entities - code from Fredrik Lundh"""
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

#------------------------------------------------------------------------------
def navplot(pdf_filename, firs, start_date, num_days, username, password,
            mapinfo):
    """Download NOTAM data from EAD Basic website, parse NOTAM data and
       convert to PDF document."""

    # Build url opener with cookie handling
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    # Login to EAD
    url_base = 'http://www.ead.eurocontrol.int'
    url = url_base + '/publicuser/public/pu/login.do'
    values = {
        'user': username,
        'password': password
    }
    data = urllib.urlencode(values)
    response = opener.open(url, data)

    # Get applications page search for URL path (including authenication cookie)
    # for the NOTAM app
    url = url_base + "/publicuser/protect/pu/applicationenter.do"
    response = opener.open(url)
    s = re.search("'Generate PIB', '([^']*)", response.read())
    if s is None:
        raise NavplotError("Can't get NOTAM application path")
    notam_gen_path = s.group(1)

    # Calculate duration (with adjustment if we are part way though day 1)
    duration = num_days*24
    if start_date==datetime.date.today():
        utc = datetime.datetime.utcnow()
        duration -= utc.hour + 1
        start_hour = "%02d" % utc.hour
        start_min = "%02d" % utc.minute
    else:
        start_hour = "00"
        start_min = "00"

    # Build POST data for NOTAM request
    values = {
        #'action': 'generate',
        'PIBSubject': 'navplot',
        'Validity/Day': start_date.strftime('%d'),
        'Validity/Month': start_date.strftime('%b').upper(),
        'Validity/Year': start_date.strftime('%Y'),
        'Validity/Hour': start_hour,
        'Validity/Minute': start_min,
        'Validity/Duration': str(duration),
        'Traffic': 'V',
        'Purpose': 'BM',
        'FlightLevel/UpperFL': '100',
        'FlightLevel/LowerFL': '000',
        'MessageTypeList': 'SNOWTAM',
        'Controls/Aerodrome': '',
        'Controls/FIR': ''
    }
    for n, fir in enumerate(firs):
        values['SimpleGeoFilter/FIRList/FIR[%d]/ICAO' % (n+1)] = fir

    # POST multipart (why???) encoded NOTAM request
    url = url_base + notam_gen_path + "?action=generate"
    content_type, data = encode_multipart_formdata(values)
    request = urllib2.Request(url=url, data=data)
    request.add_header('content-type', content_type)
    response = opener.open(request)

    # POST returns the orignal page with wanted NOTAM info in the 'onload'
    # attribute of the HTML body
    s = re.search("onload=\"window.open\('([^']*)'\)", response.read())
    if s is None:
        raise NavplotError("Can't get NOTAM page")
    notam_path = unescape(s.group(1))
    notam_path = re.sub("PIBLayout=HTML", "PIBLayout=XML", notam_path)

    # Get briefing in XML format and convert to an ElementTree
    url = url_base + notam_path
    response = opener.open(url)
    xml_str = response.read()
    root = ET.fromstring(xml_str)

    # Logout from EAD
    url = url_base + '/publicuser/public/pu/logout.do'
    opener.open(url)

    # Parse NOTAMS from XML
    notams = parse_notams(root)

    # Make header text
    if len(notams):
        hdr = root.find('AreaPIBHeader')
        hdr_text = '%s - %s\n' % (hdr.findtext('AuthorityName'),
                                  hdr.findtext('AuthorityTitle'))
        hdr_text += 'Issued: %s\n' % hdr.findtext('Issued')
        hdr_text += 'Validity: %s to %s\n' % (hdr.findtext('Validity/ValidFrom'),
                                              hdr.findtext('Validity/ValidTo'))
        hdr_text += 'Height Limits: Lower FL%s, Upper FL%s\n' %\
            (hdr.findtext('FlightLevel/LowerFL'),
             hdr.findtext('FlightLevel/UpperFL'))

        # Build NOTAM PDF document
        notamdoc.notamdoc(notams, hdr_text, firs, start_date, num_days,
                          pdf_filename, mapinfo, COPYRIGHT_HOLDER)

    return len(notams)

#------------------------------------------------------------------------------
def usage():
    print 'usage: eadplot [options] PDF_filename'
    print ''
    print 'Options:'
    print '    -d    Number of days offset from today'
    print '    -n    Number of days to get (default 1)'
    print '    -p    EAD basic - password'
    print '    -u    EAD basic - username'

#------------------------------------------------------------------------------
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:n:p:u:h')
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Get any options
    delta_day = 0
    num_days = 1
    username = USERNAME
    password = PASSWORD
    for o, a in opts:
        if o == '-h':
            usage()
            sys.exit()
        if o == '-d':
            delta_day = int(a)
        if o == '-n':
            num_days = int(a)
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
                 datetime.timedelta(delta_day)

    n = 0
    try:
        n = navplot(pdf, FIRS, start_date, num_days, username, password,
                    (DFLT_LATITUDE, DFLT_LONGITUDE, DFLT_WIDTH))
    except NavplotError, err:
        sys.stderr.write(err.value + "\n")

    if n==0:
        sys.stderr.write("Can't get any NOTAMS, check user name and password\n")

if __name__ == '__main__':
    main()
