#!/usr/bin/env python

#
# Gaim Launcher Experiment
# SegPhault - 06/28/2006
#

import aim, gtk

def get_buddies():
  return dict([(b.name.replace(" ", "").lower(), b)
    for b in aim.BuddyList().online_buddies])

class GaimLauncher:
  def __init__(self):
    self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    self.window.connect('destroy', lambda w: gtk.main_quit())

    self.txtBuddy = gtk.Entry()
    comp = gtk.EntryCompletion()
    self.buddyStore = gtk.ListStore(str, str)

    for b in get_buddies().values():
      n = b.alias and "%s (%s)" % (b.alias, b.name) or b.name
      self.buddyStore.append([n, b.name.replace(" ", "").lower()])

    comp.set_match_func(self.on_match)
    comp.set_model(self.buddyStore)
    comp.set_text_column(0)
    comp.connect("match-selected", self.on_complete)

    self.txtBuddy.set_completion(comp)

    self.window.add(self.txtBuddy)
    self.window.show_all()

  def on_match(self, comp, key, iter):
    return self.txtBuddy.get_text().lower() in self.buddyStore[iter][0].lower()

  def on_complete(self, comp, model, iter):
    get_buddies()[model[iter][1]].start_chat()
    gtk.main_quit()

GaimLauncher()
gtk.main()

