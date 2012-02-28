#!/usr/bin/env python
#
# NavPlot - Download NOTAMs from www.ais.org.uk and generate PDF viewer file.
# Copyright (C) 2008  Alan Sparrow
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

import BeautifulSoup
import datetime
import mechanize
import optparse
import re
import sys
import time
import notamdoc

LOGIN_URL = "http://www.nats-uk.ead-it.com/fwf-natsuk/public/user/account/login.faces"
COPYRIGHT_HOLDER = 'NATS Ltd'

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
QGroupRe = re.compile(r'^Q\) '
    r'(?P<fir>[A-Z]+)/'
    r'(?P<qcode>Q[A-Z]+)/'
    r'(?P<traffic>[IV]+)/'
    r'(?P<purpose>[NBOM]+)/'
    r'(?P<scope>[AEW]+)/'
    r'(?P<lower>\d+)/'
    r'(?P<upper>\d+)/'
    r'(?P<centre>\d{4}[NS]\d{5}[EW])(?P<radius>\d{3})[ ]*')

#------------------------------------------------------------------------------
# Extract NOTAM data from the HTML soup
def parse_notam_soup(soup):
    # Find all the Q-codes
    notam_dict = {}
    for q in soup.findAll(text=QGroupRe):
        # Q code is in tr->td->div
        notam_row = q.parent.parent.parent

        # Get NOTAM id from adjancent cell to the NOTAM
        id = notam_row.find('td', {"class": "right"}).string

        n_dict = QGroupRe.match(q.string).groupdict()
        notam = q.parent.parent
        n_dict["text"] = '\n'.join([n.string for n in notam.findAll()])

        notam_dict[id] = n_dict

    return notam_dict.values()

#-----------------------------------------------------------------------------
# Get NOTAMS from AIS website & make PDF document
def navplot(filename, firs, start_date, num_days, username, password, mapinfo):
    # Calculate dates
    if start_date == datetime.date.today():
        utc = datetime.datetime.utcnow()
        start_hour = utc.hour
        start_min = utc.minute
    else:
        start_hour = 0
        start_min = 0
    end_date = start_date + datetime.timedelta(days=num_days-1)

    # Create browser, get login page and login
    br = mechanize.Browser()
    br.open(LOGIN_URL)
    br.select_form(name="mainForm")
    br["j_username"] = username
    br["j_password"] = password
    br.submit()

    # Get area brief request page
    br.select_form(name="menuView:menuForm")
    br.form.find_control("menuView:menuForm:_idcl").readonly = False
    br["menuView:menuForm:_idcl"] = "menuView:menuForm:notam_area"
    br.submit()

    # Get area brief
    br.select_form(name="mainForm")
    br["mainForm:startValidityDay"]    = [str(start_date.day)]
    br["mainForm:startValidityMonth"]  = [str(start_date.month-1)]
    br["mainForm:startValidityYear"]   = [str(start_date.year)]
    br["mainForm:startValidityHour"]   = [str(start_hour)]
    br["mainForm:startValidityMinute"] = [str(start_min)]
    br["mainForm:endValidityDay"]      = [str(end_date.day)]
    br["mainForm:endValidityMonth"]    = [str(end_date.month-1)]
    br["mainForm:endValidityYear"]     = [str(end_date.year)]
    br["mainForm:endValidityHour"]     = ["23"]
    br["mainForm:endValidityMinute"]   = ["59"]
    br["mainForm:traffic"]             = ["V"]
    br["mainForm:lowerFL"]             = "000"
    br["mainForm:upperFL"]             = "100"
    for i, fir in enumerate(firs):
        br["mainForm:fir_%d" % i] = fir
    response = br.submit()

    # Create soup from response and then parse for NOTAMs
    notam_soup = BeautifulSoup.BeautifulSoup(response.read())
    notams = parse_notam_soup(notam_soup)

    # Get the header text
    div = notam_soup.find("div", {"id": "mainColContent"})
    hdr = '\n'.join([' '.join([x.string.strip() for x in l(text=True)])
                     for l in div('li')])

    # Create PDF document
    notamdoc.notamdoc(notams, hdr, firs, start_date, num_days,
                      filename, mapinfo, COPYRIGHT_HOLDER)

#------------------------------------------------------------------------------
def main():
    usage = "usage: %prog [options] pdf_filename"
    parser = optparse.OptionParser(usage)
    parser.set_defaults(delta_day=0, num_days=1, username=USERNAME,
                        password=PASSWORD)
    parser.add_option("-d", dest="delta_day", type="int",
                      help="Days offset from today (default 0)")
    parser.add_option("-n", dest="num_days", type="int",
                      help="Number of days (default 1)")
    parser.add_option("-p", dest="password", help="AIS password")
    parser.add_option("-u", dest="username", help="AIS username")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(2)
    pdf_filename = args[0]

    # Use with UTC times/dates
    start_date = datetime.datetime.utcnow().date() +\
                 datetime.timedelta(options.delta_day)

    navplot(pdf_filename, FIRS, start_date, options.num_days, options.username,
            options.password, (DFLT_LATITUDE, DFLT_LONGITUDE, DFLT_WIDTH))

if __name__ == '__main__':
    main()
