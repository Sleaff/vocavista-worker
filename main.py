from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import re

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
        api = YouTubeTranscriptApi()
        
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
