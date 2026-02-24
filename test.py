from youtube_transcript_api import YouTubeTranscriptApi

# Test with a popular video ID (replace with any YouTube video ID)
video_id = "p8XECshfjZU"  # Rick Astley - Never Gonna Give You Up

try:
    # Create an instance of the API
    api = YouTubeTranscriptApi()
    
    # Get the list of all available transcripts
    transcript_list = api.list(video_id)
    
    print(f"Available transcripts for video {video_id}:")
    for transcript in transcript_list:
        print(f"  - {transcript.language} ({transcript.language_code}) - Generated: {transcript.is_generated}")
    
    # Try to get English transcript
    target_transcript = transcript_list.find_transcript(['en'])
    
    # Fetch the actual text
    data = target_transcript.fetch()
    
    print(f"\nRaw data (first 3 items):")
    for i, item in enumerate(data[:3]):
        print(f"  Item {i}: {item}")
        print(f"    All attributes: {dir(item)}")
        print(f"    start: {item.start}")
        print(f"    duration: {item.duration}")
        print(f"    text: {item.text}")
        print()
    
    full_text = " ".join([item.text for item in data])
    
    print(f"\nTranscript language: {target_transcript.language_code}")
    print(f"Transcript preview (first 200 chars): {full_text[:200]}...")
    
    print(f"\nFirst 3 snippets with timings:")
    for i, item in enumerate(data[:3]):
        print(f"  [start={item.start:.2f}s, duration={item.duration:.2f}s]: {item.text}")
    
except Exception as e:
    print(f"Error: {e}")
