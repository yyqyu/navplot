# -*- coding: iso-8859-1
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

import os
import tempfile
import time
import string
import sys
import urllib2
import wx
import wx.lib.hyperlink
import navplot

SECS_IN_DAY = 24*60*60

#------------------------------------------------------------------------------
# A simple non-modal message dialog
class MsgDialog(wx.Dialog):
    def __init__(self, parent, msg, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        pre = wx.PreDialog()
        pre.Create(parent, -1, title, pos, size, style)
        self.PostCreate(pre)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label=msg)
        sizer.Add(label, 0, wx.ALL, 15)

        self.SetSizer(sizer)
        sizer.Fit(self)

#------------------------------------------------------------------------------
# AIS login details and map drawing stuff
class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.config = wx.Config('Freeflight')
        self.config.SetPath('NavPlot')

        border = wx.BoxSizer(wx.HORIZONTAL)

        self.lat_ctrl = wx.TextCtrl(self, size=(75, -1))
        self.lon_ctrl = wx.TextCtrl(self, size=(75, -1))
        self.width_ctrl = wx.TextCtrl(self, size=(75, -1))
        mapsizer = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        mapsizer.Add(
            wx.StaticText(self, label='Latitude'), 0, wx.ALIGN_CENTER_VERTICAL)
        mapsizer.Add(self.lat_ctrl, 0, wx.LEFT, 4)
        mapsizer.Add(
            wx.StaticText(self, label='Longitude'), 0, wx.ALIGN_CENTER_VERTICAL)
        mapsizer.Add(self.lon_ctrl, 0, wx.LEFT, 4)
        mapsizer.Add(
            wx.StaticText(self, label='Width'), 0, wx.ALIGN_CENTER_VERTICAL)
        mapsizer.Add(self.width_ctrl, 0, wx.LEFT, 4)

        mapbox = wx.StaticBox(self, label='Map Coordinates')
        mapboxsizer = wx.StaticBoxSizer(mapbox, wx.VERTICAL)
        mapboxsizer.Add(mapsizer, 0, wx.ALL, 8)
        border.Add(mapboxsizer, 0, wx.ALL, 4)

        self.user_ctrl = wx.TextCtrl(self)
        self.pwd_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        aissizer = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        aissizer.Add(
            wx.StaticText(self, label='Username'), 0, wx.ALIGN_CENTER_VERTICAL)
        aissizer.Add(self.user_ctrl, 0, wx.LEFT, 4)
        aissizer.Add(
            wx.StaticText(self, label='Password'), 0, wx.ALIGN_CENTER_VERTICAL)
        aissizer.Add(self.pwd_ctrl, 0, wx.LEFT, 4)

        aisbox = wx.StaticBox(self, label='AIS Login')
        aisboxsizer = wx.StaticBoxSizer(aisbox, wx.VERTICAL)
        aisboxsizer.Add(aissizer, 0, wx.ALL, 8)

        resetbutton = wx.Button(self, label='Reset')
        self.Bind(wx.EVT_BUTTON, self.on_reset, resetbutton)
        savebutton = wx.Button(self, label='Save Settings')
        self.Bind(wx.EVT_BUTTON, self.on_save, savebutton)
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(resetbutton, 0, wx.ALIGN_LEFT)
        buttonsizer.Add(savebutton, 0, wx.LEFT|wx.ALIGN_RIGHT, 8)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(aisboxsizer)
        sizer.Add(buttonsizer, 0, wx.ALL|wx.ALIGN_RIGHT, 8)
        border.Add(sizer, 0, wx.ALL, 4)

        self.SetAutoLayout(True)
        self.SetSizer(border)

        self.load_config()

    def on_save(self, event):
        self.get_values()
        self.config.Write('AIS Username', self.user)
        self.config.Write('AIS Password', self.password)
        self.config.WriteFloat('Longitude', self.longitude)
        self.config.WriteFloat('Latitude', self.latitude)
        self.config.WriteFloat('Map Width', self.width)

    def on_reset(self, event):
        self.load_config()

    def load_config(self):
        self.user = self.config.Read('AIS Username')
        self.password = self.config.Read('AIS Password')
        self.latitude = self.config.ReadFloat('Latitude', navplot.DFLT_LATITUDE)
        self.longitude = self.config.ReadFloat('Longitude',
                                               navplot.DFLT_LONGITUDE)
        self.width = self.config.ReadFloat('Map Width', navplot.DFLT_WIDTH)
        self.set_values()

    def get_values(self):
        self.user = self.user_ctrl.GetValue()
        self.password = self.pwd_ctrl.GetValue()
        self.latitude = float(self.lat_ctrl.GetValue())
        self.longitude = float(self.lon_ctrl.GetValue())
        self.width = abs(float(self.width_ctrl.GetValue()))
        return self.user, self.password,\
               (self.latitude, self.longitude, self.width)

    def set_values(self):
        self.user_ctrl.SetValue(self.user)
        self.pwd_ctrl.SetValue(self.password)
        self.lat_ctrl.SetValue(str(self.latitude))
        self.lon_ctrl.SetValue(str(self.longitude))
        self.width_ctrl.SetValue(str(self.width))

#------------------------------------------------------------------------------
# NOTAM FIR(s) and dates
class NotamPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.time = time.time()
        border = wx.BoxSizer(wx.VERTICAL)

        days = [time.strftime('%A', time.localtime(self.time+d*SECS_IN_DAY))
                for d in range(7)]
        days[0] = 'Today'
        days[1] = 'Tomorrow'
        self.datechoice = wx.Choice(self, choices=days)
        self.datechoice.SetSelection(0)
        self.dayschoice = wx.Choice(self, choices=['1', '2', '3'])
        self.dayschoice.SetSelection(0)
        self.firchoice = wx.Choice(self, choices=['London', 'Scottish', 'Both'])
        self.firchoice.SetSelection(0)

        ctrlsizer = wx.FlexGridSizer(cols=4, hgap=8, vgap=10)
        ctrlsizer.Add(wx.StaticText(self, label='Date'),
                  0, wx.ALIGN_CENTER_VERTICAL)
        ctrlsizer.Add(self.datechoice)
        ctrlsizer.Add(wx.StaticText(self, label='FIR'), 0,
                  wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 8)
        ctrlsizer.Add(self.firchoice)
        ctrlsizer.Add(wx.StaticText(self, label='Number of Days'),
                  0, wx.ALIGN_CENTER_VERTICAL)
        ctrlsizer.Add(self.dayschoice)

        box = wx.StaticBox(self, label='Briefing Details')
        boxsizer = wx.StaticBoxSizer(box)
        boxsizer.Add(ctrlsizer, 0, wx.RIGHT|wx.LEFT|wx.BOTTOM, 8)
        border.Add(boxsizer, 1, wx.ALL|wx.EXPAND, 4)

        text = wx.StaticText(self, label=
            'Displays Navigation Warnings from UK AIS site at www.ais.org.uk\n'
            'Requires an AIS account and a PDF reader to view the results')
        border.Add(text, 0, wx.ALL, 8)

        self.SetAutoLayout(True)
        self.SetSizer(border)

    def get_values(self):
        date = self.time + self.datechoice.GetSelection()*SECS_IN_DAY
        days = self.dayschoice.GetSelection()
        fir = self.firchoice.GetSelection()

        firs = (('EGTT', ''), ('EGPX', ''), ('EGTT', 'EGPX'))[fir]
        return (firs, date, days)

#------------------------------------------------------------------------------
# Program information
class AboutPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        border = wx.BoxSizer(wx.VERTICAL)
        space = wx.BoxSizer(wx.VERTICAL)

        t = wx.StaticText(self, label=
            'NavPlot Version 0.3.2, Copyright � 2005-7 Alan Sparrow')
        border.Add(t)
        t = wx.StaticText(self, label=
            'NavPlot comes with ABSOLUTELY NO WARRANTY. This is\n'
            'free software, and you are welcome to redistribute it under\n'
            'certain conditions; See the gpl.txt file for more details')
        border.Add(t, 0, wx.TOP, 4)
        t = wx.StaticText(self, label=
            'See www.freeflight.org.uk for more information on the program')
        border.Add(t, 0, wx.TOP, 16)
        h = wx.lib.hyperlink.HyperLinkCtrl(self, wx.ID_ANY,
            'Or you can send me an e-mail',
            URL='mailto:navplot@freeflight.org.uk')
        border.Add(h)
        space.Add(border, 0, wx.ALL, 16)

        self.SetAutoLayout(True)
        self.SetSizer(space)

#------------------------------------------------------------------------------
class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        nb = wx.Notebook(self)
        self.notam_panel = NotamPanel(nb)
        self.settings_panel= SettingsPanel(nb)
        self.about_panel = AboutPanel(nb)
        nb.AddPage(self.notam_panel, 'NOTAM')
        nb.AddPage(self.settings_panel, 'Settings')
        nb.AddPage(self.about_panel, 'About')

        notam_button = wx.Button(self, label='Get NOTAMS')
        notam_button.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.on_click, notam_button)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(notam_button, 0, wx.RIGHT, 3)

        sizer = wx.FlexGridSizer(cols=1, vgap=5)
        sizer.Add(nb, 0, wx.LEFT|wx.RIGHT, 4)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 4)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def on_click(self, event):
        firs, start, ndays = self.notam_panel.get_values()
        user, pwd, mapinfo = self.settings_panel.get_values()
        end = start + ndays*SECS_IN_DAY

        dir = tempfile.gettempdir()
        filename = self.make_tmpfile(dir)

        msg = MsgDialog(self.GetParent(),
            'Dowloading NOTAMS from www.ais.org.uk\n'
            'This may take half a minute or more. Please be patient...',
            'NOTAM Download')
        msg.Show(True)
        wx.BeginBusyCursor()
        wx.SafeYield()
        try:
            n = navplot.navplot(filename, firs, time.localtime(start),
                                time.localtime(end), user, pwd, mapinfo)
        finally:
            msg.Destroy()
            wx.EndBusyCursor()
            wx.SafeYield()

        if n>0:
            os.startfile(filename)
        else:
            if n==0:
                msg = 'Error downloading NOTAMS.\n'\
                      'Check your username and password settings'
            else:
                msg = 'Error parsing NOTAMS. Try again or download manually\n'\
                      'from http://www.nats.co.uk/operational/pibs/index.shtml'
            m = wx.MessageDialog(self, msg, 'Error', wx.OK|wx.ICON_ERROR)
            m.ShowModal()

    def make_tmpfile(self, dir, num=0):
        if num:
            filename = os.path.join(dir, 'navplot-'+str(num)+'.pdf')
        else:
            filename = os.path.join(dir, 'navplot.pdf')

        if os.path.exists(filename):
            try:
                os.unlink(filename)
            except OSError:
                filename = self.make_tmpfile(dir, num+1)

        return filename

#------------------------------------------------------------------------------
class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title,
            style = wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)

        self.SetIcon(wx.Icon('navplot.ico', wx.BITMAP_TYPE_ICO))

        panel = MainPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel)
        self.SetSizer(sizer)
        self.Fit()

#------------------------------------------------------------------------------
class NotamApp(wx.App):
    def OnInit(self):
        self.frame=MainWindow(None, 'NavPlot')
        self.frame.Show()

        sys.excepthook = self.excepthook
        return True

    def excepthook(self, type, value, tb):
        if type == ValueError:
            msg = 'Error parsing the map coordinate settings.\n'\
                  'Reset the values or check they are valid numbers'
        elif type == urllib2.URLError:
            msg = 'Unable to connect to the AIS website'
        else:
            import traceback
            msg = ''
            for m in traceback.format_exception(type, value, tb):
                msg += m

        d = wx.MessageDialog(self.frame, msg, 'Error', wx.OK|wx.ICON_ERROR)
        d.ShowModal()

if __name__ == '__main__':
    app = NotamApp(redirect=0)
    app.MainLoop()