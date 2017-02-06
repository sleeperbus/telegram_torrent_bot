#-*- coding: utf-8 -*-
import sys
import os
import log
import logging
import json

from pprint import pprint
from random import randint
from datetime import datetime
import telepot
import telepot.helper
from telepot.delegate import (
	per_chat_id, create_open, per_application, pave_event_space,
  include_callback_query_chat_id
)
from telepot.namedtuple import (
  ReplyKeyboardMarkup, KeyboardButton, 
  ForceReply, 
  InlineKeyboardMarkup, InlineKeyboardButton,
  InlineQueryResultArticle, InlineQueryResultPhoto, 
  InputTextMessageContent 
)
from services import searchFromTorrentKim
from torrentserver import deluge
from sqlite3 import dbapi2 as sqlite
from dbserver import dbserver
from apscheduler.schedulers.background import BackgroundScheduler
import docclass

reload(sys)
sys.setdefaultencoding('utf-8')

class T2bot(telepot.helper.ChatHandler):
  def __init__(self, seed_tuple, search, db, server, **kwargs):
    super(T2bot, self).__init__(seed_tuple, **kwargs)
    self.logger = logging.getLogger('torrentbot')
    self.logger.debug('Chatbot logger init')
    self.search = search
    self.server = deluge()
    self.db = db
    self.items = []
    self.mode = ''

    # inline keyboards
    self.savedMsgIdentifier = None

    self.inlineButtons = InlineKeyboardMarkup(
      inline_keyboard=[]
    )
   
  def on_close(self, e):
    pass

  # Check user is valid and welcome message
  def open(self, initial_msg, seed):
    if not self.db.isUser(self.chat_id):
      self.sender.sendMessage('user_id: %d is not a valid user' % (self.chat_id))
      self.logger.warn('invalid user %d' % self.chat_id)
      return 
    self.sender.sendMessage('Welcome back')
 
  # user에게 선택 버튼을 보여준다. 
  def showItems(self, items):
    l = [[InlineKeyboardButton(text=item['title'], callback_data=str(index))] for index, item in enumerate(items) if item]
    self.inlineButtons = InlineKeyboardMarkup(inline_keyboard=l)
    self.savedMsgIdentifier = self.sender.sendMessage('Choose ...', reply_markup=self.inlineButtons)

  # Send torrent info string 
  def showTorrentsProgress(self):
    ids = self.db.torrentIds(self.chat_id)
    if len(ids) == 0: 
      msg = 'There is no torrents downloading ...'
      self.sender.sendMessage(msg)
    else:
      info = [self.server.torrentInfoStr(id) for id in ids]
      # only torrent exists in server
      info = [t for t in info if t]
      if len(info) == 0: 
        self.sender.sendMessage('There is no torrents downloading ...')
      else: self.sender.sendMessage('\n\n'.join(info))

  # current torrent files downloaded
  def ongoingList(self):
    torrents = []
    ids = self.db.torrentIds(self.chat_id)
    torrents = [self.server.torrentInfo(id) for id in ids]
    torrents = [t for t in torrents if t is not None]
    return torrents
 
  def on_chat_message(self, msg): 
    content_type, chat_type, chat_id = telepot.glance(msg) 
    # check valid user
    if not self.db.isUser(chat_id):
      msg = 'user_id: %d is not a valid user' % chat_id
      self.sender.sendMessage(msg)
      self.logger.warn(msg)
      return 
    
    # always consider text message
    if content_type == 'text': 
      # command - progress
      if msg['text'] == '/progress':
        self.mode = 'progress'
        self.showTorrentsProgress() 
        return

      # command - delete
      elif msg['text'] == '/delete':
        self.mode = 'delete'
        # clear message identifier saved
        if self.savedMsgIdentifier:
          id = telepot.message_identifier(self.savedMsgIdentifier)
          self.bot.editMessageText(id, '...', reply_markup=None)

        self.sender.sendMessage('Select torrent to delete ...')
        self.items = self.ongoingList()
        if len(self.items) == 0: 
          self.sender.sendMessage('There is no downloading files.')
          self.savedMsgIdentifier = None
        else:
          self.showItems(self.items) 
          # self.showTorrentsMenu(self.torrents) 

      # command - reboot
      elif msg['text'] == '/reboot':
        self.logger.debug('user select reboot option')
        self.sender.sendMessage('Torrent server rebooting ...')
        self.sender.sendMessage('*** Do not enter message ***')
        self.server.reboot()
        self.sender.sendMessage('System ok ...')
        self.logger.debug('System reboot done ... ')

      # command - new tv schedule
      elif '/new_tvshow' in msg['text']:
        name, weekday, time, start_date, keyword = msg['text'].split(' ')[1].split('|')
        keyword = keyword.replace(',', ' ')
        for day in weekday.split(','):
					for res in ['720', '1080']:
						self.db.createTvShow(name, day, time, start_date, keyword+' '+res, self.chat_id)

      # 설정된 tvshow 목록을 확인한다. 
      elif '/close_tvshow' in msg['text']:
        self.mode = 'close_tvshow'
        if self.savedMsgIdentifier:
          id = telepot.message_identifier(self.savedMsgIdentifier)
          self.bot.editMessageText(id, '...', reply_markup=None)
        self.sender.sendMessage('오늘부터 스케줄링을 하지 않을 티비쇼를 고르세요.')
        self.logger.debug('chat_id is %d' % self.chat_id)
        self.items = self.db.tvShowList(self.chat_id)
        if len(self.items) == 0:
          self.sender.sendMessage('활성화된 티비쇼가 없습니다.')
          self.savedMsgIdentifier = None
        else:
          self.showItems(self.items)

      # search torrents file using self.search function
      else: 
        self.mode = 'search'
        if self.savedMsgIdentifier:
          id = telepot.message_identifier(self.savedMsgIdentifier)
          self.bot.editMessageText(id, '...', reply_markup=None)

        self.sender.sendMessage('searching ...') 
        self.logger.debug('user try to search keyword: %s' % msg['text'])
        self.items = self.search(unicode(msg['text'])) 

        if not len(self.items): 
          self.sender.sendMessage('There is no files searched.')
          self.logger.debug('can not find any torrent ...')
          self.savedMsgIdentifier = None
        else: 
          self.showItems(self.items)

    else: self.sender.sendMessage('You can only send text message.')

  # When user click a inline button
  def on_callback_query(self, msg): 
    query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
    self.logger.debug('in callback')

    if not self.savedMsgIdentifier:
      self.bot.answerCallbackQuery(query_id, 
        text='Overdue list, please search again')
      return 

    id = telepot.message_identifier(self.savedMsgIdentifier) 

    if self.mode == 'search':
      torrent = self.items[int(data)]
      self.bot.editMessageText(id, 'Adding,  %s' % torrent['title'], reply_markup=None)
      self.addTorrent(torrent['magnet'], self.chat_id)

    elif self.mode == 'delete': 
      torrent = self.items[int(data)]
      self.bot.editMessageText(id, 'Deleting, %s' % torrent['title'], reply_markup=None)
      self.deleteTorrent(torrent['id'])

    elif self.mode == 'close_tvshow':
      tvshow = self.items[int(data)]
      self.bot.editMessageText(id, '오늘부터 [%s]를 스케줄링 하지 않습니다.' % tvshow['title'], reply_markup=None)
      self.db.unsubscribeTvShow(tvshow['program_id'], datetime.today().strftime('%Y%m%d'))

  # add torrent magnet to torrent server and db server 
  def addTorrent(self, magnet, chat_id):
    torrentInfo = self.server.add(magnet) 
    if not torrentInfo:
      self.sender.sendMessage('Already in list')
      self.logger.debug('torrent user add is already in deluge, maybe')
      return

    torrentInfo['chat_id'] = chat_id
    self.db.addTorrent(torrentInfo)

  # remove torrent file from torrent server and db server
  def deleteTorrent(self, id):
    self.server.delete(id)
    self.db.deleteTorrent(self.chat_id, id)

# torrent monitoring
class JobMonitor(telepot.helper.Monitor):
  def __init__(self, seed_tuple, search, server, db):
    super(JobMonitor, self).__init__(seed_tuple, capture=[{'_': lambda msg: True}])
    self.server = server 
    self.search = search
    self.db = db
    self.logger = logging.getLogger('torrentbot')
    self.sched = BackgroundScheduler()
    self.sched.start()
    self.sched.add_job(self.torrentMonitor, 'interval', minutes=3)
    self.sched.add_job(self.keepAliveTorrentServer, 'interval', minutes=10)
    self.sched.add_job(self.downloadTvEpisodes, 'interval', minutes=120)
    self.sched.add_job(self.createDailyTvSchedule, 'cron', hour=1, minute=0)

    # self.createDailyTvSchedule()
    # self.downloadTvEpisodes()

    self.logger.debug('JobMonitor logger init ...')

  def createDailyTvSchedule(self):
    self.db.createDailySchedule()    
    self.logger.debug('daily schedule created')

  def downloadTvEpisodes(self):
    self.logger.debug('downloadTvEpisodes started')
    # 완료되지 않은 스케줄을 가져온다. 
    schedule = self.db.uncompletedTvEpisode()
    for episode in schedule:
      torrents = self.search(unicode(episode['keyword']))
      if not len(torrents): 
        self.logger.info('can not find tvshow ' + str(episode))
        self.db.increaseTvEpisodeCount(episode['program_id'], episode['download_date'])
      else: 
        # torrent 를 발견한다면 deluge 에 magnet 을 던진다. 
        torrentInfo = self.server.add(torrents[0]['magnet'])
        torrentInfo['chat_id'] = episode['chat_id']
        self.logger.info('new tvshow added ' + str(episode))
        if torrentInfo:
          # 스케줄을 완료처리하고 db 에 토렌트 정보를 입력한다.
          self.db.completeTvEpisode(episode['program_id'], episode['download_date'])
          torrentInfo['chat_id'] = episode['chat_id']
          self.db.addTorrent(torrentInfo)

  def on_chat_message(self, msg): 
    pass

  def on_callback_query(self, msg): 
    pass

  def on_close(self, e):
    self.logger.debug('JobMonitor will shutdown')
    self.shutdown()
   
  def shutdown(self):
    self.sched.shutdown()

  def keepAliveTorrentServer():
    if not self.server.isAlive():
      self.logger.warn('Server down, will reboot')
      self.server.reboot()

  def torrentMonitor(self):
    self.logger.debug('========== DB ==========')
    fromDB = self.db.uncompleted() 
    self.logger.debug(fromDB)

    self.logger.debug('========== Server ==========')
    if not self.server.isAlive():
      self.logger.warn('checking server completed list, find Server down, will reboot')
      self.server.reboot()
    else:
      self.logger.debug('Torrent server is alived ...')
      
    fromServer = self.server.completed() 
    self.logger.debug(fromServer)

    # extract complete torrents
    self.logger.debug('========== updateList ==========')
    updateList = []
    for dbt in fromDB:
      for st in fromServer:
        if dbt['id'] == st['id']:
          updateList.append({'id':dbt['id'], 'chat_id':dbt['chat_id'], 
            'title': st['title']}) 

    self.logger.debug(updateList) 

    for t in updateList:
      self.bot.sendMessage(t['chat_id'], 'downloaded\n' + t['title'])
      # self.db.completeTorrent(t['chat_id'], t['id'])
      self.server.delete(t['id'])
      self.db.deleteTorrent(t['chat_id'], t['id'])

# Delegator Bot
class ChatBox(telepot.DelegatorBot):
  def __init__(self, token, search, db, server):
    self.search = search
    self.db = db
    self.server = server
    
    super(ChatBox, self).__init__(token, 
    [
      include_callback_query_chat_id(
			pave_event_space())(
				per_chat_id(), create_open, T2bot, self.search, self.db, self.server, timeout=90	
			), 
      (per_application(), create_open(JobMonitor, self.search, self.server, self.db)),
    ])
	
########################################################################### 

if __name__ == '__main__':
  try:
    with open('setting.json', 'r') as f:
      settings = json.load(f)
    TOKEN = str(settings['token']['torrent'])

    logger = log.setupCustomLogger('torrentbot', './torrentbot.log')
    server = deluge()
    db = dbserver('torrent.db')

    bot = ChatBox(TOKEN, searchFromTorrentKim, db, server)
    bot.message_loop(run_forever='Listening...')

  except KeyboardInterrupt:
    print('Interrupted')
    try:
      sys.exit(0)
    except SystemExit:
      os._exit(0)
    

        
