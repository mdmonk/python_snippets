###############################################################################
## base64Utils.py -- PnPy utility script to encode and decode base64. 
## tested on Python 2.6.1. This utility will take the current selection
## (or document if there is no selection) and create a base 64 encoded document
## It will also take a base 64 encoded document and return the unencoded text.
## -- Note: No verification is done to ensure that the unencoded data is 
## ASCII or valid unicode textual data. 
## By: NickDMax

import pn
import scintilla
from pypn.decorators import script
import base64

@script("Base64Encode", "DocUtils")
def doBase64():
    """ This method will grab the curent selection/document and
        create a new document that is a base64 vesion of the text """
    doc = pn.CurrentDoc()
    if doc is not None:     #Lets try not to crash pn too often...
        editor = scintilla.Scintilla(doc)
        start = editor.SelectionStart
        end = editor.SelectionEnd
        if (start == end):  #nothing is selected so we will just grab it all...
            start = 0
            end = editor.Length 
        text = editor.GetTextRange(start, end)
        newDoc = pn.NewDocument(None)
        newEditor = scintilla.Scintilla(newDoc)
        newEditor.BeginUndoAction()
        encoded = base64.b64encode(text)
        l = len (encoded)
        m = 0
        while l > 80:
            str = encoded[m:m+80] + '\n'
            newEditor.AppendText(len(str), str)
            l, m = l - 80, m + 80
        str = encoded[m:m+l]
        newEditor.AppendText(len(str), str)        
        newEditor.EndUndoAction()
    
@script("DecodeBase64", "DocUtils")
def undoBase64():
    """ This method will grab the curent selection/document and
        create a new document that is the base64 decoded vesion 
        of the text """
    doc = pn.CurrentDoc()
    if doc is not None:     #Lets try not to crash pn too often...
        editor = scintilla.Scintilla(doc)
        start = editor.SelectionStart
        end = editor.SelectionEnd
        if (start == end):  #nothing is selected so we will just grab it all...
            start = 0
            end = editor.Length 
        text = editor.GetTextRange(start, end)
        decoded = base64.b64decode(text)
        newDoc = pn.NewDocument(None)
        newEditor = scintilla.Scintilla(newDoc)
        newEditor.BeginUndoAction()
        newEditor.AppendText(len(decoded), decoded)
        newEditor.EndUndoAction()
