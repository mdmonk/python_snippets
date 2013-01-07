#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import os
import sys
import gtk
import pynotify
from configobj import ConfigObj
from hashlib import md5
from time import time
from math import floor

ICON = [ "22 22 33 1", " 	g #000000", ".	g #A5A5A5", "+	g #9C9C9C", "@	g #949494", "#	g #848484",
         "$	g #7B7B7B", "%	g #737373", "&	g #6B6B6B", "*	g #F7F7F7", "=	g #FFFFFF", "-	g #D6D6D6",
         ";	g #EFEFEF", ">	g #BDBDBD", ",	g #CECECE", "'	g #8C8C8C", ")	g #E6E6E6", "!	g #5A5A5A",
         "~	g #525252", "{	g #DEDEDE", "]	g #636363", "^	g #B5B5B5", "/	g #C5C5C5", "(	g #4A4A4A",
         "_	g #ADADAD", ":	g #3A3A3A", "<	g #424242", "[	g #191919", "}	g #292929", "|	g #101010",
         "1	g #000000", "2	g #080808", "3	g #313131", "4	g #212121",
         "......................", "++++++++++++++++++++++", "@@@@@@@@@@@@@@@@@@@@@@",
         "######################", "$$$$$$$$$$$$$$$$$$$$$$", "%%%%%%%&@*=-%;===>,=;'",
         "#',$.>&')@$.;$#;#%-'#-", "+-@*.,+>@!!~{#];&~,^/>", "@.({]$_>@((()$!;!(/+#]",
         "'+:{!%_&*~<#,!(;~:/&<<", ":][@(~'~-{_^,(<_<}$<|1", "121111|{{-+++}11111111",
         "111111</,/'++211111111", "1111112+_<^^^|11111111", "1111111@[1'(^:11111111",
         "1111113$11%:~_11111111", "111111&(11&(2>41111111", "111111]211]!1|11111111",
         "11111111113:1111111111", "2222222222222222222222", "2222222222222222222222",
         "||||||||||||||||||||||" ]

class TrayIcon(wx.TaskBarIcon):
    def __init__(self, parent):
        self.parent = parent
        super(TrayIcon, self).__init__()
        iconres = wx.IconFromXPMData(ICON)
        self.SetIcon( iconres, "mOTPGen" )
        self.Bind( wx.EVT_TASKBAR_LEFT_UP, self.parent.OnCreateToken )

    def CreatePopupMenu(self):
        title = ""
        token = self.parent.getToken()
        if token:
            title = "Current: " + token
        menu = wx.Menu(title)
        menuSetSecret = menu.AppendCheckItem(wx.ID_ANY, "Set &Secret")
        menuSetPin    = menu.AppendCheckItem(wx.ID_ANY, "Set &PIN")
        if len( self.parent.cfg["Secret"] ) == 32:
            menuSetSecret.Check()

        if self.parent.cfg["PIN"] != "":
            menuSetPin.Check()

        menu.AppendSeparator()
        menu.Append(wx.ID_ABOUT)
        menu.Append(wx.ID_EXIT)
        self.Bind( wx.EVT_MENU, self.parent.OnSetSecret, menuSetSecret )
        self.Bind( wx.EVT_MENU, self.parent.OnSetPin, menuSetPin )
        self.Bind( wx.EVT_MENU, self.parent.OnAbout, id=wx.ID_ABOUT )
        self.Bind( wx.EVT_MENU, self.parent.OnExit, id=wx.ID_EXIT )
        return menu

class TaskBarApp(wx.Frame):
    def __init__(self, parent, id, title):
        # Fetch user's homedir (non-Win32) or Roaming Profile dir (Win32)
        try:
            from win32com.shell import shellcon, shell
            homedir = shell.SHGetFolderPath( 0, shellcon.CSIDL_APPDATA, 0, 0 )
        except:
            homedir = os.path.expanduser("~")

        self.cfgfile = homedir + "/.mOTPgen.conf"
        self.cfg = ConfigObj( self.cfgfile )
        if not "Secret" in self.cfg:
            self.cfg["Secret"] = ""
        if not "PIN" in self.cfg:
            self.cfg["PIN"] = ""

        if len( self.cfg["Secret"] ) != 32 or self.cfg["PIN"] == "":
            self.Notify( "Mobile OTP Generator", "Set Secret and/or PIN first! Right-click on icon in tray." )

        wx.Frame.__init__(self, parent, -1, title, size = (1, 1),
            style=wx.FRAME_NO_TASKBAR|wx.NO_FULL_REPAINT_ON_RESIZE)

        self.tbicon = TrayIcon(self)
        self.Show(True)

    def Notify(self, title, message):
        global ICON
        try:
            if pynotify.init("Mobile OTP Generator"):
                n = pynotify.Notification(title, message)
                n.set_timeout( 2 )
                n.set_urgency( pynotify.URGENCY_LOW )
                n.set_icon_from_pixbuf( gtk.gdk.pixbuf_new_from_xpm_data( ICON ) )
                n.show()
        except:
            pass

    def getToken(self):
        if len( self.cfg["Secret"] ) != 32:
            return False
        now = time()
        now = int( floor( now / 10 ) )
        now = str(now)
        full = now + self.cfg["Secret"] + self.cfg["PIN"]
        m = md5()
        m.update( full )
        mhex = m.hexdigest()
        return mhex[:6]

    def OnCreateToken(self, event):
        token = self.getToken()
        if token == False:
            self.Notify( "Set Secret first!", "Right-click tray icon and set Secret" )
            return False
        clipmsg = ""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData( wx.TextDataObject( token ) )
            wx.TheClipboard.Close()
            clipmsg = "The token has been copied into the Clipboard."
        if self.cfg["PIN"] == "":
            clipmsg += " (No PIN set!)"
        self.Notify( "Token: " + token, clipmsg )

    def OnSetSecret(self, event):
        preset = self.cfg["Secret"]
        dlg = wx.TextEntryDialog(self, "Please enter the secret:", "Enter Secret", preset)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.cfg["Secret"] = dlg.GetValue()
            self.Notify( "SECRET set", "Generate token by left-clicking tray icon" )

    def OnSetPin(self, event):
        preset = ""
        if self.cfg["PIN"] != "####":
            preset = self.cfg["PIN"]
        dlg = wx.PasswordEntryDialog(self, "Please enter the PIN:", "Enter PIN", preset)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.cfg["PIN"] = dlg.GetValue()
            self.Notify( "PIN set", "Generate token by left-clicking tray icon" )

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "Python Mobile OTP Generator 1.0\n" +
                                     "©2010 by Markus Birth <markus@birth-online.de>\n\n"+
                                     "http://wiki.birth-online.de/software/python/motp-token-generator\n\n"+
                                     "Configuration file: "+self.cfgfile, "About...", wx.OK|wx.ICON_INFORMATION )
        dlg.ShowModal()

    def OnExit(self, event):
        self.cfg.write()
        sys.exit()


class MOTPGen(wx.App):
    def OnInit(self):
        frame = TaskBarApp(None, -1, ' ')
        frame.Center(wx.BOTH)
        frame.Show(False)
        return True

def _main(argv=None):
    if argv is None:
        argv = sys.argv
    app = MOTPGen(0)
    app.MainLoop()

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    _main()
