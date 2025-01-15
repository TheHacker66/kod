# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ilcorsaronero
# ------------------------------------------------------------

from core import support, httptools

host = support.config.get_channel_url()
support.info('HOST',host)
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    menu = [
        ('Film {film}', ['/cat/film', 'peliculas', [0, 'movie', True], 'undefined']),
        ('Serie TV', ['/cat/serie-tv', 'peliculas', [0 , 'tvshow', True], 'undefined']),
        ('Animazione', ['/cat/animazione', 'peliculas', [0 , 'anime', True], 'undefined']),
        ('Documentari', ['/cat/altro/documentari', 'peliculas', [0 , 'documentary', True], 'undefined']),
        ('Programmi TV', ['/cat/altro/programmi-tv', 'peliculas', [0 , 'tvshow', True], 'tvshow']),
        ('Video Musica', ['/cat/musica/video-musicali', 'peliculas', [0 , 'music', False], 'undefined']),
        ('Videocorsi', ['/cat/altro/videocorsi', 'peliculas', [0 , 'music', False], 'undefined'])
    ]
    search = ''

    return locals()

@support.scrape
def peliculas(item):
    debug = False
    action = 'findvideos'
    sceneTitle = item.args[2]    

    def itemHook(item):
        if not sceneTitle:
            item.title = item.title.replace('_', ' ')
            item.fulltitle = item.fulltitle.replace('_', ' ')
        item.title = support.scrapertools.decodeHtmlentities(support.urlparse.unquote(item.title))

        return item

    patron = r'<a class="hover:underline line-clamp-1.*?href="(?P<url>[^"]+)"\s*>(?P<title>.*?)</a>[^>]+>[^>]+>[^>]+>(?P<seed>.*?)<'
    patronNext = r'<a href="(?P<url>[^"]+)".*?Next</span>'
    return locals()

def search(item, text):
    item.url = "{}/search?{}".format(host, support.urlencode({'q': text}))
    item.args = 'search'

    try:
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []

def findvideos(item):
    if item.contentType == 'tvshow': item.contentType = 'episode'
    Videolibrary = True if 'movie' in item.args else False
    return support.server(item, support.match(item.url, patron=r'"(magnet[^"]+)').match, Videolibrary=Videolibrary)
