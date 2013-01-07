# -*- coding: utf-8 -*-
'''
File:          db_row.py

Authors:       Kevin Jacobs (jacobs@theopalgroup.com)

Created:       May 14, 2002

Abstract:      This module defines light-weight objects which allow very
               flexible access to a fixed number of positional and named
               attributes via several interfaces.

Compatibility: Python 2.2 and above

Requires:      new-style classes, Python 2.2 super builtin

Version:       0.8

Revision:      $Id: db_row.py,v 4.9 2003/10/15 18:03:03 jacobs Exp $

Copyright (c) 2002,2003 The OPAL Group.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

----------------------------------------------------------------------------------

This module defines light-weight objects suitable for many applications,
though the primary goal of the implementer is for storage of database query
results.  The primary design criteria for the data-structure where:

  1) store a sequence of arbitrary Python objects.
  2) the number of items stored in each instance should be constant.
  3) each instance must be as light-weight as possible, since many thousands
     of them are likely to be created.
  4) values must be retrievable by index:
     e.g.: d[3]
  5) values must be retrievable by field name by both Python attribute syntax and
     item syntax:
     e.g.: d.fields.foo == d['foo']
  6) optionally, operations using field names should be case-insensitive
     e.g.: d['FiElD'], d.fields.FiElD
  7) Otherwise drop-in compatible with tuple objects.
  8) Maintains a disjoint namespace for field names so they do not conflict
     with method names.

These criteria were chosen to simplify access to rows that are returned from
database queries.  Lets say that you run this query:

  cursor.execute('SELECT a,b,c FROM blah;')
  results = cursor.fetchall()

The resulting data-structure is typically a list of row tuples. e.g.:

  results = [ (1,2,3), (3,4,5), (6,7,8) ]

While entirely functional, these data types only allow integer indexed
access.  e.g., to query the b attribute of the second row:

  b = results[1][1]

This requires that all query results are accessed by index, which can be
very tedious and the code using this technique tends to be hard to maintain.
The alternative has always been to return a list of native Python
dictionaries, one for each row.  e.g.:

  results = [ {'a':1,'b':2,'c':3}, {'a':3,'b':4,'c':5},
              {'a':6,'b':7,'c':8} ]

This has the advantage of easier access to attributes by name, e.g.:

  foo = results[1]['b']

however, there are several serious disadvantages.

  1) each row requires a heavy-weight dictionary _per instance_.  This can
     damage performance by forcing a loaded system to start swapping virtual
     memory to disk when returning, say, 100,000 rows from a query.

  2) access by index is lost since Python dictionaries are unordered.

  3) attribute-access syntax is somewhat sub-optimal (or at least
     inflexible) since it must use the item-access syntax.

     i.e., x['a'] vs. x.a.

  4) Compatibility with code that expects tuples is lost.

Of course, the second and third problems can be partially addressed by
creating a UserDict (a Python class that looks and acts like a dictionary),
though that only magnifies the performance problems.

HOWEVER, there are some new features in Python 2.2 and newer that can
provide the best of all possible worlds.  Here is an example:

  # Create a new class type to store the results from our query (we'll make
  # field names case-insensitive just to show off)

  R=IMetaRow(['a','b','c'])

  # Create an instance of our new tuple class with values 1,2,3
  r=R( (1,2,3) )

  # Demonstrate all three accessor types
  print r['a'], r[1], r.fields.c
  > 1 2 3

  # Demonstrate case-insensitive operation
  print r['a'], r['A']
  > 1 1

  # Return the keys (column names)
  print r.keys()
  > ('a', 'b', 'c')

  # Return the values
  print r.values()
  > (1, 2, 3)

  # Return a list of keys and values
  print r.items()
  > (('a', 1), ('b', 2), ('c', 3))

  # Return a dictionary of the keys and values
  print r.dict()
  > {'a': 1, 'c': 3, 'b': 2}

  # Demonstrate slicing behavior
  print r[1:3]
  > (2, 3)

This solution uses some new Python 2.2 features and ends up allocating only
one dictionary _per row class_, not per row instance.  i.e., the row
instances do not allocate a dictionary at all!  This is accomplished using
the new-style object 'slots' mechanism.

Here is how you could use these objects:

  cursor.execute('SELECT a,b,c FROM blah;')

  # Make a class to store the resulting rows
  R = IMetaRow(cursor.description)

  # Build the rows from the row class and each tuple returned from the cursor
  results = [ R(row) for row in cursor.fetchall() ]

  print results[1].fields.b, results[2].fields.B, results[3]['b'], results[2][1]

Open implementation issues:

  o Values are currently mutable, so hashing of rows is explicitly
    disallowed.  This does not bother me much, though some may desire both
    mutable and immutable instance types.

  o The current row code returns most slicing, copying, combing operations
    (objects resulting from the '+' and '*' operators), keys(), values(),
    items() as tuples.  This is done to better conform to legacy code which
    assumes that rows are always tuples.  This seems sensible enough, though
    I welcome other opinions on the subject.

   o More documentation and doc-strings are needed.

   o Improve the integrated unit-tests (a la doctest or unittest, most likely)

   o Add some better example code.

Changes from version 0.71 -> 0.8:

  o Ported to win32+Mingw32 and includes pre-compiled Win32 versions for
    Python 2.2 and Python 2.3.

  o Fixed C implmentation to allow fields with zero elements.  The behavior
    now matches the pure-Python version.  (Reported by Anthony Baxter)

  o Fixed C implementation so that accessing unitialized fields raise an
    exception.  The behavior now matches the pure-Python version.

  o Other minor cleanups and tweaks

  o Added more unit tests.

Changes from version 0.7 -> 0.71:

  o Removed an unnecessary call to 'enumerate', which is only available in
    Python 2.3.  Thanks to Ben Golding of Object Craft for noticing this.

Changes from version 0.6 -> 0.7:

  o Removed some cruft from the Python implementation of FieldsBase.

  o Made the behavior of the Python base classes better match the C version
    in a few spots.

  o Cleaned up driver and description storage using properties.

  o Added a dictionary-like .get(key,default=None) method to the Row class.

  o Added new test cases.

Changes from version 0.5 -> 0.6:

  o Added missing slots declaration from Python FieldsBase object.  This
    corrected a major flaw in the pure-Python implementation which caused
    the allocation of per-instance dictionaries, and allowing access to
    undeclared fields.  The C version of FieldsBase was not affected.

  o Fixed exception types so that various accessors raise the appropriate
    exceptions.  e.g., previously __getitem__ would incorrectly raise
    AttributeError exceptions.  These changes were made in both the Python
    and C versions.

  o Added many new test cases to the regression suite, including much more
    rigorous read/write testing.

  o Removed some unnecessary (and slow!) code from the C fields_subscript
    function.  I suspect it was a left-over from past debugging that was
    not completely removed.
'''

__all__ = ['MetaFields', 'IMetaFields',
           'MetaRow',    'IMetaRow',
           'Fields',     'IFields',
           'Row',        'IRow',
           'FieldDescriptor']

FORCE_PURE_PYTHON = 0

try:
  Nothing
except NameError:
  Nothing = object()

class MetaFields(type):
  '''MetaFields:

     A meta-class that adds properties to a class that allow access to
     indexed elements in the class by names specified in the __fields__
     attribute of the class.  Indices start with __fieldoffset__ if it
     exists, or 0 if it does not.  Field name access is case-sensitive,
     though case-insensitive classes may be created using the
     IMetaFields meta-class.
  '''

  __slots__ = ()

  def __new__(cls, name, bases, field_dict):
    fields = field_dict.get('__fields__',())
    cls.build_properties(cls, fields, field_dict)

    return super(MetaFields,cls).__new__(cls, name, bases, field_dict)

  def build_properties(self, fields, field_dict):
    '''Helper function that creates field properties'''

    slots = list(field_dict.get('__slots__',[]))

    field_names = {}
    for s in slots:
      field_names[s] = 1

    for f in fields:
      if type(f) is not str:
        raise TypeError, 'Field names must be ASCII strings'
      if not f:
        raise ValueError, 'Field names cannot be empty'
      if f in field_names:
        raise ValueError, 'Field names must be unique: %s' % f

      slots.append(f)
      field_names[f] = 1

    fields = tuple(fields)
    slots  = tuple(slots)

    field_dict['__fieldnames__'] = fields
    field_dict['__fields__']     = fields
    field_dict['__slots__']      = slots

  build_properties = staticmethod(build_properties)


class IMetaFields(MetaFields):
  '''IMetaFields:

     A meta-class that adds properties to a class that allow access to
     indexed elements in the class by names specified in the __fields__
     attribute of the class.  Indices start with __fieldoffset__ if it
     exists, or 0 if it does not.  Field name access is case-insensitive,
     though case-sensitive classes may be created using the
     MetaFields meta-class.
  '''

  __slots__  = ()

  def build_properties(cls, fields, field_dict):
    '''Helper function that creates field properties'''

    try:
      ifields = tuple( [ f.lower() for f in fields ] )
    except AttributeError:
      raise TypeError, 'Field names must be ASCII strings'

    super(IMetaFields,cls).build_properties(cls, ifields, field_dict)
    field_dict['__fields__'] = tuple(fields)

  build_properties = staticmethod(build_properties)


try:
  if FORCE_PURE_PYTHON:
    raise ImportError

  import db_rowc
  FieldsBase  = db_rowc.abstract_fields
  IFieldsBase = db_rowc.abstract_ifields

except ImportError:
  class FieldsBase(object):

    __slots__ = ()

    def __init__(self, values):
      fields = type(self).__fieldnames__
      for field,value in zip(fields,values):
        setattr(self, field, value)

    def __len__(self):
      fields = type(self).__fieldnames__
      return len(fields)

    def __contains__(self, item):
      return item in tuple(self)

    def __str__(self):
      return str(tuple(self))

    def __repr__(self):
      return repr(tuple(self))

    def __getitem__(self, i):
      try:
        if isinstance(i, int):
          fields = self.__fieldnames__
          return getattr(self, fields[i])
        else:
          return getattr(self, i)
      except AttributeError:
        return None

    def __setitem__(self, i, value):
      if isinstance(i, int):
        fields = type(self).__fieldnames__
        setattr(self, fields[i], value)
      else:
        setattr(self, i, value)

    def __delitem__(self, i):
      if isinstance(i, int):
        fields = type(self).__fieldnames__
        delattr(self,fields[i])
      else:
        delattr(self,i)

    def __getslice__(self, i, j):
      return tuple(self)[i:j]

    def __setslice__(self, i, j, values):
      fields = type(self).__fieldnames__[i:j]
      for field,value in zip(fields,values):
        setattr(self, field, value)

    def __delslice__(self, i, j):
      fields = type(self).__fieldnames__[i:j]
      for field in fields:
        delattr(self,field)

    def __eq__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) == tuple(other)
      return tuple(self) == other

    def __ne__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) != tuple(other)
      return tuple(self) != other

    def __lt__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) < tuple(other)
      return tuple(self) < other

    def __gt__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) > tuple(other)
      return tuple(self) > other

    def __le__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) <= tuple(other)
      return tuple(self) <= other

    def __ge__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) >= tuple(other)
      return tuple(self) >= other

    def __add__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(self) + tuple(other)
      return tuple(self) + other

    def __radd__(self, other):
      if isinstance(other, FieldsBase):
        return tuple(other) + tuple(self)
      return other + tuple(self)

    def __mul__(self, other):
      return tuple(self) * other

    def __delattr__(self, key):
      super(FieldsBase, self).__setattr__(key,None)


  class IFieldsBase(FieldsBase):
    '''IFields:

       A tuple-like base-class that gains properties to allow access to
       indexed elements in the class by names specified in the __fields__
       attribute when the class is declared.  Indices start with
       __fieldoffset__ if it exists, or 0 if it does not.  Field name access
       is case-insensitive, though case-sensitive objects may be created by
       inheriting from the Fields base-class.
    '''

    __slots__ = ()

    def __getattribute__(self, key):
      return super(IFieldsBase, self).__getattribute__(key.lower())

    def __setattr__(self, key, value):
      super(IFieldsBase, self).__setattr__(key.lower(),value)

    def __delattr__(self, key):
      super(IFieldsBase, self).__setattr__(key.lower(),None)


class Fields(FieldsBase):
  '''Fields:

     A tuple-like base-class that gains properties to allow access to
     indexed elements in the class by names specified in the __fields__
     attribute when the class is declared.  Indices start with
     __fieldoffset__ if it exists, or 0 if it does not.  Field name access
     is case-sensitive, though case-insensitive objects may be created by
     inheriting from the IFields base-class.
  '''

  __metaclass__ = MetaFields
  __slots__ = ()


class IFields(IFieldsBase):
  '''IFields:

     A tuple-like base-class that gains properties to allow access to
     indexed elements in the class by names specified in the __fields__
     attribute when the class is declared.  Indices start with
     __fieldoffset__ if it exists, or 0 if it does not.  Field name access
     is case-insensitive, though case-sensitive objects may be created by
     inheriting from the Fields base-class.
  '''

  __metaclass__ = IMetaFields
  __slots__ = ()


try:
  if FORCE_PURE_PYTHON:
    raise ImportError

  import db_rowc
  RowBase = db_rowc.abstract_row

except ImportError:
  class RowBase(object):
    '''Row:

       A light-weight object which allows very flexible access to a fixed
       number of positional and named fields via several interfaces.  Field
       access by name is case-sensitive, though case-insensitive access is
       available via the IRow object.
    '''

    __slots__ = ('fields',)

    def __getitem__(self, key):
      if type(key) is str:
        try:
          return getattr(self.fields,key)
        except AttributeError:
          raise KeyError,key
      return self.fields.__getitem__(key)

    def __setitem__(self, key, value):
      if type(key) is str:
        try:
          setattr(self.fields,key,value)
        except AttributeError:
          raise KeyError,key
      else:
        self.fields.__setitem__(key,value)

    def __delitem__(self, key):
      if type(key) is str:
        try:
          delattr(self.fields,key)
        except AttributeError:
          raise KeyError,key
      else:
        self.fields.__delitem__(key)

    def __getslice__(self, i, j):
      return self.fields.__getslice__(i, j)

    def __setslice__(self, i, j, values):
      self.fields.__setslice__(i, j, values)

    def __delslice__(self, i, j):
      self.fields.__delslice__(i, j)

    def __hash__(self):
      raise NotImplementedError,'Row objects are not hashable'

    def __len__(self):
      return len(self.fields)

    def __contains__(self, item):
      return item in self.fields

    def __str__(self):
      return str(self.fields)

    def __repr__(self):
      return repr(self.fields)

    def __eq__(self, other):
      if isinstance(other, Row):
        return self.fields == other.fields
      return self.fields == other

    def __ne__(self, other):
      if isinstance(other, Row):
        return self.fields != other.fields
      return self.fields != other

    def __lt__(self, other):
      if isinstance(other, Row):
        return self.fields < other.fields
      return self.fields < other

    def __gt__(self, other):
      if isinstance(other, Row):
        return self.fields > other.fields
      return self.fields > other

    def __le__(self, other):
      if isinstance(other, Row):
        return self.fields <= other.fields
      return self.fields <= other

    def __ge__(self, other):
      if isinstance(other, Row):
        return self.fields >= other.fields
      return self.fields >= other

    def __add__(self, other):
      if isinstance(other, Row):
        return self.fields + other.fields
      return self.fields + other

    def __radd__(self, other):
      if isinstance(other, Row):
        return other.fields + self.fields
      return other + self.fields

    def __mul__(self, other):
      return self.fields * other


class Row(RowBase):
  '''Row:

     A light-weight object which allows very flexible access to a fixed
     number of positional and named fields via several interfaces.  Field
     access by name is case-sensitive, though case-insensitive access is
     available via the IRow object.
  '''

  __slots__ = ()

  driver = property(lambda self: type(self).driver)
  descr  = property(lambda self: type(self).field_descriptors)

  def keys(self):
    '''r.keys() -> list of r's field names'''
    return type(self.fields).__fields__

  def items(self):
    '''r.items() -> tuple of r's (field, value) pairs, as 2-tuples'''
    return zip(self.keys(),self.fields)

  def get(self, key, default=None):
    if not isinstance(key, str):
      return default
    try:
      return self[key]
    except KeyError:
      return default

  def has_key(self, key):
    '''r.has_key(k) -> 1 if r has field k, else 0'''
    return key in type(self.fields).__fieldnames__

  def dict(self):
    '''r.dict() -> dictionary mapping r's fields to its values'''
    return dict(self.items())

  def copy(self):
    '''r.copy() -> a shallow copy of r'''
    return type(self)(self)

  def __hash__(self):
    raise NotImplementedError,'Row objects are not hashable'


class IRow(Row):
  '''IRow:

     A light-weight object which allows very flexible access to a fixed
     number of positional and named fields via several interfaces.  Field
     access by name is case-insensitive, though case-sensitive access is
     available via the Row object.
  '''

  __slots__ = ()

  def has_key(self, key):
    if isinstance(key, str):
      key = key.lower()
    return super(IRow, self).has_key(key)


class MetaRowBase(type):
  '''MetaRowBase:

     A meta-class that builds row objects given a list of fields or field
     schema.  Field acces is case-sensitive, though a case-insensitive
     version, IMetaRow, is also available.
  '''

  __slots__  = ()

  def __new__(cls, name, bases, cls_dict):
    fields = tuple(cls_dict.get('__fields__',()))

    field_dict = {}
    field_dict['__slots__'] = getattr(cls.field_base,'__slots__',())

    field_names = []
    field_descriptors = []

    for field in fields:
      descriptor = FieldDescriptor(field)
      field_names.append(descriptor.name)
      field_descriptors.append(descriptor)

    field_dict['__fields__'] = tuple(field_names)
    field_class = type('%s_fields' % name, (cls.field_base,), field_dict)

    cls_dict['field_descriptors'] = field_class(field_descriptors)

    row_class = super(MetaRowBase,cls).__new__(cls, name, bases, cls_dict)

    assert '__init__' not in cls_dict

    def __init__(self, fields):
      super(row_class, self).__init__(fields)
      self.fields = field_class(fields)

    row_class.__init__ = __init__

    return row_class


class MetaRow(MetaRowBase):
  '''MetaRow:

     A meta-class that builds row objects given a list of fields or field
     schema.  Field acces is case-sensitive, though a case-insensitive
     version, IMetaRow, is also available.
  '''

  __slots__  = ()
  row_base   = Row
  field_base = Fields

  def __new__(cls, fields, driver = None):
    cls_dict = {'__slots__' : (), '__fields__' : fields, 'driver' : driver}
    return super(MetaRow,cls).__new__(cls, 'row', (cls.row_base,), cls_dict)


class IMetaRow(MetaRowBase):
  '''IMetaRow:

     A meta-class that builds row objects given a list of fields or field
     schema.  Field acces is case-insensitive, though a case-sensitive
     version, MetaRow, is also available.
  '''

  __slots__  = ()
  row_base   = IRow
  field_base = IFields

  def __new__(cls, fields, driver = None):
    cls_dict = {'__slots__' : (), '__fields__' : fields, 'driver' : driver}
    return super(IMetaRow,cls).__new__(cls, 'irow', (cls.row_base,), cls_dict)


class FieldDescriptor(Fields):
  '''FieldDescriptor:

     A class that includes the Python DB-API 2.0 schema description fields
     that allows read-only access to data elements by name and by index.
  '''

  __slots__  = ()
  __fields__ = ('name', 'type_code', 'display_size', 'internal_size',
               'precision', 'scale', 'null_ok')

  def __init__(cls, desc):
    if isinstance(desc, (tuple,list)):
      desc = tuple(desc) + (None,)*(6-len(desc))
    elif not isinstance(desc, FieldDescriptor):
      desc = (desc,)+(None,)*6

    super(FieldDescriptor,cls).__init__(desc)

  def __str__(self):
    fields = type(self).__fields__
    values = ['%s: %s' % (key,repr(value)) for key,value in zip(fields, self) ]
    return '{%s}' % ', '.join(values)

  __repr__ = __str__


class RowList(list):
  __slots__ = ('row_class',)
  def __init__(self, values, row_class = None):
    super(RowList,self).__init__(values)
    self.row_class = row_class
  driver = property(lambda self: self.row_class.driver)
  descr  = property(lambda self: self.row_class.field_descriptors)


class NullRow(type(Nothing)):
  __slots__ = ('driver','row_class','descr')
  driver = property(lambda self: self.row_class.driver)
  descr  = property(lambda self: self.row_class.field_descriptors)
  def __new__(self):
    return object.__new__(self)
  def __init__(self, row_class = None):
    self.row_class = row_class
  def __eq__(self, other):
    return 0
  def __ne__(self, other):
    return 1
  def __nonzero__(self):
    return 0


def test(cls):
  D=cls(['a','B','c'])
  d=D( (1,2,3) )

  assert d['a']==d[0]==d.fields.a==d.fields[0]==1
  assert d['B']==d[1]==d.fields.B==d.fields[1]==2
  assert d['c']==d[2]==d.fields.c==d.fields[2]==3

  assert len(d) == 3
  assert d.has_key('a')
  assert d.has_key('B')
  assert d.has_key('c')
  assert 'd' not in d
  assert 1 in d
  assert 2 in d
  assert 3 in d
  assert 4 not in d
  assert not d.has_key(4)
  assert not d.has_key('d')
  assert d[-1] == 3
  assert d[1:3] == (2,3)

  assert d.keys() == ('a','B','c')
  assert d.items() == [('a', 1), ('B', 2), ('c', 3)]
  assert d.dict()  == {'a': 1, 'c': 3, 'B': 2}
  assert d.copy() == d
  assert d == d.copy()
  assert d is not d.copy()
  assert type(d) is type(d.copy())
  assert d.fields is not d.copy().fields
  assert [ x for x in d ] == [1,2,3]

  assert d.get('a') == 1
  assert d.get('B') == 2
  assert d.get('c') == 3

  assert d.get('d') == None
  assert d.get(0)   == None
  assert d.get(3)   == None

  assert d.get('d', -1) == -1
  assert d.get(0,   -1) == -1
  assert d.get(3,   -1) == -1

  assert d.fields==d.fields
  assert d == d
  assert d == (1,2,3)
  assert (1,2,3) == d
  assert d!=()
  assert ()<d
  assert ()<=d
  assert d>()
  assert d>=()

  try:
    d[4]
    raise AssertionError, 'Illegal index not caught'
  except IndexError:
    pass

  try:
    d['f']
    raise AssertionError, 'Illegal key not caught'
  except KeyError:
    pass

  try:
    d.fields.f
    raise AssertionError, 'Illegal attribute not caught'
  except AttributeError:
    pass


def test_insensitive(cls):
  D=cls(['a','B','c'])
  d=D( (1,2,3) )

  assert d['a']==d['A']==d[0]==d.fields.A==d.fields.a==d.fields[0]==1
  assert d['b']==d['B']==d[1]==d.fields.B==d.fields.b==d.fields[1]==2
  assert d['c']==d['C']==d[2]==d.fields.C==d.fields.c==d.fields[2]==3

  assert d.has_key('a')
  assert d.has_key('A')
  assert d.has_key('b')
  assert d.has_key('B')
  assert d.has_key('c')
  assert d.has_key('C')
  assert not d.has_key('d')
  assert not d.has_key('D')

  assert 1 in d
  assert 2 in d
  assert 3 in d
  assert 4 not in d
  assert 'a' not in d
  assert 'A' not in d
  assert 'd' not in d
  assert 'D' not in d

  assert d.get('A') == 1
  assert d.get('b') == 2
  assert d.get('C') == 3


def test_concat(cls):
  D=cls(['a','B','c'])
  d=D( (1,2,3) )

  assert d+(4,5,6) == (1, 2, 3, 4, 5, 6)
  assert (4,5,6)+d == (4, 5, 6, 1, 2, 3)
  assert d+d       == (1, 2, 3, 1, 2, 3)
  assert d*2       == (1, 2, 3, 1, 2, 3)


def test_descr(cls):
  D=cls( (('field1', 1, 2, 3, 4, 5, 6),
          ('field2', 0, 0, 0, 0, 0, 0),
          'field3') )
  d = D( (1,2,3) )

  assert d==(1,2,3)
  assert len(d.descr) == 3
  assert d.descr[0] == ('field1', 1, 2, 3, 4, 5, 6)
  assert d.descr[0].name          == 'field1'
  assert d.descr[0].type_code     == 1
  assert d.descr[0].display_size  == 2
  assert d.descr[0].internal_size == 3
  assert d.descr[0].precision     == 4
  assert d.descr[0].scale         == 5
  assert d.descr[0].null_ok       == 6
  assert d.descr[1] == ('field2', 0, 0, 0, 0, 0, 0)
  assert d.descr[2] == ('field3', None, None, None, None, None, None)


def test_rw(cls):
  D=cls(['a','B','c'])
  d=D( (1,2,3) )

  assert d['a']==d[0]==d.fields.a==1
  assert d['B']==d[1]==d.fields.B==2
  assert d['c']==d[2]==d.fields.c==3

  d['a']     = 4
  d[1]       = 5
  d.fields.c = 6

  assert d['a']==d[0]==d.fields.a==4
  assert d['B']==d[1]==d.fields.B==5
  assert d['c']==d[2]==d.fields.c==6

  d[:] = (7,8,9)

  assert d['a']==d[0]==d.fields.a==7
  assert d['B']==d[1]==d.fields.B==8
  assert d['c']==d[2]==d.fields.c==9

  d.fields[:] = (1,2,3)

  assert d['a']==d[0]==d.fields.a==1
  assert d['B']==d[1]==d.fields.B==2
  assert d['c']==d[2]==d.fields.c==3

  del d[0]

  assert d[0] == None
  assert d == (None, 2, 3)

  del d[:]

  assert d == (None, None, None)
  assert d[0]==d[1]==d[2]==None

  d.fields.a = 1
  d['B'] = 2
  assert d[0:2] == (1,2)

  del d.fields.a
  del d['B']
  assert d[0:2] == (None,None)

  try:
    d['g'] = 'illegal'
    raise AssertionError,'Illegal setitem'
  except KeyError:
    pass

  try:
    del d['g']
    raise AssertionError,'Illegal delitem'
  except KeyError:
    pass

  try:
    d[5] = 'illegal'
    raise AssertionError,'Illegal setitem'
  except IndexError:
    pass

  try:
    del d[5]
    raise AssertionError,'Illegal delitem'
  except IndexError:
    pass

  try:
    d.fields.g = 'illegal'
    raise AssertionError,'Illegal setattr'
  except AttributeError:
    pass

  try:
    del d.fields.g
    raise AssertionError,'Illegal delattr'
  except AttributeError:
    pass


def test_Irw(cls):
  D=cls(['a','B','c'])
  d=D( (1,2,3) )

  assert d['a']==d[0]==d.fields.a==1
  assert d['B']==d[1]==d.fields.B==2
  assert d['c']==d[2]==d.fields.c==3

  d['A']     = 4
  d[1]       = 5
  d.fields.C = 6

  assert d['A']==d[0]==d.fields.A==4
  assert d['b']==d[1]==d.fields.B==5
  assert d['C']==d[2]==d.fields.C==6

  d[:] = (7,8,9)

  assert d['a']==d[0]==d.fields.a==7
  assert d['B']==d[1]==d.fields.B==8
  assert d['c']==d[2]==d.fields.c==9

  d.fields[:] = (1,2,3)

  assert d['a']==d[0]==d.fields.a==1
  assert d['b']==d[1]==d.fields.b==2
  assert d['c']==d[2]==d.fields.c==3

  del d[0]

  assert d[0] == None
  assert d == (None, 2, 3)

  del d[:]

  assert d == (None, None, None)
  assert d[0]==d[1]==d[2]==None

  d.fields.A = 1
  d['b'] = 2
  assert d[0:2] == (1,2)

  del d.fields.A
  del d['b']
  assert d[0:2] == (None,None)


def test_incomplete(cls):
  D=cls(['a','B','c'])
  d=D( ' ' )

  assert d['a'] == ' '
  assert d.fields.a == ' '

  try:
    d['B']
    raise AssertionError,'Illegal getitem: "%s"' % d['B']
  except KeyError:
    pass

  try:
    d['c']
    raise AssertionError,'Illegal getitem'
  except KeyError:
    pass

  try:
    d.fields.b
    raise AssertionError,'Illegal getattr'
  except AttributeError:
    pass

  try:
    d.fields.c
    raise AssertionError,'Illegal getattr'
  except AttributeError:
    pass

  d['c'] = 1
  d.fields.c = 2


def test_empty(cls):
  D=cls([])
  d=D([])


if __name__ == '__main__':
  import gc,sys

  N = 100

  orig_objects = len(gc.get_objects())

  for i in range(N):
    for cls in [MetaRow,IMetaRow]:
      test(cls)
      test_concat(cls)
      test_descr(cls)
      test_rw(cls)
      test_incomplete(cls)
      test_empty(cls)

    test_insensitive(IMetaRow)
    test_Irw(IMetaRow)
    gc.collect()

  # Detect memory leak fixed in 2.2.2 (& 2.3pre CVS)
  gc.collect()
  new_objects = len(gc.get_objects()) - orig_objects
  if new_objects >= N:
    print "WARNING: Detected memory leak of %d objects." % new_objects
    if sys.version_info >= (2,2,2):
      print "         Please notify jacobs@theopalgroup.com immediately."
    else:
      print "         You are running a Python older than 2.2.1 or older.  Several"
      print "         memory leaks in the core interepreter were fixed in version"
      print "         2.2.2, so we strongly recommend upgrading."

  print 'Tests passed'
