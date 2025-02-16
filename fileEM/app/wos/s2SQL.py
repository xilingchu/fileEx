from fileEM.sql.sqloper import operSQL
from fileEM.app.wos.s2client import s2Client

def sortYear(_list):
  return _list['Pubyear']

def tuple2var(tarlist, index:int=0):
    for i in range(len(tarlist)):
        tarlist[i] = tarlist[i][index]
    return tarlist

def artprint(dict_art, i, flag_abstract=True):
    # Print title the second column is title
    print('----------------------------------------------------------')
    print('(%i) Title  : %s'%(i, dict_art['Title']))
    print('Authors: %s'%(dict_art['Authors']))
    print('Pubyear: %s'%(dict_art['Pubyear']))
    print('Journal: %s'%(dict_art['Journal']))
    print('Fields : %s'%(dict_art['Fields']))
    if flag_abstract:
        print('Abstract: %s'%(dict_art['Abstract']))
    print('----------------------------------------------------------')
    print('----------------------------------------------------------')

class s2InsertOper(object):
    def __init__(self, sql_path:str):
        sql = type('sql', (operSQL,), {'config':sql_path})
        self.sql = sql()
        self.sql.create()
        
    def insertDB(self, doi, path):
        _client = s2Client()
        try:
            _query  = _client.queryPaperDOI(doi)
        except:
            raise Exception('Cannot find the paper in S2 database.')
        _id = _query['paperId']
        # _authors = _client.queryPaperAuthor(_id)['data']
        _authors = _query['authors']
        _venue   = _query['publicationVenue']
        # print(_query['abstract'])
        # If the article don't have publicationVenue
        if _venue == None:
            _venue = {}
            # Type the information by yourself
            _venue['type'] = input('If the type of type article is Journal?(Y/N)')
            if _venue['type'] == 'Y':
                _venue['type'] = 'journal'
                _journal_info  = _query['journal']
                _venue['id']   = _journal_info['name']
                _venue['name'] = _journal_info['name']
                _venue['alternate_names'] = _venue['name']
            else:
                _venue['type'] = None
        # Judge if that paper is an article paper.
        if _venue['type'] == 'journal':
            #------------- Insert Author -------------#
            # Insert author into table
            _authors_for_art = []
            for _author in _authors:
                # get the authors for article
                _authors_for_art.append(_author['authorId'])
                # Query if the Author in the table!
                _result = self.sql.query('Author', key=['authorId'],
                                        where={'authorId' : {'oper': '==', 'value': int(_author['authorId'])}})
                # Add author to the table
                if len(_result) != 0:
                    _author_list = self.sql.query('Author', key=['Name'],
                                            where={'authorId' : {'oper': '==', 'value': int(_author['authorId'])}})
                    _author_list = tuple2var(_author_list)[0]
                    if _author['name'] not in _author_list:
                        _author_list += ' | ' + _author['name']
                        _author_insert = {
                                'authorId': int(_author['authorId']),
                                'Name'    : _author_list, 
                                }
                        self.sql.insert('Author', **_author_insert)
                # if not!
                if len(_result) == 0:
                    # Get the author namelist
                    # _author_aliases = _author['aliases']
                    _author_list = _author['name']
                    _author_insert = {
                            'authorId': int(_author['authorId']),
                            'Name'    : _author_list, 
                            }
                    self.sql.insert('Author', **_author_insert)
            #------------ Insert Journal ------------#
            # Insert journal into journal paper
            # Query if the Author in the table!
            _result = self.sql.query('Journal', key=['Id'],
                                    where={'Id' : {'oper': '==', 'value': _venue['id']}})
            # if not!
            if len(_result) == 0:
                # Get the author namelist
                _journal_aliases = _venue['alternate_names']
                # _journal_list    = ' | '.join(_journal_aliases)
                _journal_insert = {
                        'Id'          : _venue['id'],
                        'Name'        : _venue['name'], 
                        'Alternative' : ','.join(_journal_aliases)
                        }
                self.sql.insert('Journal', **_journal_insert)
            #------------ Insert Article ------------#
            _result = self.sql.query('Journal_articles', key=['paperId'],
                                    where={'paperId' : {'oper': '==', 'value': _query['paperId']}})
            # Get the fields
            _field  = _query['s2FieldsOfStudy']
            _field_list = []
            for _ifield in _field:
                if _ifield['source'] == 's2-fos-model':
                    _field_list.append(_ifield['category'])
            _field  = ' | '.join(_field_list)
            # Get the authors
            _authors_for_art = ' | '.join(_authors_for_art)
            #### Risk1 No jorunal pages and vol
            try:
                _pages = _query['journal']['pages']
            except:
                _pages = '0'
            try:
                _vol   = int(_query['journal']['volume'])
            except:
                _vol = 0
            _article_dict = {
                        'paperId' : _query['paperId'],  
                        'title'   : _query['title'],
                        'fields'  : _field,
                        'pubyear' : int(_query['year']),
                        'pages'   : _pages,
                        'vol'     : _vol,
                        'journal' : _venue['id'],
                        'authors' : _authors_for_art,
                        'abstract': _query['abstract'],
                        'doi'     : doi,
                        'path'    : str(path), 
                        'nref'    : len(_query['references']),
                        }
            if _article_dict['abstract'] ==  None:
                _article_dict['abstract'] = 'None'
            self.sql.insert('Journal_articles', **_article_dict)
            #----------- Insert References -----------#
            # Create reference table
            self.createReferenceTable(_id)
            self.insertCitedTable(_id, _query['references'])

    def createReferenceTable(self, paperId):
        self.sql.c.execute(
                '''
                CREATE TABLE IF NOT EXISTS '%s' (
                paperId        varchar      UNIQUE NOT NULL,
                title          varchar      NOT NULL,
                FOREIGN KEY(paperId) REFERENCES Journal_articles(paperId) ON UPDATE CASCADE
                );'''%paperId)
        self.sql.conn.commit()

    def insertCitedTable(self, table, citedlist):
        for cited in citedlist:
            self.sql.c.execute('SELECT paperId from "%s" WHERE paperId == "%s";'%(table, cited['paperId']))
            result = self.sql.c.fetchall()
            if len(result) == 0:
                ###!!!!! have to use "" between paperid
                self.sql.c.execute('INSERT INTO "%s" (%s) VALUES (%s);'
                                   %(table, ', '.join(cited.keys()),
                                     ', '.join([f'"{value}"'for value in cited.values()])))
                print('Add paper %s into the table.'%(cited['title']))
                self.sql.conn.commit()

class s2QueryOper(object):
    def __init__(self, sql_path:str=None):
        sql = type('sql', (operSQL,), {'config':sql_path})
        self.sql = sql()
        self.sql.create()

    def query(self, **kwargs):
        def uid2name(authorId:int):
            _name = self.sql.query('Author', key = ['Name'],
                                   where = {'authorId':{'oper': '==', 'value': authorId}})
            _namelist = _name[0][0].split(' | ')
            # print(_namelist)
            return _namelist[-1]
            
        def jid2name(Id:str):
            _name = self.sql.query('Journal', key = ['Name'],
                                   where = {'Id':{'oper': '==', 'value': Id}})
            # print(_namelist)
            return _name[0][0]

        _where = {}
        # Select author from author table.
        if 'author' in kwargs.keys():
            #----------- Query The Author -----------#
            if type(kwargs['author']) != list:
                kwargs['author'] = [kwargs['author']]
            _id          = []
            for _author in kwargs['author']:
                _query_list = self.sql.query('Author', key=['authorId', 'Name'],
                                             where={'Name' : {'oper': 'LIKE', 'value': '%{}%'.format(_author)}})
                _id_list     = tuple2var(_query_list[:])
                _author_list = tuple2var(_query_list[:], 1)
                if len(_author_list) == 1:
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
                for i in range(len(_id)):
                    _id[i] = '%{}%'.format(_id[i]) 
                _where['authors'] = {'oper': 'LIKE', 'value' : _id}

        # Select journal from journal table.
        _journal = ''
        if 'journal' in kwargs.keys():
            _journal_list = self.sql.query('Journal', key=['Id', 'Name'],
                                           where={'Name' : {'oper': 'LIKE', 'value': '%{}%'.format(kwargs['journal'])}})
            _journal_list_2    = tuple2var(_journal_list[:])
            _journal_name_list = tuple2var(_journal_list[:], 1)
            if len(_journal_list) == 1:
                _journal = _journal_list_2[0]
            elif len(_journal_list) > 1:
                print('Which Jornal do you wanna select?[1-{}]'.format(len(_journal_list)))
                count = 0
                for name in _journal_name_list:
                    count += 1
                    print('{}. {}'.format(count, name))
                num_id = int(input('Please choose the number:'))
                _journal = _journal_list_2[num_id]
            else:
                print('Database doesn\'t have this journal.')
            if _journal != '':
                _where['journal'] = {'oper': '==', 'value': _journal}

        # Change the kwargs to where dict
        if 'fields' in kwargs.keys():
            if type(kwargs['fields']) is list:
                for i in range(len(kwargs['fields'])):
                    kwargs['fields'][i] = '%{}%'.format(kwargs['fields'][i])
            else:
               kwargs['fields'] = '%{}%'.format(kwargs['fields'])
            _where['fields'] =  {'oper': 'LIKE', 'value' : kwargs['fields']}
        if 'title' in kwargs.keys():
            if type(kwargs['title']) is list:
                for i in range(len(kwargs['title'])):
                    kwargs['title'][i] = '%{}%'.format(kwargs['title'][i])
            else:
               kwargs['title'] = '%{}%'.format(kwargs['title'])
            _where['title'] =  {'oper': 'LIKE', 'value' : kwargs['title']}
        if 'pubyear' in kwargs.keys():
            _where['pubyear'] =  {'oper': 'BETWEEN', 'value' : kwargs['pubyear']}
        _query_list = ['paperId', 'authors', 'title', 'journal', 'pubyear', 'abstract', 'fields', 'path']
        # The list of where is none or not.
        if _where == {}:
            print('Nothing to search!')
            return []
        _query_info = self.sql.query('Journal_articles', key=_query_list,
                                    where=_where, order=['journal', 'pubyear'])
        # Get the dict of the sql query
        _query_list = []
        for _item in _query_info:
            info_dict = {}
            info_dict['uid'] = _item[0]
            _str_author      = _item[1]
            _author_list     = _str_author.split(' | ')
            _author_name     = []
            for _author in _author_list:
                _author_name.append(uid2name(int(_author)))
            info_dict['Authors']  = '; '.join(_author_name)
            info_dict['Title']    = _item[2]
            info_dict['Journal']  = jid2name(_item[3])
            info_dict['Pubyear']  = _item[4]
            info_dict['Abstract'] = _item[5]
            info_dict['Fields']   = _item[6]
            info_dict['Path']     = _item[7]
            _query_list.append(info_dict)
        _query_list.sort(key=sortYear)
        return _query_list

if __name__ == '__main__':
    sql_path = '/home/xlc/projects/fileEm/fileEM/config/wos/wos.yaml'
    # s2c = s2InsertOper(sql_path)
    s2q = s2QueryOper(sql_path)
    qu  = s2q.query  (author = 'qu')
    print(qu)
    # s2c.insertDB('10.1017/jfm.2018.749', '')
    # s2c.query()
