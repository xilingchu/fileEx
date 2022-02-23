from fileEx.sql.sqloper import operSQL
from fileEx.app.wos.client import wosClient
from fileEx.app.wos.xml2dict import translateQuery, translateCited
from fileEx.utils.path import path
from pathlib import Path
import sqlite3
import time
import yaml

def tuple2var(tarlist, index:int=0):
    for i in range(len(tarlist)):
        tarlist[i] = tarlist[i][index]
    return tarlist

def artprint(dict_art, flag_abstract=True):
    # Print title the second column is title
    print('----------------------------------------------------------')
    print('Title: %s'%(dict_art['Title']))
    print('Authors: %s'%(dict_art['Authors']))
    print('Pubyear: %s'%(dict_art['Pubyear']))
    print('Journal: %s'%(dict_art['Journal']))
    print('Keywords: %s'%(dict_art['Keywords']))
    if flag_abstract:
        print('Abstract: %s'%(dict_art['Abstract']))
    print('----------------------------------------------------------')
    print('----------------------------------------------------------')

class wosOper(object):
    def __init__(self, sid_path:str=None, sql_path:str=None, user:str=None, password:str=None):
        if 'user' and 'password' is not None:
            self.wos = wosClient(path(sid_path), user, password)
        else:
            self.wos = wosClient(path(sid_path))
        sql = type('sql', (operSQL,), {'config':sql_path})
        self.sql = sql()
        self.sql.create()

    def insert(self, doi, path):
        _query = 'DO="%s"'%doi
        query = self.wos.query(_query)
        dict_article, dict_authors, dict_journal = translateQuery(query)
        uid   = dict_article['uid']
        dict_article['doi']  = doi
        dict_article['path'] = str(Path(path).resolve().expanduser())
        # Import author
        for key, value in dict_authors.items():
            # Query author before import it
            result = self.sql.query('Author', key=['unique_id'], where={'unique_id' : {'oper': '==', 'value': key}})
            if len(result) == 0:
                self.sql.insert('Author', **value)
        # Import journal
        # Query Journal before insert it.
        result = self.sql.query('Journal', key=['journal'], where={'journal' : {'oper': '==', 'value': dict_journal['journal']}})
        if len(result) == 0:
            self.sql.insert('Journal', **dict_journal)
        # Import article
        result = self.sql.query('Article', key=['uid'], where={'uid' : {'oper': '==', 'value': dict_article['uid']}})
        if len(result) == 0:
            self.sql.insert('Article', **dict_article)
        self.getCited(uid)
        self.updateLink(uid)

    def query(self, **kwargs):
        def uid2name(uid):
            fname = self.sql.query('Author', key = ['full_name'], where = {'unique_id':{'oper': '==', 'value': uid}})
            return fname[0][0]
            
        where = {}
        # Select author from author table.
        if 'author' in kwargs.keys():
            if type(kwargs['author']) != list:
                kwargs['author'] = [kwargs['author']]
            _id          = []
            for _author in kwargs['author']:
                _query_list = self.sql.query('Author', key=['unique_id', 'full_name'], where={'full_name' : {'oper': 'LIKE', 'value': '%{}%'.format(_author)}})
                _id_list     = tuple2var(_query_list[:])
                _author_list = tuple2var(_query_list[:], 1)
                if len(_author_list) == 1:
                    print(_author_list[0])
                    _id.append(_id_list[0])
                elif len(_author_list) > 1:
                    print('Which author do you wanna select?[1-{}]'.format(len(_author_list)))
                    count = 0
                    for name in _author_list:
                        count += 1
                        print('{}. {}'.format(count, name))
                    num_id = int(input('Please choose the number:'))
                    print(_author_list[num_id-1])
                    _id.append(_id_list[num_id-1])
                else:
                    print('Database doesn\'t have this author.')
            if _id != []:
                where['author'] = {'oper': '==', 'value' : _id}

        # Select journal from journal table.
        if 'journal' in kwargs.keys():
            _journal_list = self.sql.query('Journal', key=['journal'], where={'journal' : {'oper': 'LIKE', 'value': '%{}%'.format(kwargs['journal'])}})
            _journal_list = tuple2var(_journal_list)
            _journal = ''
            if len(_journal_list) == 1:
                _journal = _journal_list[0]
            elif len(_journal_list) > 1:
                print('Which Jornal do you wanna select?[1-{}]'.format(len(_journal_list)))
                count = 0
                for name in _journal_list:
                    count += 1
                    print('{}. {}'.format(count, name))
                num_id = int(input('Please choose the number:'))
                _journal = _journal_list[num_id-1]
            else:
                print('Database doesn\'t have this journal.')
            if _journal != '':
                where['journal'] = {'oper': '==', 'value': _journal}

        # Change the kwargs to where dict
        if 'keywords' in kwargs.keys():
            if type(kwargs['keywords']) is list:
                for i in range(len(kwargs['keywords'])):
                    kwargs['keywords'][i] = '%{}%'.format(kwargs['keywords'][i])
            else:
               kwargs['keywords'] = '%{}%'.format(kwargs['keywords'])
            where['keywords'] =  {'oper': 'LIKE', 'value' : kwargs['keywords']}
        if 'title' in kwargs.keys():
            if type(kwargs['title']) is list:
                for i in range(len(kwargs['title'])):
                    kwargs['title'][i] = '%{}%'.format(kwargs['title'][i])
            else:
               kwargs['title'] = '%{}%'.format(kwargs['title'])
            where['title'] =  {'oper': 'LIKE', 'value' : kwargs['title']}
        if 'pubyear'  in kwargs.keys():
            where['pubyear'] =  {'oper': 'BETWEEN', 'value' : kwargs['pubyear']}
        query_list = ['uid', 'author', 'title', 'journal', 'pubyear', 'abstract', 'keywords']
        query_info = self.sql.query('Article', key=query_list,
                                    where=where, order=['journal', 'pubyear'])
        # Get the dict of the sql query
        query_list = []
        for item in query_info:
            info_dict = {}
            info_dict['uid'] = item[0]
            nauthor = item[1]
            author_list = []
            for i in range(int(nauthor)):
                author_list.append(uid2name(item[2+i]))
            info_dict['Authors']  = '; '.join(author_list)
            info_dict['Title']    = item[12]
            info_dict['Journal']  = item[13]
            info_dict['Pubyear']  = item[14]
            info_dict['Abstract'] = item[15]
            info_dict['Keywords'] = item[16]
            query_list.append(info_dict)
        return query_list

    def createCitedTable(self, uid):
        self.sql.c.execute(
                '''
                CREATE TABLE IF NOT EXISTS '%s'(
                UID            varchar      UNIQUE NOT NULL,
                Title          varchar      NOT NULL,
                Journal        varchar      NOT NULL,
                FOREIGN KEY(UID) REFERENCES Article(UID) ON UPDATE CASCADE,
                FOREIGN KEY(Journal) REFERENCES Journal(Journal) ON UPDATE CASCADE
                );'''%uid)

    def insertCitedTable(self, table, citedlist):
        for cited in citedlist:
            self.sql.c.execute('SELECT UID from "%s" WHERE UID == %s;'%(table, cited['UID']))
            result = self.sql.c.fetchall()
            if len(result) == 0:
                self.sql.c.execute('INSERT INTO "%s" (%s) VALUES (%s);'%(table, ', '.join(cited.keys()), ', '.join(cited.values())))
                print('Add paper %s into the table.'%(cited['Title']))
                self.sql.conn.commit()

    def getCited(self, uid):
        cited = self.wos.querycite(uid)
        cite_total = len(cited)
        self.wos.search.retrieveParameters.viewField = self.wos.search.viewField_cited
        list_cites = []
        cite_number = 0
        for cite in cited:
            if hasattr(cite, 'citedTitle') and hasattr(cite, 'citedWork'):
                time.sleep(0.5)
                _query = 'TI="%s" AND SO="%s"' % (cite.citedTitle, cite.citedWork)
                _result = self.wos.query(str(_query))
                _uid     = translateCited(_result)
                if _uid is not None:
                    cite_number += 1
                    dict_cite = {}
                    dict_cite['UID']     = '\'%s\''%_uid
                    dict_cite['Title']   = '\'%s\''%cite.citedTitle
                    dict_cite['Journal'] = '\'%s\''%cite.citedWork
                    list_cites.append(dict_cite)
        print('Add cited papers %i/%i!'%(cite_number, cite_total))
        self.createCitedTable(uid)
        self.insertCitedTable(uid, list_cites)
        self.wos.search.retrieveParameters.viewField = self.wos.search.viewField_query

    def updateLink(self, uid):
        _result_article = self.sql.query('Article', key = ['uid'])
        _result_article = tuple2var(_result_article)
        self.sql.c.execute('SELECT UID FROM "%s";'%uid)
        # Find cited article in the list
        _result_cite    = tuple2var(self.sql.c.fetchall())
        set_cited = set(_result_article).intersection(_result_cite)
        for cite in set_cited:
            result = self.sql.query('Link', article=uid, citedarticle=cite)
            if len(result) == 0:
                self.sql.insert('Link', article=uid, citedarticle=cite)
        # Find citing article in the list
        for i in _result_article:
            self.sql.c.execute('SELECT UID FROM "%s" WHERE UID == "%s";'%(i, uid))
            result = self.sql.c.fetchall()
            if len(result) == 1:
                result = self.sql.query('Link', article=i, citedarticle=uid)
                if len(result) == 0:
                    self.sql.insert('Link', article=i, citedarticle=uid)

if __name__ == '__main__':
    a = wosOper('config.yaml')
    # a.insert('10.1063/1.1586273', 'test')
    # a.insert('10.1017/S0022112087000892', 'test')
    a.insert('10.1063/1.4819144', 'test')
    a.query(author=['kim', 'moser'])
    artprint(a.query(journal='fluid')[0])
    # b = a.getCited('000184104100015')
