# 텔레그램봇을 사용한 토렌트 컨트롤 
## 라이브러리 
[Telepot Tutorial](http://telepot.readthedocs.io/en/latest/)을 보고 해당 라이브러리를 설치한다. 

## 최근 변경사항 
### v1.11(2017-02-07)
#### hot fix 
* 1주일이 넘게 대기하고 있는 tv schedule은 자동으로 중지하고 사용자에게 통보한다. 
* /close_tvshow 실행시 해당 tvshow의 요일도 표시해준다.
* /close_tvshow 에서 목록을 조회시 end_date is null 조건을 포함한다.

### v1.1(2017-02-06)
#### 기능 추가 
* tvshow의 종료일을 설정할 수 있다. 명령어: /close_tvshow

#### 기능 변경 
* tvshow 를 추가할 때 end_date 를 입력받지 않는다. 
  * /add_tvshow 보이스|6,0|2000|20170101|보이스

#### bug fix 
* daily tv schedule 생성시 localtime 기준으로 row 를 생성한다. 

## settings.json 설정 
* token: 두 개의 토큰을 사용한다.  
  *  torrent: 토렌트를 검색하고 다운받는 봇에서 사용한다. 
  *  classify: 파일분류봇을 운영하는데 사용한다.
* src_path: 다운완료된 토렌트 파일들이 저장되는 경로 
* dest_path: 파일분류봇이 파일을 옮길 목적지의 최상위 디렉토리 
* base_prob: 파일분류봇이 자동분류를 할 때 사용하는 확률. background 에서 돌아가는 파일분류 작업시 특정 폴더에 속할 확률이 이 수치보다 높으면 해당 폴더로 자동 분류된다. 
* super_user: 슈퍼유저의 텔레그램 id, 숫자로 되어 있다. 

## 실행 
두 개의 세션에서 아래를 실행한다. 
```
python bot.py 
python fileclassify.py
```

## 앞으로 개발할 기능 
### 다운로드 봇 
* 다운로드 대기 중인 티비쇼 에피소드 확인 및 삭제
* 토렌트 검색시 return 된 결과물이 10개보다 많을 경우 page nation

### 분류 봇 
* 파일을 목적지 디렉토리로 옮길 때 파일명을 깔끔하게 정리
* 파일 이름에서 제거할 문구를 tf-idf 기법을 사용해서 선택 

