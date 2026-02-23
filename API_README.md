# YouTube Transcript API

A FastAPI application that fetches transcripts from YouTube videos.

## Installation

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
python test.py
```

Or with uvicorn:

```bash
uvicorn test:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Usage

### POST /transcript

Fetch a transcript for a YouTube video.

**Request:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

Or with just the video ID:
```json
{
  "video_url": "dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "transcript": "[0.00s] Never gonna give you up\n[2.50s] Never gonna let you down..."
}
```

### Example with curl

```bash
curl -X POST "http://localhost:8000/transcript" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## Docker Deployment

### Build the image

```bash
docker build -t youtube-transcript-api .
```

### Run the container

```bash
docker run -p 8000:8000 youtube-transcript-api
```

## Deployment Options

### Deploy to Heroku

1. Create a `Procfile`:
   ```
   web: uvicorn test:app --host=0.0.0.0 --port=${PORT:-8000}
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Deploy to Railway/Render

Simply connect your Git repository and set the start command:
```
uvicorn test:app --host=0.0.0.0 --port=${PORT:-8000}
```

### Deploy to AWS Lambda

Use [Mangum](https://mangum.io/) adapter:
```python
from mangum import Mangum
handler = Mangum(app)
```
