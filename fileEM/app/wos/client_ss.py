import os
import json
import requests

class s2Client(object):
    '''
    A client to query paper information through API.

    Methods:
    for external usage:
    queryPaperId : query one paper through id.
    for fileEM:
    queryPaperDOI : query one paper through doi.
    '''
    def __init__(self):
        self.S2_API_KEY = os.environ.get('S2_API_KEY', '')
        self.base_url = 'https://api.semanticscholar.org'
        self.headers  = {
                'X-API-KEY': self.S2_API_KEY,
                }

    def queryPaperId(self, id_paper, fields = 'paperId,externalIds'):
        url = self.base_url + f'/graph/v1/paper/{id_paper}'
        params = {
                'fields' : fields,
                }
        msg = requests.get(url, headers=self.headers, params=params)
        msg.raise_for_status()
        return msg.json()

    # For fileEM
    def queryPaperDOI(self, doi, fields = 'paperId,externalIds,title,authors,publicationVenue,abstract,s2FieldsOfStudy,journal,references'):
        url = self.base_url + f'/graph/v1/paper/DOI:{doi}'
        params = {
                'fields' : fields,
                }
        msg = requests.get(url, headers=self.headers, params=params)
        msg.raise_for_status()
        return msg.json()

    def queryPaperAuthor(self, id_paper, fields = 'authorId,name,aliases', offset = 0):
        url = self.base_url + f'/graph/v1/paper/{id_paper}/authors'
        params = {
                'fields' : fields,
                'offset' : offset,
                }
        authors = requests.get(url, headers=self.headers, params=params)
        authors.raise_for_status()
        return authors.json()

    def queryPaperReferences(self, id_paper, fields = 'contexts,intents,paperId,title', offset = 0, limit = 100):
        url = self.base_url + f'/graph/v1/paper/{id_paper}/references'
        params = {
                'fields' : fields,
                'offset' : offset,
                'limit'  : limit,
                }
        references = requests.get(url, headers=self.headers, params=params)
        references.raise_for_status()
        return references.json()
        
if __name__ == '__main__':
    client = s2Client()
    msg = client.queryPaperDOI('10.1017/jfm.2018.749')
    print(msg['references'])
