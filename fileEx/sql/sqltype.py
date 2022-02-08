from fileEx.utils.utils import indent
# The class of the Element in sql
class sqlElement(object):
    def __init__(self, **kwargs):
        if 'elementType' and 'elementName' and 'columnName' not in list(kwargs.keys()):
            raise Exception('The element type, element name and column name is must in the SQL element.')

        if kwargs['elementType'] == 'str':
            _type = str
        elif kwargs['elementType'] == 'int':
            _type = int
        elif kwargs['elementType'] == 'float':
            _type = float
        else:
            raise Exception('The type of Element %s maybe wrong!'%kwargs['elementName'])

        self.__elementType__ = _type
        self.__elementName__ = kwargs['elementName']
        self.__columnName__  = kwargs['columnName']

        if 'foreignKey' in kwargs.keys():
            self.__foreignKey__  = kwargs['foreignKey']

        try:
            self.__otherWords__  = kwargs['otherKW']
        except:
            self.__otherWords__  = ''

    def __str__(self, _indent:int=0):
        return indent(_indent) + 'Element: %s-%s' % (str(self.__elementType__), self.__elementName__)

class sqlTable(object):
    def __init__(self, **kwargs):
        # The table name is must in the keywords.
        if 'tableName' not in list(kwargs.keys()):
            raise Exception('The table name is must in the SQL table.')
        self.__tableName__ = kwargs['tableName']
        kwargs.pop('tableName')
        self.elementlist = []
        self.nelementlist = []
        for key, value in kwargs.items():
            if 'nargs' in value:
                setattr(self, 'n'+key, sqlElement(**{'elementType':'int', 'elementName':'n'+value['elementName'], 'columnName':'INT'}))
                self.elementlist.append('n'+key)
                self.nelementlist.append(key)
                for _nkey in range(int(value['nargs'])):
                    value['elementName'] += '%i' % (_nkey+1)
                    setattr(self, key+'%i'%(_nkey+1), sqlElement(**value))
                    self.elementlist.append(key+'%i'%(_nkey+1))
                    value['elementName'] = value['elementName'].replace('%i' % (_nkey+1), '')
            else:
                setattr(self, key, sqlElement(**value))
                self.elementlist.append(key)

    def __str__(self, _indent:int=0):
        _str  = indent(_indent) + 'Table: %s'%(self.__tableName__)
        for element in self.elementlist:
            _str += getattr(self, element).__str__(_indent+1)
        return _str

    def _check_element(self, key, value):
        def _check_element_value(value):
            # Judge if the type of the element is correct
            if type(value) != _element.__elementType__:
                raise Exception('ERROR: The insert type is not correct in the table!')
            if type(value) == str:
                _value = '\'%s\''%(value)
            else:
                _value = str(value)
            return _value

        # Judge if the element in the table
        if key not in self.elementlist:
            print('Warining: The key %s is not in the table'%(key))
            print(self.elementlist)
            return None, None
        _element = getattr(self, key)
        _key = _element.__elementName__
        if type(value) == list:
            _value = []
            for item in value:
                item = _check_element_value(item)
                _value.append(item)
        else:
            _value = _check_element_value(value)
        return _key, _value

    def _check_keys(self, keylist:list):
        # Judge if the element in the table
        for key in keylist:
            if key not in self.elementlist:
                print('Warining: The key %s is not in the table'%(key))
                print(self.elementlist)
                keylist.remove(key)
        return keylist

        

class sqlDB(object):
    def __init__(self, **kwargs):
        # The table name is must in the keywords.
        if 'dbName' not in list(kwargs.keys()):
            raise Exception('The database name is must in the SQL database.')
        self.__dbName__ = kwargs['dbName']
        kwargs.pop('dbName')
        self.tablelist = []
        for key, value in kwargs.items():
            setattr(self, key, sqlTable(**value))
            self.tablelist.append(key)

    def _check_table(self, table:str):
        if table not in self.tablelist:
            print(self.tablelist)
            raise Exception('ERROR: The table %s is not exist in Tablelist.'%(table))

    def __str__(self):
        _str  = 'Database: %s'%(self.__dbName__)
        for table in self.tablelist:
            _str += getattr(self, table).__str__(1)
        return _str
        
if __name__ == '__main__':
    test_key = {'dbName':'dbtest', 'tabletest':{'tableName': 'testtable', 'test':{'elementType':'int', 'elementName':'test', 'columnName': 'str'}}}
    test_key2 = {'elementType':'int', 'elementName':'test', 'columnName': 'str'}
    test_key3 = {'tableName': 'testtable', 'test':{'elementType':'int', 'elementName':'test', 'columnName': 'str'}}
    a = sqlDB(**test_key)
    b = sqlElement(**test_key2)
    c = sqlTable(**test_key3)
    print(a)
