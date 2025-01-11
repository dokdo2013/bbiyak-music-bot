import os
import json
import redis
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import discord

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Redis 설정
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE_PATH")
REDIS_CHANNEL_ID = 'bbybby'

# YouTube Data API 인증
def get_youtube_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
    )
    return build("youtube", "v3", credentials=credentials)

# YouTube 검색
def search_youtube(search_query):
    """YouTube Data API를 사용해 노래 검색"""
    youtube = get_youtube_service()
    request = youtube.search().list(
        part="snippet",
        type="video",
        q=search_query,
        maxResults=5
    )
    response = request.execute()
    print(f"YouTube API response: {response}")

    # 검색 결과 정리
    videos = []
    for item in response['items']:
        video_id = item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        title = item['snippet']['title']
        description = item['snippet']['description']
        videos.append({
            "title": title,
            "description": description,
            "url": video_url
        })

    return videos

# OpenAI API를 사용해 가장 적합한 영상 선택
def select_best_video(videos, song_info):
    """OpenAI API를 사용해 가장 적합한 영상 선택"""
    prompt = (
        f"다음은 '{song_info}'에 대한 YouTube 검색 결과입니다. "
        f"가장 적합한 영상 URL만 반환해주세요:\n\n"
    )
    for i, video in enumerate(videos):
        prompt += f"{i+1}. 제목: {video['title']}\n   설명: {video['description']}\n   URL: {video['url']}\n\n"

    prompt += "가장 적합한 영상의 URL만 출력해주세요."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": f"다음은 '{song_info}'에 대한 YouTube 검색 결과입니다. 가장 적합한 영상 URL만 반환해주세요. 또한 Special Clip이 들어가는 건 지양해줘. 그리고 차근차근히 찾아봤는데 만일 가장 적합한 URL이 없으면 'NONE'을 해줘. 그리고 'NONE' 이랑 URL을 제외한 어떠한 메세지도 나오면 안돼"},
            {
                "role": "user",
                "content": json.dumps(videos),
            }
        ]
    )

    best_url = response.choices[0].message.content
    print(f"OpenAI response (BEST RESPONSE): {best_url}")

    return best_url

# 최종 실행 함수
def find_best_song_video(song_title, artist_name):
    """노래 제목과 가수명으로 적합한 YouTube 영상 URL 반환"""
    try:
        # YouTube에서 검색
        videos = search_youtube(song_title, artist_name)

        # OpenAI API로 가장 적합한 영상 선택
        best_video_url = select_best_video(videos, song_title, artist_name)

        return best_video_url

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_song_info(message):
    """OpenAI API를 사용해 노래 제목과 가수명 추출"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "제공되는 메시지에서 노래 제목과 가수명을 찾아줘. 만일 노래 제목과 가수명으로 인식되지는 않지만, hyphen으로 구분되어 텍스트가 제공되면 노래 제목과 가수명으로 간주해도 좋아. 만일 노래 제목과 가수명을 찾을 수 없으면 'none'을 return하고, 노래 제목과 가수명이 있으면 '<노래제목> - <가수명>' 형식으로 return해줘. (e.g. 'Dynamite - 방탄소년단')"},
            {
                "role": "user",
                "content": message,
            }
        ]
    )

    song_info = response.choices[0].message.content
    return song_info

def handle_message(message):
    try:
        song_info = get_song_info(message)
        print(f"Song info: {song_info}")

        if song_info.lower() == "none":
            raise Exception("No song info found.")

        # 노래 제목과 가수명으로 YouTube 영상 검색 (Youtube Data API v3)
        videos = search_youtube(song_info)
        print(f"YouTube search response: {videos}")

        if not videos:
            raise Exception("No videos found.")

        # 가장 적합한 영상 URL 선택
        best_video_url = select_best_video(videos, song_info)
        print(f"Best video URL: {best_video_url}")

        if not best_video_url or best_video_url.lower() == "none":
            raise Exception("No best video URL found.")

        # 사용자에게 가장 적합한 영상 URL 전송
        url = best_video_url
        isSuccess = True
    except Exception as e:
        print(f"Error: {e}")
        # 유저에게 메시지 보내기
        url = f"노래를 찾을 수 없습니다. 다른 키워드로 다시 시도해주세요! :cry:"
        isSuccess = False

    return isSuccess, url



## ========================================================================================================
## MAIN
## ========================================================================================================

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

# 봇이 준비되었을 때 실행
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is ready!")

thread_ids_string = os.getenv("THREAD_IDS")
thread_ids = [int(thread_id) for thread_id in thread_ids_string.split(",")]

# 메시지 수신 이벤트 처리
@bot.event
async def on_message(message):
    # 메시지가 대상 스레드에서 왔는지 확인
    if message.channel.id in thread_ids and message.channel.name == '신청곡 받습니당':
        print(f"New message in thread '{message.channel.name}': {message.content}")
    else:
        print('Ignore')
        return

    # 봇 자신의 메시지는 무시
    if message.author == bot.user:
        return

    isSuccess, url = handle_message(message.content)

    if isSuccess:
        # Redis Pub
        redis_client.publish('bbybby', url)

        send_message = f"노래가 추가되었어요 (url : {url})"
        await message.channel.send(send_message)
    else:
        await message.channel.send(url)
        pass


# 봇 실행
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    print("환경변수 BOT_TOKEN이 설정되어 있지 않습니다.")
else:
    bot.run(TOKEN)


