import os.path
import json

from bs4 import BeautifulSoup
import asyncio, aiohttp
from aiohttp import web

import logging
#logging.basicConfig(level=logging.DEBUG)

WP_DOMAIN = "http://en.wikipedia.org/wiki/"

topics = [
    'Mathematics',
    'Barack_Obama',
    'Daredevil',
    'Monsieur_Farty_Pants',
    'fhgjfds',
]

SAVE_DIR = 'tmp/'

# Saves html to file
def save_json(obj, filename):
    path = os.path.join(SAVE_DIR, filename)
#    print("Saving to "+path)
    with open(path, 'wt') as fp:
        json.dump(obj,fp)

# parse html and build save document
def parse(html):
    doc = {}
    page = BeautifulSoup(html)
    doc['title'] = page.find(id='firstHeading').get_text()
    doc['categories'] = [ li.a['href'].split('/')[2] for li in page.find(id='mw-normal-catlinks').find_all('li') ]
    doc['content'] = page.find(id='mw-content-text').get_text()
    return doc

@asyncio.coroutine
def get_page(session, url):
    html = None
    err = None
    resp = yield from session.get(url)
    if resp.status == 200:
        html = yield from resp.read()
    else:
        if resp.status == 404:
            err = web.HTTPNotFound
        else:
            err = aiohttp.HttpProcessingError(
                code=resp.status, message=resp.reason,
                headers=resp.headers)
    resp.close()
    if(err):
        raise err
    return html
    
@asyncio.coroutine
def download_page(session, title):
    try:
        html = yield from get_page(session, WP_DOMAIN + title)
        print('Completed download of: ' + title)
        document = parse(html)
        save_json(document, title.lower() + '.json')
    except web.HTTPNotFound as e:
        print('Topic not found at Wikipedia: ' + title)
    except Exception as e:
        print('Error:')
        print(e)
    return title


# asyncio driver 
def crawl(topics):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=100))
    schedule = [download_page(session,t) for t in topics]
    garcon = asyncio.wait(schedule)
    res, _ = loop.run_until_complete(garcon)
    session.close()
    loop.close()
    return len(res)


if __name__ == '__main__':
    crawl(topics)
