"""In-memory database management

Access by list comprehension or generator expression

Syntax :
    from strakell import Base
    db = Base('dummy')
    # create new base with field definitions
    # field type can be str, unicode, int or float
    db.create(name=str,age=int,size=float)
    # existing base
    db.open()
    # insert new record
    db.insert(name='homer',age=23,size=1.84)
    # records are dictionaries with a unique integer key __id__
    # selection by list comprehension
    res = [ r for r in db if 30 > r['age'] >= 18 and r['size'] < 2 ]
    # or generator expression
    for r in (r for r in db if r['name'] in ('homer','marge') ]
    # delete a list of records
    db.delete(selected_records)
    # direct access by id
    record = db[rec_id] # return the record with __id__ == rec_id
    # make an index on a field
    db.create_index('age')
    # access by index
    records = db.age[23] # returns the list of records with age == 23
    # update
    db.update(record,age=24)
    # save changes on disk
    db.commit() # save on disk
"""

import os
import cPickle
import bisect

class Index:
    """Class used as an attribute of Base instances"""

    def __init__(self,db,field):
        self.db = db # database object (instance of Base)
        self.field = field # field name

    def __getitem__(self,key):
        """Lookup by key : return the list of records where
        field value is equal to this key, or an empty list"""
        ids = self.db.indices[self.field].get(key,[])
        return [ self.db.records[_id] for _id in ids ]

class Base:

    def __init__(self,basename):
        self.name = basename

    def create(self,**fields):
        """Create a new base. The keyword arguments are k=v where k
        is the field name and v is the built-in type of the field"""
        if os.path.exists(self.name):
            raise IOError,"Base %s already exists" %self.name
        for v in fields.values():
            if v not in [str,unicode,int,float]:
                raise TypeError,"type %s not allowed" %v
        self.fields = fields
        self.field_names = fields.keys()
        self.records = {}
        self.next_id = 0
        self.indices = {}
        return self

    def create_index(self,*field_names):
        """Create an index on the specified field names
        
        An index on a field is a mapping between the values taken by the field
        and the sorted list of the ids of the records whose field is equal to 
        this value
        
        For each field, an attribute of self is created, an instance of
        the class Index (see above)
        """
        for f in field_names:
            if not f in self.field_names:
                raise NameError,"%s is not a field name" %f
            # initialize the indices
            self.indices[f] = {}
            for _id,record in self.records.iteritems():
                # use bisect to quickly insert the id in the list
                bisect.insort(self.indices[f].setdefault(record[f],[]),
                    _id)
            # create a new attribute of self, used to find the records
            # by this index
            setattr(self,f,Index(self,f))

    def open(self):
        """Open an existing database and load its content into memory"""
        _in = open(self.name,'rb')
        fields = cPickle.load(_in)
        self.field_names = [ k for (k,v) in fields ]
        self.fields = dict((k,eval(v)) for (k,v) in fields)
        self.next_id = cPickle.load(_in)
        self.records = cPickle.load(_in)
        self.indices = cPickle.load(_in)
        for f in self.indices.keys():
            setattr(self,f,Index(self,f))
        _in.close()
        return self

    def commit(self):
        """Write the database to a file"""
        out = open(self.name,'wb')
        fields = [(k,v.__name__) for (k,v) in self.fields.iteritems()]
        cPickle.dump(fields,out)
        cPickle.dump(self.next_id,out)
        cPickle.dump(self.records,out)
        cPickle.dump(self.indices,out)
        out.close()

    def insert(self,**kw):
        """Insert a record in the database
        If some of the fields are missing the value is set to None
        """
        # initialize all fields to None
        record = dict((f,None) for f in self.fields.keys())
        # set keys and values
        for (k,v) in kw.iteritems():
            self._validate(k,v)
            record[k]=v
        # add the key __id__ : record identifier
        record['__id__'] = self.next_id
        # create an entry in the dictionary self.records, indexed by __id__
        self.records[self.next_id] = record
        # update index
        for ix in self.indices.keys():
            bisect.insort(self.indices[ix].setdefault(record[ix],[]),
                self.next_id)
        # increment the next __id__ to attribute
        self.next_id += 1

    def delete(self,removed_records):
        """Remove the records in the iterable removed_records
        Return the number of deleted items
        """
        # convert iterable into a list (to be able to sort it)
        removed = [ r for r in removed_records ]
        # sort by record id
        removed.sort(lambda x,y:cmp(x['__id__'],y['__id__']))
        deleted = 0
        while removed:
            r = removed.pop()
            deleted += 1
            _id = r['__id__']
            # remove id from indices
            for indx in self.indices.keys():
                pos = bisect.bisect(self.indices[indx][r[indx]],_id)-1
                del self.indices[indx][r[indx]][pos]
            # remove record from self.records
            del self.records[_id]
        return deleted

    def update(self,record,**kw):
        """Update the record with new keys and values and update indices"""
        # validate all the keys and values before updating
        for k,v in kw.iteritems():
            self._validate(k,v)
        # update record values
        for k,v in kw.iteritems():
            record[k] = v
        # if there is no index to update, stop here
        if not self.indices.keys():
            return
        # update index
        # get previous version of the record (same __id__)
        _id = record['__id__']
        try:
            old_rec = self.records[_id]
        except KeyError:
            raise KeyError,"No record with __id__ %s" %_id
        # change indices
        for indx in self.indices.keys():
            if old_rec[indx] == record[indx]:
                continue
            # remove id for the old value
            old_pos = bisect.bisect(self.indices[indx][old_rec[indx]],_id)-1
            del self.indices[indx][old_rec[indx]][old_pos]
            # insert new value
            bisect.insort(self.indices[indx].setdefault(record[indx],[]),_id)

    def _validate(self,k,v):
        """Check if key is valid and value has the appropriate type"""
        if not k in self.fields.keys():
            raise NameError,"No field named %s" %k
        if not isinstance(v,self.fields[k]):
            raise TypeError,"Bad type for %s : expected %s, got %s" \
                  %(k,self.fields[k].__name__,v.__class__.__name__)
    
    def __getitem__(self,num):
        """Direct access by record id"""
        return self.records[num]
        
    def __iter__(self):
        """Iteration on the records"""
        return self.records.itervalues()

if __name__ == '__main__':
    # test on a 1000 record base
    import random
    names = ['pierre','claire','simon','camille','jean',
                 'florence','marie-anne']
    db = Base('strakell_test')
    if os.path.exists('strakell_test'):
        os.remove('strakell_test')
    db.create(name=unicode,age=int,size=float)
    for i in range(1000):
        db.insert(name=unicode(random.choice(names)),
             age=random.randint(7,47),size=random.uniform(1.10,1.95))
    db.create_index('age')
    db.commit()
    raw_input()

    print 'Record #20 :',db[20]
    print '\nRecords with age=30 :'
    for rec in db.age[30]:
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    db.insert(name=unicode(random.choice(names))) # missing fields
    print '\nNumber of records with 30 <= age < 33 :',
    print sum(1 for r in db if 33 > r['age'] >= 30)

    d = db.delete(r for r in db if 32> r['age'] >= 30 and r['name']==u'pierre')
    print "\nDeleting %s records with name == 'pierre' and 30 <= age < 32" %d
    print '\nAfter deleting records '
    for rec in db.age[30]:
        print '%-10s | %2s | %s' %(rec['name'],rec['age'],round(rec['size'],2))
    print '\n',sum(1 for r in db),'records in the database'
    print '\nMake pierre uppercase for age > 27'
    for record in (r for r in db if r['name']=='pierre' and r['age'] >27) :
        db.update(record,name=u"Pierre")
    print len([r for r in db if r['name']==u'Pierre']),'Pierre'
    print len([r for r in db if r['name']==u'pierre']),'pierre'
    print len([r for r in db if r['name'] in [u'pierre',u'Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
    db.commit()
    db.open()
    print '\nSame operation after commit + open'
    print len([r for r in db if r['name']==u'Pierre']),'Pierre'
    print len([r for r in db if r['name']==u'pierre']),'pierre'
    print len([r for r in db if r['name'] in [u'pierre',u'Pierre']]),'p/Pierre'
    print 'is unicode :',isinstance(db[20]['name'],unicode)
