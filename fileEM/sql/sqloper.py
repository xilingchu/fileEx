from fileEM.sql.sqltype import sqlDB
from fileEM.utils.path import path
import sqlite3 as sql
import yaml
import sys

class metaSql(type):
    def __new__(cls, name, bases, attrs):
        if name == 'operSQL':
            return type.__new__(cls, name, bases, attrs)
        if 'config' not in attrs.keys():
            raise Exception('Config file is needed in attributes.')
        _config_file = path(attrs['config'])
        _config = open(_config_file, 'r')
        _config = yaml.load(_config, Loader=yaml.FullLoader)
        attrs['db'] = sqlDB(**_config)
        return type.__new__(cls, name, bases, attrs)


class operSQL(metaclass=metaSql):
    def __init__(self):
        filename      = self.db.__dbName__
        self.conn     = sql.connect(filename)
        self.c        = self.conn.cursor()
        print('Open {} successfully'.format(filename))

    def sqlExit(self):
        self.conn.close()

    # Decorator
    @staticmethod
    def _commit(func):
        def wrapper(self, *args, **kwargs):
            _commit = func(self, *args, **kwargs)
            _commit += ';'
            # print(_commit)
            # print(_commit)
            self.c.execute(_commit)
            self.conn.commit()
        return wrapper

    @staticmethod
    def _order(func):
        def wrapper(self, table, **kwargs):
            # 'order' will be a list which contains keys you wanna ordered.
            if 'order' in kwargs.keys():
                self.db._check_table(table)
                _table = getattr(self.db, table)
                _order = kwargs['order']
                _str_order = ' ORDER BY '
                orderlist  = _table._check_keys(_order)
                _str_order += ','.join(orderlist)
                kwargs.pop('order')
                return func(self, table, **kwargs)+_str_order
            else:
                return func(self, table, **kwargs)
        return wrapper

    @staticmethod
    def _where(flag:bool):
        def decorator(func):
            def wrapper(self, table, **kwargs):
                if flag == True:
                    if 'where' not in kwargs.keys():
                        print('Warning: If you don\'t enter where may cause severe outcomes.') 
                        no = input('Press n/N to stop, and press any other key to continue...')
                        if no.lower() == 'n':
                            sys.exit()
                # 'where' will be a dict which contains:
                # key: str    -- The element in the table
                # oper: str   -- The operator in the where
                # value: list -- The value in the where
                if 'where' in kwargs.keys():
                    self.db._check_table(table)
                    _table = getattr(self.db, table)
                    _where = kwargs['where']
                    _str_where = ' WHERE '
                    wherelist  = []
                    for key, value in _where.items():
                        if 'n' + key in _table.elementlist:
                            nkey      = getattr(_table, 'n'+key).__nargs__
                            _key, _value = _table._check_element(key+'1', value['value'])
                            _key = _key[:-1]
                            if type(_value) is not list:
                                _value = [_value]
                            for svalue in _value:
                                nkey_list = []
                                for i in range(nkey):
                                    nkey_list.append('%s %s %s'%(_key+str(i+1), value['oper'], svalue))
                                str_nkey = '( %s )'%(' OR '.join(nkey_list))
                                wherelist.append(str_nkey)
                        else:
                            _key, _value = _table._check_element(key, value['value'])
                            if type(_value) is not list:
                                _value = [_value]
                            if value['oper'].lower() == 'between':
                                wherelist.append('%s %s %s'%(_key, value['oper'], ' AND '.join(_value)))
                            if value['oper'].lower() == 'in':
                                wherelist.append('%s %s (%s)'%(_key, value['oper'], *_value))
                            else:
                                wherelist.append('%s %s %s'%(_key, value['oper'], ' AND '.join(_value)))
                    _str_where += ' AND '.join(wherelist)
                    kwargs.pop('where')
                    return func(self, table, **kwargs)+_str_where
                else:
                    return func(self, table, **kwargs)
            return wrapper
        return decorator

    # Operation
    def create(self):
        for table in  self.db.tablelist:
            _table = getattr(self.db, table)
            create_str = 'CREATE TABLE IF NOT EXISTS %s ( \n' % (_table.__tableName__)
            _element_list = []
            _foreign_list = []
            for element in _table.elementlist:
                _element = getattr(_table, element)
                _element_list.append('%s %s %s' % (_element.__elementName__, _element.__columnName__, _element.__otherWords__))
                if hasattr(_element, '__foreignKey__'):
                    _key_info = _element.__foreignKey__
                    _foreign_list.append('FOREIGN KEY(%s) REFERENCES %s(%s) ON UPDATE CASCADE'
                                        % (_element.__elementName__, _key_info['table'], _key_info['name']))
            if hasattr(_table, '__constrain__'):
                constrain = 'UNIQUE(%s)'%', '.join(_table.__constrain__)
                _element_list.append(constrain)
            create_str += ',\n'.join(_element_list+_foreign_list)
            create_str += ');'
            # print('Table %s are created!'%(_table.__tableName__))
            # print(create_str)
            self.c.execute(create_str)
            self.conn.commit()

    @_commit
    def insert(self, table, **kwargs):
        self.db._check_table(table)
        _table = getattr(self.db, table)
        table  = _table.__tableName__
        keylist   = []
        valuelist = []
        for key, value in kwargs.items():
            _key, _value = _table._check_element(key, value)
            if _key is not None:
                keylist.append(_key)
                valuelist.append(_value)
        _str_insert = 'INSERT OR REPLACE INTO %s(%s) VALUES (%s)'%(table, ','.join(keylist), ','.join(valuelist))
        # return _str_insert
        # print(_str_insert)
        self.c.execute(_str_insert)
        self.conn.commit()
        return _str_insert

    @_commit
    @_where(True)
    def update(self, table, **kwargs):
        self.db._check_table(table)
        _table = getattr(self.db, table)
        table  = _table.__tableName__
        updatelist = []
        for key, value in kwargs.items():
            _key, _value = _table._check_element(key, value)
            if _key is not None:
                updatelist.append('%s=%s'%(_key, _value))        
        _str_update = 'UPDATE %s SET %s'%(table, ','.join(updatelist))
        return _str_update

    @_commit
    @_where(True)
    def delete(self, table, **kwargs):
        self.db._check_table(table)
        _table = getattr(self.db, table)
        table  = _table.__tableName__
        _str_delete = 'DELETE FROM %s'%(table)
        return _str_delete

    @_commit
    @_order
    @_where(False)
    def select(self, table, **kwargs):
        self.db._check_table(table)
        _table = getattr(self.db, table)
        table  = _table.__tableName__
        if 'key' not in kwargs:
            _str_select = 'SELECT * FROM %s'%(table)
        else:
            # keylist = _table._check_keys(kwargs['key'])
            _str_select = 'SELECT %s FROM %s' % (','.join(kwargs['key']), table)
        return _str_select

    def query(self, table, **kwargs):
        self.select(table, **kwargs)
        return self.c.fetchall()
