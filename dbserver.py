#-*- coding: utf-8 -*-
from sqlite3 import dbapi2 as sqlite
from pprint import pprint

# sqlite db server
class dbserver:
  def __init__(self, dbfile):
    self.con = sqlite.connect(dbfile, check_same_thread=False)
    self.createTables()
  
  def createTables(self):
    self.con.execute(
      "create table if not exists users(chat_id primary key, username)"
    )

    self.con.execute(
      """create table if not exists torrents
      (
        id text
        , completed integer
        , stime datetime
        , etime datetime
        , chat_id integer
        , primary key(id, chat_id)
        , foreign key(chat_id) references users(chat_id)
      )
      """
    )

    self.con.execute(
      """
      create table if not exists tv_program(
        program_id integer primary key
        , program_name
        , day
        , time
        , start_date
        , end_date
        , search_keyword 
      )
      """
    )

    self.con.execute(
      """
        create table if not exists tv_schedule(
          program_id integer
          , download_date 
          , try_count integer
          , completed integer
          , primary key(program_id, download_date)
          , foreign key(program_id) references tv_program(program_id)
        )
      """
    )
 
  # user check
  def isUser(self, chat_id):
    res = self.con.execute(
      "select username from users where chat_id = %d" % (chat_id)
    ).fetchone()
    return True if res else False

  # username
  def username(self, chat_id):
    res = self.con.execute(
      "select username from users where chat_id = %d" % chat_id
    ).fetchone()
    return res[0]

  # 새로운 티비 프로그램을 입력한다. 
  def createTvShow(self, name, day, time, startDate, endDate, keyword):
		try:
			with self.con:
				self.con.execute(
					"""
					insert into tv_program(
						program_name
						, day
						, time
						, start_date
						, end_date
						, search_keyword
					) values (?,?,?,?,?,?)
					""", (name, day, time, startDate, endDate, keyword)
				)
		except sqlite.Error as err:
			print('Error: insert new tvshow ')
			pprint(err)

  # tv_program 을 기반으로 일별 스케줄을 생성한다. 
  def createDailySchedule(self):
    try:
      with self.con:
        self.con.execute(
          """
            insert into tv_schedule(
              program_id
              , download_date
              , try_count
              , completed
            ) 
            select  program_id
                    , substr(strftime('%Y%m%d'), 3)
                    , 0
                    , 0
            from    tv_program 
            where   strftime('%Y%m%d') between ifnull(start_date, '19000101') and ifnull(end_date, '30000101')
            and     strftime('%w') = day 
          """
        )
    except sqlite.IntegrityError:
      print('db error: dup on val: already in tv_schedule')

  # 
  def addTorrent(self, tinfo):
    try:
      with self.con: 
        self.con.execute(
          """
           insert into torrents values(?, 0, datetime('now', 'localtime'), NULL, ?)
          """ , (tinfo['id'], tinfo['chat_id'])
        )
    except sqlite.IntegrityError:
      print('db error: dup on val')
      pprint(tinfo) 

  # 
  def deleteTorrent(self, chat_id, id):
    try:
      with self.con:
        self.con.execute(
          "delete from torrents where chat_id = %d and id = '%s'" % (chat_id, id)
        )
    except sqlite.Error as err:
      print('db error: delete')
      pprint(err) 

  def completeTorrent(self, chat_id, id):
    try:
      with self.con:
        self.con.execute(
          """
          update  torrents 
          set     completed = 1 
                  , etime = datetime('now', 'localtime')
          where   chat_id = %d and id = '%s'
          """ % (chat_id, id) 
        )
    except sqlite.Error as err:
      print('db error: update')
      pprint(err) 

  # 
  def torrentIds(self, chat_id):
    cur = self.con.execute("""
    select  id 
    from    torrents 
    where   chat_id = %d
    """ % chat_id)
    results = cur.fetchall()
    return [r[0] for r in results]

  def uncompleted(self):
    cur = self.con.execute("""
      select  distinct id, chat_id
      from    torrents 
      where   completed = 0
      """)
    results = cur.fetchall()
    return [{'id':r[0], 'chat_id':r[1]} for r in results]

  def uncompletedSchedule(self):
    cur = self.con.execute(
      """
      select  a.download_date || ' ' || b.search_keyword as keyword 
              , a.program_id
              , a.download_date
      from    tv_schedule a, tv_program b
      where   a.completed = 0 
      and     b.program_id = a.program_id
      """
    )
    results = cur.fetchall()
    return [{'keyword':r[0], 'program_id':r[1], 'download_date':r[2]} for r in results]

  def increaseTvShowCount(self, program_id, download_date):
    try:
      with self.con:
        self.con.execute(
          """
          update    tv_schedule
          set       count = count + 1
          where     program_id = ? 
          and       download_date = ?
          """, (program_id, download_date)
        )
    except sqlite.Error as err:
      print('db error: update')
      pprint(err) 

  def completedTvSchedule(self, program_id, download_date):
    try:
      with self.con:
        self.con.execute(
          """
          update    tv_schedule
          set       completed = 1
          where     program_id = ? 
          and       download_date = ?
          """, (program_id, download_date)
        )
    except sqlite.Error as err:
      print('db error: update')
      pprint(err) 



