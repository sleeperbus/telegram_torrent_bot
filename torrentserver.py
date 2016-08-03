#-*- coding: utf-8 -*- 
import logging
import os
from pprint import pprint
from time import sleep


# Deluge server
class deluge:
  def __init__(self):
    self.logger = logging.getLogger('torrentserver')
    self.logger.debug('deluge logger init')
    pass 

  def reboot(self):
    if self.isAlive(): 
      self.logger.warn('server still alive, killing forcibly')
      os.system("ps ax | grep -vw grep | grep deluged | awk '{print $1}' | xargs kill -9")

    self.logger.info('execute deluge')
    os.system("deluged")
    self.logger.info('deluge check files')
    os.system("deluge-console 'recheck *'")
    self.logger.info('deluge resume files')
    os.system("deluge-console 'resume *'")

  def restart(self):
    if self.isAlive(): 
      self.logger.warn('server still alive, killing forcibly')
      os.system("ps ax | grep -vw grep | grep deluged | awk '{print $1}' | xargs kill -9") 

    self.logger.info('execute deluge')
    os.system("deluged")

  def isAlive(self):
    self.logger.debug('in isAlive')
    command = 'ps ax | grep -vw grep | grep deluged'
    results = os.popen(command).read()
    if len(results) > 0: 
      self.logger.debug('server alive')
      return True 
    else:
      self.logger.debug('server dead')
      return False
  
  # add magnet return hash id
  def add(self, magnet): 
    if not self.isAlive(): 
      self.logger.warn('before adding torrent, find server down, will restart')
      self.restart() 

    command = "deluge-console add " + magnet 
    befTorrents = self.ongoing()
    befTorrents = [{'title': t['title'], 'id':t['id']} for t in befTorrents]
    os.system(command)
    sleep(1)
    afTorrents = self.ongoing()
    afTorrents = [{'title': t['title'], 'id':t['id']} for t in afTorrents]
    newone = [x for x in afTorrents if x not in befTorrents]
    if len(newone) >= 1:
      torrentInfo = newone[0]
      return torrentInfo
    else: return None
        
  # delete torrent using hash id
  def delete(self, id):
    if not self.isAlive(): 
      self.logger.warn('before deleting torrent, find server down, will restart')
      self.restart() 

    command = "deluge-console rm " + id
    os.system(command)
  
  # return torrent download status
  def ongoing(self):
    if not self.isAlive(): 
      self.logger.warn('before checking torrent, find server down, will restart')
      self.restart() 

    command = "deluge-console info"
    info = os.popen(command).read()
    return self.parse(info)

  # deluge-console info id
  def torrentInfoStr(self, id):
    if not self.isAlive(): 
      self.logger.warn('before checking torrent, find server down, will restart')
      self.restart() 

    command = "deluge-console info " + id
    info = os.popen(command).read()
    return info

  # return torrent info as type of dict
  def torrentInfo(self, id):
    if not self.isAlive(): 
      self.logger.warn('before checking torrent, find server down, will restart')
      self.restart() 

    command = "deluge-console info " + id
    info = os.popen(command).read() 
    return self.parse(info)[0] if len(info) != 0 else None

  # return torrents completed
  def completed(self):
  	torrents = self.ongoing()
	torrents = [t for t in torrents if t['state'] == 'seeding']
	return torrents
 
  # parse deluge-console info
  def parse(self, info, torrentSep='\n \n', lineSep = '\n'):
    if info == '': return []

    parsed = []
    # per torrents
    torrents = info.split(torrentSep)
    for torrent in torrents:
      torrentInfo = {}

      lines = torrent.split(lineSep) 

      if lines[0] == ' ': del lines[0]
      if len(lines) == 0: return None

      for line in lines:
        tokens = line.split(': ')
        if tokens[0] == 'Name':
          torrentInfo['title'] = tokens[1]
        elif tokens[0] == 'ID':
          torrentInfo['id'] = tokens[1]
        elif tokens[0] == 'State':
          torrentInfo['state'] = (tokens[1].split(' '))[0].lower()
        elif tokens[0] == 'Seeds':
          torrentInfo['seeds'] = line
        elif tokens[0] == 'Size':
          torrentInfo['size'] = line
        elif tokens[0] == 'Seed time':
          torrentInfo['seed time'] = line
        elif tokens[0] == 'Progress': 
          torrentInfo['progress'] = (tokens[1].split(' '))[0].lower()

      parsed.append(torrentInfo)
    return parsed if len(parsed) > 0 else None

