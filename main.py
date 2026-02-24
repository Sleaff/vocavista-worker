from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
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

@app.post("/simple-transcript-v3")
async def simple_transcript_v3(request: TranscriptRequest):
    video_id = get_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        # Create an instance of the API
        api = YouTubeTranscriptApi()
        
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