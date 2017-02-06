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
        , chat_id
        , foreign key(chat_id) references users(chat_id)
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

    self.con.execute(
      """
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
  def subscribeTvShow(self, name, day, time, startDate, keyword, chat_id):
		try:
			with self.con:
				self.con.execute(
					"""
					insert into tv_program(
						program_name
						, day
						, time
						, start_date
						, search_keyword
            , chat_id
					) values (?,?,?,?,?,?)
					""", (name, day, time, startDate, keyword, chat_id)
				)
		except sqlite.Error as err:
			print('Error: insert new tvshow ')
			pprint(err)

  # 티비쇼를 해지한다.
  def unsubscribeTvShow(self, program_id, end_date):
    try:
      with self.con:
        self.con.execute(
          """
            update  tv_program 
            set     end_date = ?
            where   program_id = ?
          """, (end_date, program_id, )
        )
    except sqlite.Error as err:
      print('unsubscribeTvShow update error')
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
                    , substr(strftime('%Y%m%d', 'now', 'localtime'), 3)
                    , 0
                    , 0
            from    tv_program 
            where   replace(date('now', 'localtime'), '-', '') between start_date and
											case when end_date ='' then '30000101' else end_date end
            and     strftime('%w', 'now', 'localtime') = day
           """
        )
    except sqlite.IntegrityError:
      print('db error: dup on val: already in tv_schedule')

  # 토렌트 정보를 db 에 저장한다.
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

  # 토렌트 정보를 db에서 삭제한다.
  def deleteTorrent(self, chat_id, id):
    try:
      with self.con:
        self.con.execute(
          "delete from torrents where chat_id = %d and id = '%s'" % (chat_id, id)
        )
    except sqlite.Error as err:
      print('db error: delete')
      pprint(err) 

  # 진행 중인 토렌트에 완료처리를 한다. 
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

  # 토렌트 고유id를 반환한다. 마그넷과 동일하다.
  def torrentIds(self, chat_id):
    cur = self.con.execute("""
    select  id 
    from    torrents 
    where   chat_id = %d
    """ % chat_id)
    results = cur.fetchall()
    return [r[0] for r in results]

  # 완료되지 않은 토렌트 즉, 다운로드 진행 중인 것을 반환한다. 
  def uncompleted(self):
    cur = self.con.execute("""
      select  distinct id, chat_id
      from    torrents 
      where   completed = 0
      """)
    results = cur.fetchall()
    return [{'id':r[0], 'chat_id':r[1]} for r in results]

  # 스케쥴링 된 tvshow episode 를 반환한다. 
  def uncompletedTvEpisode(self):
    cur = self.con.execute(
      """
      select  a.download_date || ' ' || b.search_keyword as keyword 
              , a.program_id as program_id
              , a.download_date as download_date
              , b.chat_id as chat_id
      from    tv_schedule a
              , tv_program b
      where   a.completed = 0 
      and     b.program_id = a.program_id
      """
    )
    results = cur.fetchall()
    return [{'keyword':r[0], 'program_id':r[1], 'download_date':r[2], 'chat_id':r[3]} for r in results]

  # 스케줄링 된 tvshow episode 의 count 를 증가시킨다. 
  def increaseTvEpisodeCount(self, program_id, download_date):
    try:
      with self.con:
        self.con.execute(
          """
          update    tv_schedule
          set       try_count = try_count + 1
          where     program_id = ? 
          and       download_date = ?
          """, (program_id, download_date)
        )
    except sqlite.Error as err:
      print('db error: update')
      pprint(err) 

  # episode 를 완료처리 한다. 
  def completeTvEpisode(self, program_id, download_date):
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

  # 설정된 tvshow 목록을 반환한다. 
  def tvShowList(self, chat_id):
    try:
      with self.con:
        cur = self.con.execute(
          """
          select  a.program_id
                  , a.program_name
                  , a.search_keyword
                  , case 
                    when a.end_date <> '' then '(종료일: ' || a.end_date || ')'
                    else ''
                    end end_date
          from    tv_program a 
          where   a.chat_id = ?
          and     (a.end_date >= strftime('%Y%m%d', 'now', 'localtime') or 
                    a.end_date = '')
          """, (chat_id,)
      )
    except sqlite.Error as err:
      pprint(err)
    results = cur.fetchall()
    return [{'program_id':r[0], 'title':r[1]+'-'+r[2]+r[3]} for r in results]











