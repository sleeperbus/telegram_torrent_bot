# -*- coding: utf-8 -*-
import requests
from requests.exceptions import ConnectionError
import logging
import log
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

domain_torrenthaja = "https://torrenthaja.com/bbs/"
logger = logging.getLogger('torrentbot')
if not logger:
    logger = log.setupCustomLogger('torrentbot', './torrentbot.log')


def parseTorrentHaja(keyword, max=10):
    """
    토렌트 하자 사이트 파싱
    """
    results = []
    url = domain_torrenthaja + "search.php?search_flag=search&stx=" + keyword
    page = requests.get(url)
    bsObj = BeautifulSoup(page.text, "html.parser")

    for torrentPage in bsObj.findAll('div', {'class': 'td-subject ellipsis'}):
        pageLink = torrentPage.find('a')['href'].replace('./', '')
        title = torrentPage.find('a').text
        results.append({'title': title, 'pageLink': pageLink})

    return results


def searchFromTorrentSite(keyword, max=5):
    """
    외부에 검색을 제공하는 함수
    """
    print(keyword)
    results = []
    items = parseTorrentHaja(keyword)

    with ThreadPoolExecutor(max_workers=max) as executor:
        future_to_magnet = {executor.submit(
            magnetSubPageTorrentHaja, item['pageLink']): item['title'] for item in items}

        for future in as_completed(future_to_magnet):
            title = future_to_magnet[future]
            magnet = future.result()
            if magnet:
                results.append({'title': title, 'magnet': magnet})

    return results


def magnetSubPageTorrentHaja(pageLink):
    """
    토렌트 하자 상세페이지에서 magnet을 추출한다.
    """
    if len(pageLink) == 0:
        return None
    url = domain_torrenthaja + pageLink
    tryCount = 0
    magnet = None
    while tryCount < 5:
        try:
            page = requests.get(url)
            bsObj = BeautifulSoup(page.text, "html.parser")
            magnet = bsObj.find('button', {'class': 'btn btn-success btn-xs'})[
                'onclick'].replace('magnet_link(', '').replace(');', '')
        except ConnectionError as E:
            logger.debug("page connection error: {0} at retry {1}".format(url, tryCount))
            tryCount += 1
        except TypeError as E:
            magnet = None
        except AttributeError as e:
            logger.error("can not find magnet link in page: %s" % url)
            magnet = None
        else:
            magnet = "magnet:?xt=urn:btih:" + magnet
    return magnet

