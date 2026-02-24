from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import ProxyConfig
import re
import os

app = FastAPI()

# IMPORTANT: This allows your Chrome extension to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Request model to match the Javascript 'body'
class TranscriptRequest(BaseModel):
    url: str
    lang: str = ""  # Default to empty string if not provided

def get_video_id(url):
    pattern = r'(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_proxy_config():
    """
    Get proxy configuration from environment variables.
    Set these environment variables in your Google Cloud deployment:
    - PROXY_HTTP: http proxy URL (e.g., http://proxy.example.com:8080)
    - PROXY_HTTPS: https proxy URL (optional, defaults to http proxy)
    """
    http_proxy = os.getenv('PROXY_HTTP')
    https_proxy = os.getenv('PROXY_HTTPS', http_proxy)
    
    if http_proxy:
        return ProxyConfig(
            http=http_proxy,
            https=https_proxy
        )
    return None

@app.post("/simple-transcript")
async def simple_transcript(request: TranscriptRequest):
    video_id = get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        # Create an instance of the API with proxy support
        proxy_config = get_proxy_config()
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
        
        # Get the list of all available transcripts
        transcript_list = api.list(video_id)
        
        # Logic to pick the language
        if request.lang:
            # Try to find the specific language requested
            target_transcript = transcript_list.find_transcript([request.lang])
        else:
            # Default to English (or whatever is first available)
            target_transcript = transcript_list.find_transcript(['en', 'es', 'fr', 'de'])

        # Fetch the actual text with timings
        data = target_transcript.fetch()
        
        # Include timing information for each snippet
        transcript_with_timings = [
            {
                "text": item.text,
                "start": item.start,
                "duration": item.duration
            }
            for item in data
        ]
        
        # full_text = " ".join([item.text for item in data])

        # Return the exact JSON structure the Chrome extension expects
        return {
            "video_id": video_id, 
            # "transcript": full_text,
            "transcript": transcript_with_timings,
            "transcriptLanguageCode": target_transcript.language_code,
            "languages": [
                {"code": t.language_code, "name": t.language} 
                for t in transcript_list
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))