# 삐약톤 노래신청봇

## Features

- 디스코드 스레드에서 노래 제목을 입력하면 youtube link를 찾아 재생
- 노래 재생 중에 다른 노래를 입력하면 queue에 저장 후 이어서 재생

## Installation
### Prerequisite

- docker-compose
- python 3.12
- node.js 20 이상 (with pnpm)
- 환경변수 설정
  - `.env`
    - `BOT_TOKEN`: 디스코드 봇 토큰
    - `OPENAI_API_KEY`: openai api 키
    - `THREAD_IDS`: 디스코드 스레드 id (comma separated)
  - `sa.json`
    - Youtube Data Api 호출을 위한 service account json 

### 세팅 순서
1. `docker-compose up -d`
2. `pip install -r requirements.txt`
3. `pnpm install`
4. `python bot.py`
5. `node bridge.js`

## 파일별 동작
### bot.py
- 특정 채널 or 스레드에서 올라오는 메시지를 전부 다 catch
  - openai api를 이용해 노래 제목 - 가수명을 추출
  - 추출한 노래 제목 - 가수명을 youtube data api를 이용해 검색
  - 검색한 결과를 openai api에 보내 제일 적절한 url 추출
  - 추출한 url을 redis pub

### youtube.js
- redis pub한 url을 sub
- socket.io를 이용해 index.html로 url 전송

### index.html
- socket.io에서 받은 url을 localstorage에 queue로 저장
- queue에 저장된 url을 하나씩 iframe으로 띄워줌
- youtube iframe api를 이용해 큐 순서대로 재생