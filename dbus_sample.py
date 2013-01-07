#!/usr/bin/env python

import dbus, dbus.glib, dbus.decorators
import gtk, gobject

bus = dbus.SessionBus()

obj = bus.get_object("org.gaim.GaimService", "/org/gaim/GaimObject")
gaim = dbus.Interface(obj, "org.gaim.GaimInterface")

notify_obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
notify = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

rhythm_obj = bus.get_object("org.gnome.Rhythmbox", "/org/gnome/Rhythmbox/Player")
rhythm = dbus.Interface(rhythm_obj, "org.gnome.Rhythmbox.Player")

rhythm_shell_obj = bus.get_object("org.gnome.Rhythmbox", "/org/gnome/Rhythmbox/Shell")
rhythm_shell = dbus.Interface(rhythm_shell_obj, "org.gnome.Rhythmbox.Shell")

buddy_data_cache = {}

def onSongChanged(songUri):
  text = '<b>%(title)s</b> by <a href="http://www.last.fm/music/%(artist)s">%(artist)s</a>\
    from <a href="http://www.last.fm/music/%(artist)s/%(album)s">%(album)s</a>' %
      rhythm_shell.getSongProperties(songUri)

  nId = notify.Notify("DBus Test", 0, "gtk-cdrom", "Now Playing", text, ["skip", "Skip"], {}, 9000)

def onSignOn(bId):
  buddyAlias, buddyName = gaim.GaimBuddyGetAlias(bId), gaim.GaimBuddyGetName(bId)

  text = buddyAlias == buddyName and \
    "<b>%s</b> is now online." % buddyName or \
    "<b>%s</b> <i>(%s)</i> is now online." % (buddyAlias, buddyName)

  nId = notify.Notify("DBus Test", 0, "gtk-connect", "Buddy Signed On", text,
      ["message", "Send Message"], {}, 9000)

  buddy_data_cache[nId] = (gaim.GaimBuddyGetAccount(bId), buddyName)

def onNewMail(msgLoc):
  notify.Notify("DBus Test", 0, "gtk-dialog-info",
      "New Mail", "New message received in: <b>%s</b>" % msgLoc, [], {}, 9000)

def onNotifyClose(nId):
  if buddy_data_cache.has(nId):
    del buddy_data_cache[nId]

def onNotifyAction(nId, actKey):
  if actKey == "message":
    gaim.GaimConversationNew(1, *buddy_data_cache[nId])
  elif actKey == "skip":
    rhythm.next()
  else:
    print "%s, %s" % (msgId, actKey)

bus.add_signal_receiver(onNewMail, "Newmail", "org.gnome.evolution.mail.dbus.Signal", None, "/org/gnome/evolution/mail/newmail")
bus.add_signal_receiver(onSignOn, dbus_interface="org.gaim.GaimInterface", signal_name = "BuddySignedOn")
bus.add_signal_receiver(onSongChanged, dbus_interface="org.gnome.Rhythmbox.Player", signal_name="playingUriChanged")
bus.add_signal_receiver(onNotifyAction, dbus_interface="org.freedesktop.Notifications", signal_name="ActionInvoked")
bus.add_signal_receiver(onNotifyClose, dbus_interface="org.freedesktop.Notifications", signal_name="CloseNotification")

gtk.main()

