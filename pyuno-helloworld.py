#!/usr/bin/env python

import uno

# get the uno component context from the PyUNO runtime
localContext = uno.getComponentContext()

# create the UnoUrlResolver
resolver = localContext.ServiceManager.createInstanceWithContext( "com.sun.star.bridge.UnoUrlResolver", localContext )

# connect to the running office
ctx = resolver.resolve( "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext" )
smgr = ctx.ServiceManager

# get the central desktop object
desktop = smgr.createInstanceWithContext( "com.sun.star.frame.Desktop",ctx)

# access the current writer document
model = desktop.getCurrentComponent()

# access the document's text property
text = model.Text

# create a cursor
cursor = text.createTextCursor()

# insert the text into the document
text.insertString( cursor, "Hello World", 0 )

# Do a nasty thing before exiting the python process. In case the
# last call is a oneway call (e.g. see idl-spec of insertString),
# it must be forced out of the remote-bridge caches before python
# exits the process. Otherwise, the oneway call may or may not reach
# the target object.
# I do this here by calling a cheap synchronous call (getPropertyValue).
ctx.ServiceManager
