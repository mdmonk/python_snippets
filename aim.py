#!/usr/bin/env python
#
# DBus Gaim Library
# SegPhault - 05/18/2006
#

import os, xml.dom.minidom
import dbus, dbus.glib, dbus.decorators

bus = dbus.SessionBus()
obj = bus.get_object("net.sf.gaim.GaimService", "/net/sf/gaim/GaimObject")
gaim = dbus.Interface(obj, "net.sf.gaim.GaimInterface")
notify_obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
notify = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

BUDDY_LIST_FILE = os.path.expanduser("~/.gaim/blist.xml")

class Buddy:
  def __init__(self, e):
    self.element = e

  def get_name(self):
    if self.element:
      return self.element.getElementsByTagName("name")[0].firstChild.data
    else: return None

  def __repr__(self):
    return "<Buddy '%s'>" % self.name

  def get_alias(self):
    if self.element and len(self.element.getElementsByTagName("alias")) > 0:
      return self.element.getElementsByTagName("alias")[0].firstChild.data
    else: return ""

  def get_account_name(self):
    return self.element.getAttribute("account")

  def get_account(self):
    return gaim.GaimAccountsFindAny(self.account_name, self.protocol)

  def get_protocol(self):
    return self.element.getAttribute("protocol")

  def get_isonline(self):
    b = gaim.GaimFindBuddy(self.account, self.name)
    return gaim.GaimBuddyIsOnline(b) == 1

  def start_chat(self):
    c = gaim.GaimConversationNew(1, self.account, self.name)

  name = property(get_name, None)
  alias = property(get_alias, None)
  account_name = property(get_account_name, None)
  account = property(get_account, None)
  protocol = property(get_protocol, None)
  is_online = property(get_isonline, None)

class Group:
  def __init__(self, e):
    self.element = e

  def get_name(self):
    return self.element.getAttribute("name")

  def __repr__(self):
    return "<Group '%s'>" % self.name

  def get_buddies(self):
    b = self.element.getElementsByTagName("buddy")
    return [Buddy(x) for x in b]

  name = property(get_name, None)
  buddies = property(get_buddies, None)

class BuddyList:
  def __init__(self, f = BUDDY_LIST_FILE):
    self.buddy_data = xml.dom.minidom.parse(f)

  def get_groups(self):
    g = self.buddy_data.getElementsByTagName("group")
    return [Group(x) for x in g]

  def get_online_buddies(self):
    for group in self.groups:
      for buddy in group.buddies:
        if buddy.is_online:
          yield buddy

  groups = property(get_groups, None)
  online_buddies = property(get_online_buddies, None)

if __name__ == '__main__':
  for buddy in BuddyList().online_buddies:
    print buddy.name

