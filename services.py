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

domain = 'https://torrentkim10.net'
headers = {'User-Agent':'Mozilla/5.0'}

# 검색어 결과를 가져온다.

def searchFromTorrentKim(keyword, max=10):
    results = []
    url = domain + '/bbs/s.php?k='+keyword+'&b=&q='
    page = requests.get(url)
    bsObj = BeautifulSoup(page.text, "html.parser")
  
    try:
      siblings = bsObj.find('table', {'class':'board_list'}).tr.next_sibling
      for sibling in siblings.findNextSiblings()[1:]:
          magnet = (sibling.find('a', href=re.compile("^(javascript).*$")))['href'].replace("javascript:Mag_dn('",'').replace("')", '')
          magnet = "magnet:?xt=urn:btih:"+magnet
          title = (sibling.find('a', href=re.compile("^(\.\.).*$"))).text.strip()
          results.append({'title':title, 'magnet':magnet})

    except AttributeError as e:
      print("No data found")
    return results

# feed 상세페이지에서 magnet을 추출한다.
def magnetFromPage(url):
    url = domain + url 
    page = requests.get(url)
    bsObj = BeautifulSoup(page.text, "html.parser")
    magnet = bsObj.find('input', value=re.compile("^(magnet).*$")).get('value')
    return magnet


      
    
    
    
