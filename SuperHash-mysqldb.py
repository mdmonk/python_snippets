"""DB wrapper that uses smart struct-like objects to track data changes.

original author: Jeremy Friesen
updated by: Adam Vandenberg

Database is a layer on top of MySQLdb.

A SuperHash is a struct-like object that tracks updates to the underlying data. The string representation of an SuperHash is a string of change values of the form "name=value,name=value,name=value" that can be placed into the SET clause of a SQL INSERT or UPDATE.
"""

import MySQLdb
import time

class Error(Exception): pass

class ConditionMissingError(Error): pass
class TableMissingError(Error): pass
class NoRowsFoundError(Error): pass

def esc(thing):
	"Stringize and escape something for use in a SQL statement."
	if thing is None:
		return 'NULL'
	else:
		return '"%s"' % MySQLdb.escape_string(str(thing))


class Database(object):
	"The database connection."
	
	def date():
		"The current date in SQL format (YYYY-MM-DD)."
		return time.strftime("%Y-%m-%d", time.localtime(time.time()))
	date = staticmethod(date)
	
	def datetime():
		"The current datetime in SQL format (YYYY-MM-DD HH:MM:SS)."
		return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
	datetime = staticmethod(datetime)

		
	def __init__(self, username, dbname, dbpass='',hostname="localhost"):
		"Connect to the DB. Exceptions may be raised."
		self.DB = MySQLdb.connect(host=hostname, user=username, db=dbname, passwd=dbpass)
		self.debug = False
	
	def __del__(self):
		"Clean up if connected."
		try:
			self.DB.close()
		except:
			pass
	
	# Create a superhash with exact columns
	def newRow(self, table, data=None):
		columns = self.loadSchema(table)

		row = SuperHash(table=table, cols=[col.Field for col in columns])
		if data is not None:
			row._Add(data, False)
			
		return row

	def execute(self, operation, args=None):
		"Send one command to the database and execute it."		
		if self.debug: print 'Executing '+operation

		cur = self.DB.cursor()
		cur.execute(operation,args)
		return cur
	
	def loadObject(self, command, args=None):
		"Execute the command and return one object."		
		cur = self.execute(command, args)
		data = self.objectFromCursor(cur)
		cur.close()
		
		return data
	
	def loadObjects(self, command, args=None):
		"Execute the command and return a list of objects."
		
		cur = self.execute(command, args)
		data = self.objectsFromCursor(cur)
		cur.close()
		
		return data

	def loadSchema(self, table):
		return self.loadObjects("SHOW COLUMNS FROM %s" % table)

	def loadRow(self, table, id, name=None, cols=None):
		"Load a DB row from a table"
		if name is None: name = "id"
		if cols is None: cols = "*"
		
		row = self.loadObject(
			"select %s from %s where %s=%%s" % (",".join(cols), table, name), id)
			
		if row is not None:
			row._Table = table
		
		return row

	def loadValue(self, command, args=None, default=None):
		"""Load a single value from the DB.
		
		Returns the value from the first column of the first row of the result set. If no rows were returned, returns None.

		NOTE: This function returns None for no rows OR if the value is NULL.
		"""
		cur = self.execute(command, args)
		if cur.rowcount == 0:
			return default
			
		data = cur.fetchone()
		cur.close()
		
		return data[0]
		
	def objectFromCursor(self, cur):
		"Load one object from a DB cursor."
		row = cur.fetchone()
		if row is None:
			return None
		
		obj = SuperHash()
		for i in range(len(row)):
			obj._Data[cur.description[i][0]] = row[i]			
		
		return obj
	
	def objectsFromCursor(self, cur):
		"Load all objects from a DB cursor. If there are no results an empty list is returned."
		return [self.objectFromCursor(cur) for i in range(cur.rowcount)]
		
	def storedID(self):
		return self.loadValue("SELECT LAST_INSERT_ID()")
	
	def storeObject(self, table, obj, getID=True):
		"Inserts an object into the db."
		
		setvars = obj._GetData(True)
		if setvars == "": return
		command = "insert into "+table+" set "+setvars
		
		self.execute(command)
		
		if getID: obj.id=self.storedID()
		obj._Clean()
	
	def updateObject(self, table, obj, condition):
		"Updates an object in the db based on a condition."
		
		if condition is None:
			raise ConditionMissingError, "Update to table %s with no condition." %(table,)
		
		setvars = str(obj)
		if setvars == "":
			return
		
		command = "update %s set %s where %s" % (table,setvars,condition)
			
		self.execute(command)
		obj._Clean()


	def updateRow(self, table, obj):
		"Updates an object in the db on the ID of the row."
		
		self.updateObject(table, obj, 'id=' + esc(obj.id))
	

	def deleteRow(self, table, obj):
		self.execute('delete from %s where id=%%s' % table, obj.id)
		

class SuperHash(object):
	"""A struct-like object that tracks data changes.
	
	a = SuperHash()
	a.key = 'value'
	
	This object acts like an expandable struct that tracks changes to data. The str() of a SuperHash is a string that can be used in the SET clause of a SQL INSERT or UPDATE statment.
	"""
	
	def __init__(self, table=None, cols=None):
		self._Table = table
		self._Columns = cols
		self._Data = {}
		self._Touched = {}
		
	def  _Store(self, db):
		if self._Table is None: raise TableMissingError, "No table defined for this row"
		db.storeObject(self._Table, self)
		
	def  _Update(self, db):
		if self._Table is None: raise TableMissingError, "No table defined for this row"
		db.updateRow(self._Table, self)
		
	def _Delete(self, db):
		if self._Table is None: raise TableMissingError, "No table defined for this row"
		db.deleteRow(self._Table, self)
		
	def __getattr__(self, name):
		"Route database variables to OB_Data."
		try:
			return self.__getitem__(name)
		except IndexError, error:
			raise AttributeError, error
			
	def __setattr__(self, name, value):
		"Set a variable and touch it."
		if name.startswith("_"):
			object.__setattr__(self,name,value)
		else:
			try:
				self.__setitem__(name,value)
			except IndexError, error:
				raise AttributeError, error

	def __repr__(self):
		"Dump the key=value data. Dirty items have a * by them."
		value_strs = []
		for key in self._Data:
			dirty = ""
			if key in self._Touched:
				dirty = "*"
				
			value_strs.append( "%s%s: %s" % (dirty, key, self._Data[key]) ) 
		
		return "<SuperHash: " + ", ".join(value_strs) + ">"

	def _GetData(self, includeAll=False):
		"Turn this superhash into a key=value list of changed values."
		if includeAll:
			keys = self._Data.keys()
		else:
			keys = self._Touched.keys()
			
		fields = ["%s=%s" % (key, esc(self._Data[key])) for key in keys]
		return ','.join(fields)
	
	def __str__(self):
		return self._GetData(False)
		
	def _Clean(self):
		self._Touched = {}
		
	def __getitem__(self, name):
		columns = self._Columns
		if columns is not None:
			if not name in columns:
				raise IndexError, "No column named "+name
		
		try:
			return self._Data[name]
		except KeyError, attr:
			if columns is not None:
				return None
			else:
				raise IndexError, "No data for column " +name

	def __setitem__(self, name, value):
		if self._Columns is not None:
			if not name in self._Columns:
				raise IndexError, "No column named "+name

		#Only dirty data if it changes
		old_value = self._Data.get(name)
		if (old_value != value):
			self._Data[name] = value
			self._Touched[name] = True

	def __contains__(self, name):
		if self._Columns is not None:
			return name in self._Columns
		else:
			return name in self._Data
		
	def _Add(self, hash, dirty=True):
		"""Add values in hash to _Data.
		
		 Defaults to adding data as dirty. Pass dirty=False to insert clean data.
		"""		
		for key in hash:
			self._Data[key] = hash[key]
			if dirty:
				self._Touched[key] = True

class ProxyMixin(object):
	def __init__(self, row):
		self.__row = row

	def __getattr__(self, name):
		"Act as a proxy for the user db row"
		return self.__row.__getattr__(name)
		
	def __getitem__(self, name):
		return self.__row.__getitem__(name)
		
	def __setitem__(self, name, value):
		return self.__row.__setitem__(name, value)
		
	def __contains__(self, name):
		return self.__row.__contains__(name)
				
def demo():
	"A cheesy test script."
	
	print "Creating a SuperHash..."
	
	a = SuperHash()
	
	# Add some clean data
	a_Add({'beef':'steak', 'chicken':'nuggets'}, False)
	
	# Dirty up some data
	a.beef = "Wellington"
	a.pork = "chops"

	print "Repr: ",repr(a)	
	print "Str: ",str(a)
	
	print
	print "Adding a hash..."
	
	a._Add({'eggs': 'benedict', 'orange': 'juice'}, False)
	a._Add({'orange': 'peels', 'grapefruit': 'wedges'})
	
	print "Repr: ",repr(a)	
	print "Str: ",str(a)
	
	print

if __name__=="__main__":
	demo()
