try:
    import something
except ImportError:            # `something' not available
  ## ...code to do without, degrading gracefully...
else:                          # `something' IS available, hooray!
  ## ...code to run only when something is there...
# and then, go on with the rest of your program
## ...code able to run with or w/o `something'...
