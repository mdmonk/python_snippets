#!/usr/bin/env python

"""
  Pidgin Deskbar Plug-in
  --------------------
  Created by Ryan Paul (SegPhault) on 05/18/2006

    CONTACT
    -------
      Please direct questions and comments to: segphault@arstechnica.com

    REQUIREMENTS
    ------------
      This plug-in requires D-Bus and a D-Bus enabled build of Pidgin 2.0

    NOTES
    -----
      This plug-in will list all matching Pidgin buddies that are currently
      online. Matching is done with both the screen name and the alias.
      It will match buddies from any protocol, not just aim. Clicking on a
      buddy will open a conversation window.

    ISSUES
    ------
      Conversation window doesn't always receive focus after opening

    CHANGES
    -------
      01/11/2007 - Don't crash if Pidgin isn't open (Siva Chandran)
      01/11/2007 - Consistently show online buddies only (Siva Chandran)
      05/03/2007 - Updated to work with Pidgin 2.0 (Ryan Paul)
"""

import deskbar, os, xml.dom.minidom
import dbus, dbus.glib, dbus.decorators

from deskbar.Handler import Handler
from deskbar.Match import Match
from gettext import gettext as _

HANDLERS = {
    "PidginHandler": {
      "name": _("Pidgin Buddy List"),
      "description": _("Start a conversation with a buddy"),
    }
}

bus = dbus.SessionBus()
obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
pidgin = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")

BUDDY_LIST_FILE = os.path.expanduser("~/.purple/blist.xml")

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
    try:
      a = pidgin.PurpleAccountsFindAny(self.account, self.protocol)
      b = pidgin.PurpleFindBuddy(a, self.name)
      return pidgin.PurpleBuddyIsOnline(b) == 1
    except:
      return False

  name = property(get_name, None)
  alias = property(get_alias, None)
  account = property(get_account, None)
  protocol = property(get_protocol, None)
  is_online = property(get_isonline, None)

class PidginMatch(Match):
  def __init__(self, backend, name=None, buddy=None, **args):
    deskbar.Match.Match.__init__(self, backend, **args)
    self.buddy = buddy
    self.name = name

  def action(self, text=None):
    a = pidgin.PurpleAccountsFindAny(self.buddy.account, self.buddy.protocol)
    c = pidgin.PurpleConversationNew(1, a, self.name)

  def get_category(self):
    return "people"

  def get_verb(self):
    if self.buddy.alias:
      return _("Send a message to <b>%s (%s)</b>") % (self.name, self.buddy.alias)
    else:
      return _("Send a message to <b>%s</b>") % self.name

  def get_hash(self, text=None):
    return self.name

class PidginHandler(Handler):
  def __init__(self):
    deskbar.Handler.Handler.__init__(self, "/usr/share/pixmaps/pidgin/status/default/aim.png")

  def query(self, query):
    data = xml.dom.minidom.parse(BUDDY_LIST_FILE).getElementsByTagName("buddy")
    text = query.lower(); results = []

    for buddy in [Buddy(x) for x in data]:
      if buddy.is_online and (text in buddy.name.lower() or text in buddy.alias.lower()):
        results += [PidginMatch(self, name=buddy.name, buddy=buddy)]

    return results
