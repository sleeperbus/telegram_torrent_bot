#-*- coding: utf-8 -*-
# import feedparser

# # 토렌트 검색을 지원하는 사이트
# def searchFromTorrentKim(keyword, max=10):
#   url = 'https://torrentkim1.net/bbs/rss.php?k=' 
#   result = []
#   d = feedparser.parse(url + keyword) 
#   for entry in d.entries[0:max]:
#     result.append({'title': entry.title, 'magnet': entry.link})
#   return result
      

# feedparser 로 정상적으로 파싱이 되지 않아 BeautifulSoup 을 사용      
import requests
from bs4 import BeautifulSoup
import re
import pprint

domain_torrenthaja = "https://torrenthaja.com/bbs/"

headers = {'User-Agent':'Mozilla/5.0'}

# 검색어 결과를 가져온다.

# def searchFromTorrentKim(keyword, max=10):
#     results = []
#     url = domain_torrentkim + '/bbs/s.php?k='+keyword+'&b=&q='
#     domain_torrenthaja = 
#     page = requests.get(url)
#     bsObj = BeautifulSoup(page.text, "html.parser")
  
#     try:
#       siblings = bsObj.find('table', {'class':'board_list'}).tr.next_sibling
#       for sibling in siblings.findNextSiblings()[1:]:
#           magnet = (sibling.find('a', href=re.compile("^(javascript).*$")))['href'].replace("javascript:Mag_dn('",'').replace("')", '')
#           magnet = "magnet:?xt=urn:btih:"+magnet
#           title = (sibling.find('a', href=re.compile("^(\.\.).*$"))).text.strip()
#           results.append({'title':title, 'magnet':magnet})

#     except AttributeError as e:
#       print("No data found")
#     return results

def searchFromTorrentSite(keyword, max=10):
  results = []
  url = domain_torrenthaja + "search.php?search_flag=searchcse&stx="+keyword
  page = requests.get(url) 
  bsObj = BeautifulSoup(page.text, "html.parser")
  for torrentPage in bsObj.findAll('div', {'class':'td-subject ellipsis'}):
    pageLink = torrentPage.find('a')['href'].replace('./','')
    title = torrentPage.find('a').text 
    magnet = magnetSubPageTorrentHaja(pageLink)
    if(magnet):
      results.append({'title': title, 'magnet':magnet})
  return results

# 상세페이지에서 magnet을 추출한다.
def magnetSubPageTorrentHaja(pageLink):
    url = domain_torrenthaja + pageLink
    page = requests.get(url)
    bsObj = BeautifulSoup(page.text, "html.parser")
    try:
      magnet = bsObj.find('button', {'class': 'btn btn-success btn-xs'})['onclick'].replace('magnet_link(','').replace(');','')
      magnet = "magnet:?xt=urn:btih:"+magnet
      return magnet
    except AttributeError as e:
      return None



      
    
    
    
