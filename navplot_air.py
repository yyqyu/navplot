#!/usr/bin/env python
#
# Convert airspace data from Tim Newport-Peace format file
#

import math, sys
import getopt

from simpleparse.parser import Parser

import freenav.tnp as tnp

MAX_LEVEL = 7000
NM_TO_M = 1852

# Returns (initial) course from point1 to point2, degrees relative to North
# Return value will be in the range +/- 180 degrees
def course(lat1, lon1, lat2, lon2):
    d1 = math.sin(lon2-lon1)*math.cos(lat2)
    d2 = math.cos(lat1)*math.sin(lat2)-\
         math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1)
    return math.atan2(d1, d2)

# Airspace processor to generate data for navplot
class NavProcessor():
    def add_airspace(self, name, airclass, airtype, base, tops, airlist):
        p = airlist[0]
        if int(base) <= 5000:
            print '# -b'
            if isinstance(p, tnp.Circle):
                radius = p.radius / 60.0
                c = p.centre
                lon_scale = math.cos(c.lat.radians())
                for i in range(101):
                    ang = 2 * math.pi * i / 100.0
                    lat = c.lat.degrees() + radius * math.sin(ang)
                    lon = c.lon.degrees() + radius * math.cos(ang) / lon_scale
                    print '%f\t%f' % (lon, lat)
            else:
                self.add_segments(p.lat, p.lon, airlist[1:])

    def add_segments(self, lat, lon, airlist):
        print '%f\t%f' % (lon.degrees(), lat.degrees())
        if airlist:
            p = airlist[0]

            if isinstance(p, tnp.Arc):
                radius = p.radius / 60.0
                start = course(p.centre.lat.radians(), p.centre.lon.radians(),
                               lat.radians(), lon.radians())
                end = course(p.centre.lat.radians(), p.centre.lon.radians(),
                             p.end.lat.radians(), p.end.lon.radians())
                len = end - start

                # Kludge nasty 360 degree wrap-around problem
                if isinstance(p, tnp.CwArc):
                    if len < 0:
                        len += 2 * math.pi
                else:
                    if len > 0:
                        len -= 2 * math.pi

                # Draw arc using approx 3 degree segments
                n = int(abs(len) / math.radians(3.0))
                lon_scale = math.cos(p.centre.lat.radians())
                for i in range(n):
                    ang = start + i * len / n
                    lat = p.centre.lat.degrees() + radius * math.cos(ang)
                    lon = p.centre.lon.degrees() +\
                          radius * math.sin(ang) / lon_scale
                    print '%f\t%f' % (lon, lat)

                self.add_segments(p.end.lat, p.end.lon, airlist[1:])
            else:
                self.add_segments(p.lat, p.lon, airlist[1:])

def main():
    filename = sys.argv[1]

    parser = Parser(tnp.tnp_decl, 'tnp_file')
    nav_processor = NavProcessor()
    tnp_processor = tnp.TnpProcessor(nav_processor)

    airdata = open(filename).read()
    success, parse_result, next_char = parser.parse(airdata,
                                                    processor=tnp_processor)
    assert success and next_char==len(airdata),\
        "Error - next char is %d" % next_char

if __name__ == '__main__':
    main()
