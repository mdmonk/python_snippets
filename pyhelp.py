'''
Context sensitive python help in VIM
(C)opyright 2001 jason petrone <jp_py@jsnp.net>
All Rights Reserved

This script will lookup the __doc__ or __dict__ field for builtins, modules and
module members.  It does not perform any parsing of the current buffer, and
cannot do anything useful for variables.  

I appreciate any feedback you might have!  Please email me if you have any
problems or ideas.  

TO INSTALL:
0) Make sure you have vim compiled with python support
1) Copy this file into a directory like /home/jason/.vim or c:\vim. 
2) Add the following lines to your vimrc or gvimrc:
    py import sys,os; sys.path.append('/home/jason/.vim')
    py import pyhelp
    au Syntax python map <F2> :py pyhelp.lookup()<CR>

TO USE:
In command mode, hit the <F2> key above the term you want to look up.  You
can use it on builtins like 'apply', and 'len', modules that the script you
are editing import(like 'string' or 're'), and also the members of imported
modules(like 'string.join' or 'StringIO.StringIO'). 

PROBLEMS:
wxPython crashes VIM for me, so I skip it when importing.  If other modules
do the same for you, add them to the 'skipimport' list below.  If you are
brave and want to try with wxPython, you can remove it from the list. 
Unfortunatly this fix does not work if you import a module which imports
wxPython.
'''
skipimport = ['wxPython']

#############################################################################
import vim, types, string

__version__ = '0.1'

delimiters = [' ', '\t', '(', ')', ',', ':']

def getWordAtCursor():
  win = vim.current.window
  buf = vim.current.buffer
  (row, col) = win.cursor

  line = buf[row-1]
  if len(line) <= 2: return ''
  word = ''
  front = col - 1
  while 1:
    if front < 0 or line[front] in delimiters: break
    word = line[front] + word
    front -= 1
  back = col
  while 1:
    if back >= len(line) or line[back] in delimiters+['.']: break
    word = word + line[back]
    back += 1
  if len(word) > 0 and word[len(word)-1] == '.': word = word[:len(word)-1]
  return word

def buildNamespace():
  import sys, __main__
  buf = vim.current.buffer
  # make sure to get all imports
  for line in buf:
    line = line.strip()
    if line.startswith('import') or line.startswith('from'):
      try: 
        for s in skipimport: 
          if line.find(s) >= 0: raise 'Dont import!'
        exec(line)
      except: pass
  namespace = sys.modules.copy()
  namespace.update(__main__.__dict__)
  return namespace

def parseDict(dict):
  functions = []
  variables = []
  methods = []
  classes = []
  modules = []
  for key in dict.keys():
    if type(dict[key]) == types.FunctionType: functions.append(key)
    if type(dict[key]) == types.BuiltinFunctionType: functions.append(key)
    if type(dict[key]) == types.BuiltinMethodType: methods.append(key)
    if type(dict[key]) == types.MethodType: methods.append(key)
    elif type(dict[key]) == types.ClassType: classes.append(key)
    elif type(dict[key]) == types.ModuleType: modules.append(key)
    else: variables.append(key)
  return functions, variables, classes, methods, modules

def getHelp(word):
  namespace = buildNamespace()
  try: 
    obj =  eval(word, namespace)
  except: 
    try: obj = eval('__builtins__.'+word, namespace)
    except: return None
  if hasattr(obj, '__doc__') and obj.__doc__: 
    return obj.__doc__
  else: 
    func, var, classes, meths, mods = parseDict(obj.__dict__)
    txt = '"'+ word + '" is a '+type(obj).__name__
    if len(func) > 0: txt+= '\n   functions: ' + string.join(func, ', ')
    if len(classes) > 0: txt+= '\n   classes: ' + string.join(classes, ', ')
    if len(meths) > 0: txt+= '\n   methods: ' + string.join(meths, ', ')
    if len(mods) > 0: txt+= '\n   modules: ' + string.join(mods, ', ')
    if len(var) > 0: txt+= '\n   variables: ' + string.join(var, ', ')
    return txt

def lookup():
  word = getWordAtCursor()
  help = getHelp(word)
  if not help: print 'No help available for "' + word + '"'
  else: print help
