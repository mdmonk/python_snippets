#!/usr/bin/env python

"""
  Gaim Deskbar Plug-in
  --------------------
  Created by Ryan Paul (SegPhault) on 05/18/2006

    CONTACT
    -------
      Please direct questions and comments to: segphault@sbcglobal.net

    REQUIREMENTS
    ------------
      This plug-in requires D-Bus and a D-Bus enabled build of Gaim 2.0

    NOTES
    -----
      This plug-in will list all matching Gaim buddies that are currently
      online. Matching is done with both the screen name and the alias.
      It will match buddies from any protocol, not just aim. Clicking on a
      buddy will open a conversation window.

    ISSUES
    ------
      Conversation window doesn't always receive focus after opening
"""

import deskbar, os, xml.dom.minidom
import dbus, dbus.glib, dbus.decorators

from deskbar.Handler import Handler
from deskbar.Match import Match
from gettext import gettext as _

HANDLERS = {
    "GaimHandler": {
      "name": _("Gaim Buddy List"),
      "description": _("Start a conversation with a buddy"),
    }
}

bus = dbus.SessionBus()
obj = bus.get_object("net.sf.gaim.GaimService", "/net/sf/gaim/GaimObject")
gaim = dbus.Interface(obj, "net.sf.gaim.GaimInterface")

BUDDY_LIST_FILE = os.path.expanduser("~/.gaim/blist.xml")

class Buddy:
  def __init__(self, e):
    self.element = e

  def get_name(self):
    if self.element:
      return self.element.getElementsByTagName("name")[0].firstChild.data
    else: return None

  def get_alias(self):
    if self.element and len(self.element.getElementsByTagName("alias")) > 0:
      return self.element.getElementsByTagName("alias")[0].firstChild.data
    else: return ""

  def get_account(self):
    return self.element.getAttribute("account")

  def get_protocol(self):
    return self.element.getAttribute("protocol")

  def get_isonline(self):
    a = gaim.GaimAccountsFindAny(self.account, self.protocol)
    b = gaim.GaimFindBuddy(a, self.name)
    return gaim.GaimBuddyIsOnline(b) == 1

  name = property(get_name, None)
  alias = property(get_alias, None)
  account = property(get_account, None)
  protocol = property(get_protocol, None)
  is_online = property(get_isonline, None)

class GaimMatch(Match):
  def __init__(self, backend, name=None, buddy=None, **args):
    deskbar.Match.Match.__init__(self, backend, **args)
    self.buddy = buddy
    self.name = name

  def action(self, text=None):
    a = gaim.GaimAccountsFindAny(self.buddy.account, self.buddy.protocol)
    c = gaim.GaimConversationNew(1, a, self.name)

  def get_category(self):
    return "people"

  def get_verb(self):
    if self.buddy.alias:
      return _("Send a message to <b>%s (%s)</b>") % (self.name, self.buddy.alias)
    else:
      return _("Send a message to <b>%s</b>") % self.name

  def get_hash(self, text=None):
    return self.name

class GaimHandler(Handler):
  def __init__(self):
    deskbar.Handler.Handler.__init__(self, "/usr/local/share/pixmaps/gaim/status/default/aim.png")

  def query(self, query):
    data = xml.dom.minidom.parse(BUDDY_LIST_FILE).getElementsByTagName("buddy")
    text = query.lower(); results = []

    for buddy in [Buddy(x) for x in data]:
      if buddy.is_online and text in buddy.name.lower() or text in buddy.alias.lower():
        results += [GaimMatch(self, name=buddy.name, buddy=buddy)]

    return results

