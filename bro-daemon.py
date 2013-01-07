#!/opt/local/bin/python

import broccoli
import sqlite3
import random
import sys
import re
import select   # for select loop

# Bro event loop
def bro_event_loop(bro_conn):
   try:
       bro_conn_fd=bro_conn_get_fd(bro_conn)
       while True:
           select.select((bro_conn_fd),(bro_conn_fd),(bro_conn_fd))
           bro_conn.processInput()
   except:
       while True:
           bro_conn.processInput()
           sleep(.1)

@broccoli.event

def remote_check_URL(seqno, host, uri):
   # Receive a URL from bro, and send a return signal back
   #  if it should be blocked.
   category = check_database(host,uri)
   if category:
       if check_category(category):
           # If the category signals a block
           bro_conn.send("stomper_block",seqno)
   return

#Main program - Initialize and call event loop
# Setup the connection to bro
bro_conn = broccoli.Connection("127.0.0.1:47758")

# Event loop
bro_event_loop(bro_conn)
# Everything under this is never executed.

sys.exit(0)
