# 텔레그램봇을 사용한 토렌트 컨트롤 
## 라이브러리 
[Telepot Tutorial](http://telepot.readthedocs.io/en/latest/)을 보고 해당 라이브러리를 설치한다. 

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




