#!/usr/bin/env python3
"""
FastAPI application to fetch YouTube video transcripts.
"""

import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return the ID if already provided."""
    # Pattern for various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def fetch_transcript(video_id):
    """Fetch transcript for a given YouTube video ID."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Get the transcript - try different methods
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Format the transcript
        full_transcript = []
        for entry in transcript_list:
            text = entry['text']
            start_time = entry['start']
            full_transcript.append(f"[{start_time:.2f}s] {text}")
        
        return '\n'.join(full_transcript)
    
    except ImportError:
        return "Error: youtube-transcript-api not installed. Run: pip install youtube-transcript-api"
    except Exception as e:
        # Try alternative approach with yt-dlp
        return fetch_transcript_ytdlp(video_id, str(e))


def fetch_transcript_ytdlp(video_id, previous_error):
    """Fallback method using yt-dlp."""
    try:
        import subprocess
        import json
        import tempfile
        import os
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create a temporary directory for subtitles
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, 'subtitle')
            
            # Download subtitles
            result = subprocess.run(
                ['yt-dlp', '--write-auto-subs', '--write-subs', '--sub-lang', 'en', 
                 '--skip-download', '--sub-format', 'json3', '-o', output_template, url],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return f"Error with youtube-transcript-api: {previous_error}\nError with yt-dlp: {result.stderr}\n\nMake sure yt-dlp is installed: pip install yt-dlp"
            
            # Find the subtitle file
            subtitle_files = [f for f in os.listdir(tmpdir) if f.endswith('.json3')]
            
            if not subtitle_files:
                return f"Error with youtube-transcript-api: {previous_error}\nNo subtitles found with yt-dlp. The video may not have captions available."
            
            # Read and parse the subtitle file
            subtitle_path = os.path.join(tmpdir, subtitle_files[0])
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitle_data = json.load(f)
            
            # Extract transcript from JSON3 format
            full_transcript = []
            if 'events' in subtitle_data:
                for event in subtitle_data['events']:
                    if 'segs' in event and event.get('segs'):
                        start_time = event.get('tStartMs', 0) / 1000
                        text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
                        if text:
                            full_transcript.append(f"[{start_time:.2f}s] {text}")
            
            if full_transcript:
                return '\n'.join(full_transcript)
            else:
                return f"Error: Could not parse subtitle format from yt-dlp"
    
    except FileNotFoundError:
        return f"Error with youtube-transcript-api: {previous_error}\nyt-dlp not found. Install it with: pip install yt-dlp"
    except Exception as e:
        return f"Error with youtube-transcript-api: {previous_error}\nError with yt-dlp fallback: {str(e)}\n\nTry: pip install --upgrade youtube-transcript-api"


# FastAPI setup
app = FastAPI(
    title="YouTube Transcript API",
    description="API to fetch transcripts from YouTube videos",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscriptRequest(BaseModel):
    video_url: str


class TranscriptResponse(BaseModel):
    video_id: str
    transcript: str


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/transcript", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    """
    Fetch transcript for a YouTube video.
    
    - **video_url**: YouTube URL or video ID
    """
    video_id = extract_video_id(request.video_url)
    
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL or video ID"
        )
    
    transcript = fetch_transcript(video_id)
    
    # Check if transcript fetch resulted in an error
    if transcript.startswith("Error"):
        raise HTTPException(
            status_code=500,
            detail=transcript
        )
    
    return TranscriptResponse(
        video_id=video_id,
        transcript=transcript
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)