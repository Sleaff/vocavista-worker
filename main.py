from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import re
from dotenv import load_dotenv
import os
import random
import json

load_dotenv()
proxies_list = json.loads(os.environ['PROXY_LIST'])

def get_random_proxy_credentials():
    if not proxies_list:
        return None, None
    # Each proxy should be in the format http://username:password@host:port
    proxy_url = random.choice(proxies_list)
    import re
    match = re.match(r"http[s]?://([^:]+):([^@]+)@", proxy_url)
    if match:
        return match.group(1), match.group(2)
    return None, None

app = FastAPI(
    title="YouTube Transcript API",
    description="API to fetch transcripts from YouTube videos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    url: str
    lang: str = ""

def get_video_id(url):
    pattern = r'(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.post("/simple-transcript")
async def simple_transcript(request: TranscriptRequest):
    video_id = get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        proxy_username, proxy_password = get_random_proxy_credentials()
        proxy_config = None
        if proxy_username and proxy_password:
            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
        
        transcript_list = api.list(video_id)
        
        if request.lang:
            target_transcript = transcript_list.find_transcript([request.lang])
        else:
            target_transcript = transcript_list.find_transcript(['en', 'es', 'fr', 'de'])

        data = target_transcript.fetch()
        
        transcript_with_timings = [
            {
                "text": item.text,
                "start": item.start,
                "duration": item.duration
            }
            for item in data
        ]
        
        return {
            "video_id": video_id, 
            "transcript": transcript_with_timings,
            "transcriptLanguageCode": target_transcript.language_code,
            "languages": [
                {"code": t.language_code, "name": t.language} 
                for t in transcript_list
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
