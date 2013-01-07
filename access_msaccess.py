"""
Basically just an API wrapped around Douglas Savitsky's code at http://www.ecp.cc/pyado.html
Recordset iterator taken from excel.py in Nicolas Lehuen's code at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440661
Handling of field types taken from Craig Anderson's code at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/104801
"""
AD_OPEN_KEYSET = 1
AD_LOCK_OPTIMISTIC = 3
INTEGER = 'integer'
SMALLINT = 'smallint'
UNSIGNEDTINYINT = 'unsignedtinyint'
CURRENCY = 'currency'
DATE = 'date'
BOOLEAN = 'boolean'
TIMESTAMP = 'timestamp'
VARCHAR = 'varchar'
LONGVARCHAR = 'longvarchar'
SINGLE = 'single'

INDEX_UNIQUE = 'unique'
INDEX_NOT_UNIQUE = 'notunique'
INDEX_PRIMARY = 'indexprimary'
INDEX_NOT_PRIMARY = "indexnotprimary"

import win32com.client
#Must run makepy once - see http://www.thescripts.com/forum/thread482449.html e.g. the following way
#run PYTHON\Lib\site-packages\pythonwin\pythonwin.exe (replace PYTHON with folder python is in)
#Tools>COM Makepy utility - select library named Microsoft ActiveX Data Objects 2.8 Library (2.8) and select OK
#Microsoft ActiveX Data Objects Recordset 2.8 Library (2.8)
class AccessDb:
    """An Access connection"""
        
    def connect(self, data_source, user, pwd, mdw):
        """Returns a connection to the jet database
        NB use .Close() to close (NB title case unlike closing a file)"""
        connAccess = win32com.client.Dispatch(r'ADODB.Connection')
        """DSN syntax - http://support.microsoft.com/kb/193332 and 
        http://www.codeproject.com/database/connectionstrings.asp?df=100&forumid=3917&exp=0&select=1598401"""
        DSN = """PROVIDER=Microsoft.Jet.OLEDB.4.0;DATA SOURCE=%s;
            USER ID=%s;PASSWORD=%s;Jet OLEDB:System Database=%s;""" % (data_source, user, pwd, mdw)
        #print DSN
        connAccess.Open(DSN)
        return connAccess
    
    def getRecordset(self, connAccess, SQL_statement):
        """Get recordset"""
        return Recordset(connAccess, SQL_statement)
    
    def getTableNames(self, connAccess):
        """Get list of tables.  NB not system tables"""
        cat = win32com.client.Dispatch(r'ADOX.Catalog')
        cat.ActiveConnection = connAccess
        alltables = cat.Tables
        tab_names = []
        for tab in alltables:
            if tab.Type == 'TABLE':
                tab_names.append(tab.Name)
        return tab_names
    
    def getTables(self, connAccess):
        """Get dictionary of table objects - table name is the key"""
        tab_names = self.getTableNames(connAccess)
        tabs = {}
        for tab_name in tab_names:
            tabs[tab_name] = Table(connAccess, tab_name)
        return tabs

class Table:
    """Table object with rs, name, and index properties"""
    def __init__ (self, connAccess, tab_name):
        self.rs = win32com.client.Dispatch(r'ADODB.Recordset')
        self.rs.Open("[%s]" % tab_name, connAccess, AD_OPEN_KEYSET, AD_LOCK_OPTIMISTIC)
        self.name = tab_name
        self.indexes = self.__getIndexes(connAccess, tab_name)
    
    def getFields(self):
        """Get list of field objects"""
        field_names = [field.Name for field in self.rs.Fields]
        fields = []
        for field_name in field_names:
            fields.append(Field(self.rs, field_name))        
        return fields
    
    def __getIndexes(self, connAccess, tab_name):
        """Get list of table indexes"""
        cat = win32com.client.Dispatch(r'ADOX.Catalog')
        cat.ActiveConnection = connAccess
        index_coll = cat.Tables(tab_name).Indexes
        indexes = []
        for index in index_coll:
            indexes.append(Index(index))
        return indexes
        
class Index:
    """Index object with following properties: name, index type (UNIQUE or not),
    primary or not, and index fields - a tuple of index fields in index"""
    def __init__ (self, index):
        self.name = index.Name        
        if index.Unique:
            self.type = INDEX_UNIQUE
        else:
            self.type = INDEX_NOT_UNIQUE
        self.fields = []
        for item in index.Columns:
            self.fields.append(item.Name)
        if index.PrimaryKey:
            self.primary = INDEX_PRIMARY
        else:
            self.primary = INDEX_NOT_PRIMARY
    
class Field:
    """Field object with name, type, and size properties"""
    def __init__ (self, rs, field_name):
        self.name = field_name
        adofield = rs.Fields.Item(field_name)
        adotype = adofield.Type
        #http://www.devguru.com/Technologies/ado/quickref/field_type.html
        if adotype == win32com.client.constants.adInteger:
            self.type = INTEGER
        elif adotype == win32com.client.constants.adSmallInt:
            self.type = SMALLINT
        elif adotype == win32com.client.constants.adUnsignedTinyInt:
            self.type = UNSIGNEDTINYINT
        elif adotype == win32com.client.constants.adCurrency:
            self.type = CURRENCY
        elif adotype == win32com.client.constants.adDate:
            self.type = DATE
        elif adotype == win32com.client.constants.adBoolean:
            self.type = BOOLEAN
        elif adotype == win32com.client.constants.adDBTimeStamp:
            self.type = TIMESTAMP
        elif adotype == win32com.client.constants.adVarWChar:
            self.type = VARCHAR
        elif adotype == win32com.client.constants.adLongVarWChar:
            self.type = LONGVARCHAR
        elif adotype == win32com.client.constants.adSingle:
            self.type = SINGLE
        else:
            raise "Unrecognised ADO field type %d" % adotype
        self.size = adofield.DefinedSize

def encoding(value):
    if isinstance(value,unicode):
        value = value.strip()
        if len(value)==0:
            return None
        else:
            return value.encode("mbcs") #mbcs is a Windows, locale-specific encoding
    elif isinstance(value,str):
        value = value.strip()
        if len(value)==0:
            return None
        else:
            return value 
    else:
        return value

class Recordset:
    """Recordset created from a query"""
    def __init__ (self, connAccess, SQL_statement):
        self.rs = win32com.client.Dispatch(r'ADODB.Recordset')
        self.rs.CursorLocation = 3 #uses client - makes it possible to use RecordCount property
        self.rs.Open(SQL_statement, connAccess, AD_OPEN_KEYSET, AD_LOCK_OPTIMISTIC)
 
    def getFieldNames(self):
        """Get list of field names"""
        field_names = [field.Name for field in self.rs.Fields]
        return field_names
    
    def hasRows(self):
        """Does the recordset contain any rows?"""
        try:
            self.rs.MoveFirst()
        except:
            return False
        return True
    
    def getCount(self):
        """Get record count - NB rs.CursorLocation had to be set to 3 (client) to enable this"""
        try:
            return self.rs.RecordCount
        except:
            return 0
    
    def __iter__(self):
        """ Returns a paged iterator by default. See paged().
        """
        return self.paged()
    
    def paged(self,pagesize=128):
        """ Returns an iterator on the data contained in the sheet. Each row
            is returned as a dictionary with row headers as keys. pagesize is
            the size of the buffer of rows ; it is an implementation detail but
            could have an impact on the speed of the iterator. Use pagesize=-1
            to buffer the whole sheet in memory.
        """
        try:
            field_names = self.getFieldNames()
            #field_names = [self.encoding(field.Name) for field in recordset.Fields]
            ok = True
            while ok:
                # Thanks to Rogier Steehouder for the transposing tip 
                rows = zip(*self.rs.GetRows(pagesize))                
                if self.rs.EOF:
                    # close the recordset as soon as possible
                    self.rs.Close()
                    self.rs = None
                    ok = False
                for row in rows:
                    yield dict(zip(field_names, map(encoding,row)))                
        except:
            if self.rs is not None:
                self.rs.Close()
                del self.rs
            raise
