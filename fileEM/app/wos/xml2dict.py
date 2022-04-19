# Translate the information to dict.
from xml.etree import ElementTree as ET
from functools import partial
import re

def getTag(tag_in):
    tagtype   = re.compile(r'(?<=})\w+')
    tag_out   = tagtype.search(tag_in).group(0)
    return tag_out

def confirmDict(dict_in, dict_out, attr):
    if attr in dict_in.keys():
        dict_out[attr] = dict_in[attr]

def confirmDict_int(dict_in, dict_out, attr):
    if attr in dict_in.keys():
        dict_out[attr] = int(dict_in[attr])
        
def translateQuery(string):
    info = ET.fromstring(string)
    # Get the website
    webtype   = re.compile(r'https?[^}]*')
    website   = webtype.search(info.tag).group(0)
    web       = {'wos': website}
    # Get the basic Information
    REC          = info.find('wos:REC', web)
    static_data  = REC.find('wos:static_data', web)
    summary      = static_data.find('wos:summary', web)
    f_data       = static_data.find('wos:fullrecord_metadata', web)
    item         = static_data.find('wos:item', web)
    uid          = REC.find('wos:UID', web)
    dict_article = {}
    # Get pub_info
    pub_info = summary.find('wos:pub_info', web)
    dict_pub = pub_info.attrib
    for child in pub_info:
        dict_pub.update(child.attrib)

    # Get Title
    dict_titles = {}
    titles = summary.find('wos:titles', web)
    for title in titles:
        dict_titles[title.attrib['type']] = title.text

    # Get Author
    names = summary.find('wos:names', web)
    dict_authors = {}
    for name in names:
        if name.attrib['role'] == 'author':
            dict_author = {}
            dict_author['unique_id']  = int(name.attrib['daisng_id'])
            for child in name:
                if getTag(child.tag) in ['first_name', 'last_name', 'full_name']:
                    dict_author[getTag(child.tag)] = child.text
            dict_authors[dict_author['unique_id']] = dict_author

    # Get Keywords
    list_keywords = []
    try:
        keywords = item.find('wos:keywords_plus', web)
        for keyword in keywords:
            list_keywords.append(keyword.text)
    except:
        pass

    # Get abstract
    list_abstracts = []
    try:
        abstracts = f_data.find('wos:abstracts', web)
        for abstract in abstracts:
            text = abstract.find('wos:abstract_text', web)
            text = text.find('wos:p', web).text
            list_abstracts.append(text)
    except:
        pass

    # Return all the dictionary
    dict_article['uid'] = uid.text.replace('WOS:', '')
    # Pub info
    confirm_pub_int = partial(confirmDict_int, dict_pub, dict_article)
    confirm_pub_int('pubyear')
    confirm_pub_int('vol')
    confirm_pub_int('begin')
    confirm_pub_int('end')
    confirm_pub_int('page_count')

    # Titles and Journal
    dict_titles['journal'] = dict_titles.pop('source').replace('\'', '\'\'')
    dict_titles['title']   = dict_titles.pop('item').replace('\'', '\'\'')
    confirm_dict = partial(confirmDict, dict_titles, dict_article)
    confirm_dict('journal')
    confirm_dict('title')
    dict_titles.pop('title')

    # Authors
    index = 1
    nauthor = len(dict_authors.keys())
    dict_article['nauthor'] = nauthor
    for key in dict_authors.keys():
        dict_article['author%i'%index] = key
        index += 1

    # Keywords
    dict_article['keywords'] = ', '.join(list_keywords).replace('\'', '\'\'')

    # Abstract
    dict_article['abstract'] = ', '.join(list_abstracts).replace('\'', '\'\'')
    
    return dict_article, dict_authors, dict_titles

def translateCited(string):
    info = ET.fromstring(string)
    # Get the website
    webtype   = re.compile(r'https?[^}]*')
    website   = webtype.search(info.tag).group(0)
    web       = {'wos': website}
    REC       = info.find('wos:REC', web)
    # print(info)
    if REC is not None:
        uid       = REC.find('wos:UID', web)
        str_uid = uid.text.replace('WOS:', '')
        return str_uid
    else:
        return None
    
if __name__ == '__main__':
    a     = wosClient('sid')
    query = 'TI='
    # b     = a.query('10.1063/1.1586273') 
    b     = a.querycite('000368367800007') 
    # print(b)
    # translateQuery(len(b.references))
    tranlateCited(b)
