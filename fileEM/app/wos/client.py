from base64 import b64encode
from limit import limit
from functools import wraps
import logging
import suds

logging.getLogger('suds.client').setLevel(logging.CRITICAL)
Client = suds.client.Client

base_url = 'http://search.webofknowledge.com'
auth_url = base_url + '/esti/wokmws/ws/WOKMWSAuthenticate?wsdl'
search_url = base_url + '/esti/wokmws/ws/WokSearch?wsdl'
searchlite_url = base_url + '/esti/wokmws/ws/WokSearchLite?wsdl'

class sudsClient(type):
    '''
    Read the method from the url and set methods through the url.
    '''
    def __new__(cls, name, bases, attrs):
        if 'url' not in attrs.keys():
            raise Exception('The Client url is needed in attributes.')
        url = attrs['url']
        _client = Client(url, proxy=None, timeout=600)
        attrs['client'] = _client
        # Set the service
        # In this version, it will just record the methods.
        servicesdict = {}
        for service in _client.sd:
            _servicename = service.service.name
            servicedict  = {}
            # Get type list
            typelist     = []
            for _type in service.types:
                typelist.append(service.xlate(_type[0]))
            # Get method dict
            _methodsdict  = {}
            for port in service.ports:
                for method in port[1]:
                    attrdict = {}
                    for _attr in method[1]:
                        _attr_name = service.xlate(_attr[1])
                        attrdict[_attr[0]] = _attr_name
                        if _attr_name in typelist:
                            attrs[_attr_name] = _client.factory.create(_attr_name)
                    attrs[method[0]] = getattr(_client.service, method[0])
                    _methodsdict[method[0]] = attrdict
            servicedict['method'] = _methodsdict
            servicedict['type']   = typelist
            servicesdict[_servicename] = servicedict
        attrs['__services__'] = servicesdict
        return type.__new__(cls, name, bases, attrs)

class authClient(metaclass=sudsClient):
    url = auth_url
    def __init__(self, user:str=None, password:str=None, sid:str = None):
        # Copy from github.com/wos
        # Thanks for helping me understand how to connect to wos API.
        headers = {}
        if user and password:
            auth = '%s:%s' % (user, password)
            auth = b64encode(auth.encode('utf-8')).decode('utf-8')
            headers = {'Authorization': ('Basic %s' % auth).strip()}
            self.client.set_options(headers=headers)

class searchClient(metaclass=sudsClient):
    url = search_url
    def __init__(self, **kwargs):
        self.viewField_query  = self.client.factory.create('viewField')
        self.viewField_citing = self.client.factory.create('viewField')
        self.viewField_cited  = self.client.factory.create('viewField')
        self.sortField   = self.client.factory.create('sortField')
        self.editionDesc = self.client.factory.create('editionDesc')
        # Set the default settings of the search methods.
        # query Parameters of the search
        self.queryParameters.databaseId = 'WOS'
        self.queryParameters.queryLanguage = 'en'
        # Set sortField
        self.sortField.name = 'RS'
        self.sortField.sort = 'D'
        # Set retrieve Parameters
        self.viewField_query.collectionName = 'WOS'
        self.viewField_cited.collectionName = 'WOS'
        #  The field name in the wos client
        # UID, names, titles, identifiers, abstract, keywords, keywords_plus, subjects, conf_dates, conf_title, conf_host
        # organizations, sponsors, pub_info
        self.viewField_query.fieldName      = ['UID', 'pub_info', 'names', 'titles', 'identifiers', 'abstract', 'keywords_plus', 'subjects']
        self.viewField_cited.fieldName      = ['UID']
        # self.viewField_citing.fieldName      = ['UID', 'pub_info', 'names', 'titles', 'identifiers', 'abstract', 'keywords', 'subjects']
        # Set the retrieveParameters
        self.retrieveParameters.firstRecord = 1
        self.retrieveParameters.count       = 100
        self.retrieveParameters.sortField   = self.sortField
        # self.retrieveParameters.viewField = None # self.viewField_cite
        self.retrieveParameters.viewField = self.viewField_query

class wosClient(object):
    def __init__(self, sid_path, user:str=None, password:str=None):
        self.sid      = self.readsid(sid_path)
        self.sid      = self.sid.replace('\n', '')
        self.auth     = authClient(user, password, self.sid)
        self.search   = searchClient()
        # Set Sid Cookies
        self.auth.client.options.headers.update({'Cookie': 'SID="%s"'%self.sid})
        self.search.client.set_options(headers={'Cookie': 'SID="%s"'%self.sid})

    @staticmethod
    def readsid(path_sid):
        sid_f = open(path_sid, 'r')
        sid = sid_f.read()
        sid_f.close()
        return sid
    
    @staticmethod
    def writesid(sid, path_sid):
        sid_f = open(path_sid, 'w')
        sid_f.write(sid)
        sid_f.close()

    @staticmethod
    def throttle(func):
        throttle_wait = limit(3, 2)(lambda: True)
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            throttle_wait()
            return func(self, *args, **kwargs)
        return wrapper

    def connect(self):
        '''
        Authenticate to wos client and set sid cookie.
        '''
        self.sid = self.auth.authenticate()
        self.auth.client.options.headers.update({'Cookie': 'SID="%s"'%self.sid})
        self.search.client.options.headers.update(headers={'Cookie': 'SID="%s"'%self.sid})
        return self.sid

    @throttle
    def query(self, str_in:str):
        # self.search.retrieveParameters.viewField = self.search.viewField_query
        # self.search.queryParameters.userQuery = 'DO = %s'%DOI
        self.search.queryParameters.userQuery = str_in
        # print(self.search.queryParameters)
        try:
            _query = self.search.search(self.search.queryParameters, self.search.retrieveParameters)
        except suds.WebFault as wf:
            print('ERROR: %s'% wf.fault.faultstring)
            try:
                self.auth.authenticate()
                _query = self.search.search(self.search.queryParameters, self.search.retrieveParameters)
            except suds.WebFault as wf2:
                print('ERROR: %s'% wf2.fault.faultstring)
        return _query.records

    def querycite(self, UID):
        self.search.retrieveParameters.viewField = None
        def getcited():
            _query = self.search.citedReferences('WOS', UID, 'en', self.search.retrieveParameters)
            total_query = _query.recordsFound
            if total_query <= 100:
                return _query.references
            else:
                _loop = int(total_query/100)
                references = _query.references
                queryId    = _query.queryId
                first_record = 1
                for iloop in range(_loop):
                    first_record += 100
                    self.search.retrieveParameters.firstRecord = first_record
                    references += self.search.citedReferencesRetrieve(queryId, self.search.retrieveParameters)
                # Go back to 1
                self.search.retrieveParameters.firstRecord = 1
                return _query.references

        try:
            _query = getcited()
        except suds.WebFault as wf:
            try:
                self.auth.authenticate()
                _query = getcited()
            except suds.WebFault as wf2:
                print('ERROR: %s'% wf2.fault.faultstring)
                raise Exception
        self.search.retrieveParameters.viewField = self.search.viewField_query
        return _query
        
    # Update in future version with UI. I don't know what it can do now!
    # def queryciting(self, UID):
    #     self.search.retrieveParameters.viewField = None
    #     try:
    #         _query = self.search.citingArticles('WOS', UID, None, None, 'en', self.search.retrieveParameters)
    #     except suds.WebFault as wf:
    #         try:
    #             self.auth.authenticate()
    #             _query = self.search.citingArticles('WOS', UID, None, None, 'en', self.search.retrieveParameters)
    #         except suds.WebFault as wf2:
    #             print('ERROR: %s'% wf2.fault.faultstring)
    #     return _query

if __name__ == '__main__':
    a     = wosClient('sid')
    # query = 'DO=10.1146/annurev-fluid-122414-034550'
    query = 'TI="Prediction and investigation of the turbulent flow over a rotating disk" AND SO="JOURNAL OF FLUID MECHANICS"'
    # query = 'UT=000184104100015'
    # query = 'AU=Quadrio'
    b     = a.query(query)
    # b     = a.querycite('000368367800007') 
    print(a.search.queryParameters)
    # for c in b:
    #     print(c)