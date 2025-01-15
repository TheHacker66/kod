# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizione
# ------------------------------------------------------------


from core import httptools, support, tmdb, scrapertools
from platformcode import config, logger
import re

def findhost(url):
    host = support.match(url, patron=r'<h2[^>]+><a href="([^"]+)').match.rstrip('/')
    permUrl = httptools.downloadpage(host,  follow_redirects=False, only_headers=True).headers

    if 'location' in permUrl.keys(): # handle redirection
        return permUrl['location']
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    menu = [('Film',['/category/film/', 'peliculas', '', 'movie']),
            ('Film al cinema {submenu}',['/category/ora-al-cinema/', 'peliculas', '', 'movie']),
            ('Generi',['', 'genres', '', 'undefined']),
            ('Saghe',['', 'genres', 'saghe', 'undefined']),
            ('Serie TV',['/category/serie-tv/', 'peliculas', '', 'tvshow']),
            #('Aggiornamenti Serie TV', ['/aggiornamenti-serie-tv/', 'peliculas']) da fixare
            ]
    search = ''
    return locals()

@support.scrape
def genres(item):
    action = 'peliculas'
    blacklist = ['Scegli il Genere', 'Film', 'Serie Tv', 'Sub-Ita', 'Anime', "Non reperibile", 'Anime Sub-ITA', 'Prossimamente',]
    wantSaga = True if item.args == 'saghe' else False

    patronBlock = r'<div class=\"categories-buttons-container\"(?P<block>.*?)</div>'
    if not wantSaga: # se non richiedo le sage carico le icone in automatico
        patronMenu = r'<a href=\"(?P<url>https:\/\/.*?)\".*?>(?P<title>.*?)</a>'
    else: # mantengo l'icona del padre
        patron = r'<a href=\"(?P<url>https:\/\/.*?)\".*?>(?P<title>.*?)</a>'

    def itemlistHook(itemlist):
        itl = []
        for item in itemlist:
            isSaga = item.fulltitle.startswith('Saga')

            if len(item.fulltitle) != 3:
                if (isSaga and wantSaga) or (not isSaga and not wantSaga):
                    itl.append(item)
        return itl
    return locals()


def search(item, text):
    item.url = "{}/?{}".format(host, support.urlencode({'s': text}))
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []

@support.scrape
def peliculas(item):
    if not item.args == 'search': # pagination not works
        if not item.nextpage:
            item.page = 1
        else:
            item.page = item.nextpage

        if not item.parent_url:
            item.parent_url = item.url

        item.nextpage = item.page + 1
        nextPageUrl = "{}/page/{}".format(item.parent_url, item.nextpage)
        resp = httptools.downloadpage(nextPageUrl, only_headers = True)
        if (resp.code > 399): # no more elements
            nextPageUrl = ''
    else:
        action = 'check'

    patron= r'<article class=\"elementor-post.*?(<img .*?src=\"(?P<thumb>[^\"]+).*?)?<h1 class=\"elementor-post__title\".*?<a href=\"(?P<url>[^\"]+)\" >\s*(?P<title>[^<]+?)\s*(\((?P<lang>Sub-[a-zA-Z]+)*\))?\s*(\[(?P<quality>[A-Z]*)\])?\s*(\((?P<year>[0-9]{4})\))?\s+<'

    return locals()

def episodios(item):
    item.quality = ''
    data = item.data if item.data else httptools.downloadpage(item.url).data
    itemlist = []

    for it in support.match(data, patron=[r'div class=\"single-season.*?(?P<id>season_[0-9]+).*?>Stagione:\s(?P<season>[0-9]+).*?(\s-\s(?P<lang>[a-zA-z]+?))?<']).matches:
        block = support.match(data, patron = r'div id=\"'+ it[0] +'\".*?</div').match
        for ep in support.match(block, patron=[r'<li><a href=\"(?P<url>[^\"]+).*?img\" src=\"(?P<thumb>[^\"]+).*?title\">(?P<episode>[0-9]+)\.\s+(?P<title>.*?)</span>']).matches:
            itemlist.append(item.clone(contentType = 'episode',
                                   action='findvideos',
                                   thumb = ep[1],
                                   title = support.format_longtitle(support.cleantitle(ep[3]), season = it[1], episode = ep[2], lang= it[3]),
                                   url = ep[0], data = '')
                        )

    support.check_trakt(itemlist)
    support.videolibrary(itemlist, item)
    if (config.get_setting('downloadenabled')):
        support.download(itemlist, item)

    return itemlist

def check(item):
    item.data = httptools.downloadpage(item.url).data
    if 'season-details' in item.data.lower():
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        return findvideos(item)


def findvideos(item):
    video_url = item.url

    if item.contentType == 'movie':
        video_url = support.match(item, patron=[r'<div class="video-wrapper">.*?<iframe src=\"(https://.*?)\"',
                                                r'window.open\(\'([^\']+).*?_blank']).match
    if (video_url == ''):
       return []
    itemlist = [item.clone(action="play", url=srv) for srv in support.match(video_url, patron='<div class="megaButton" meta-type="v" meta-link="([^"]+).*?(?=>)>').matches]
    itemlist = support.server(item,itemlist=itemlist)

    return itemlist
