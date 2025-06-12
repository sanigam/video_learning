import re
import os
import requests
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

# Configure requests with custom headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

class VideoProcessor:
    def __init__(self):
        """Initialize the VideoProcessor class."""
        pass
        
    def extract_video_id(self, url):
        """
        Extract the YouTube video ID from a URL.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            str: YouTube video ID
        """
        # Regular expression to extract video ID from YouTube URL
        youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_regex, url)
        
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    
    def get_video_info(self, video_id):
        """
        Get video information based on video ID.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            dict: Dictionary containing video information
        """
        # This is a placeholder for video info fetching
        # In a real application, you would use the YouTube API
        try:
            # Try to get a more descriptive title using the video ID format
            # Format video ID to make it look more like a title
            title_from_id = video_id.replace("_", " ").replace("-", " ")
            
            return {
                'id': video_id,
                'title': f"YouTube Video: {title_from_id}",
                'channel': "YouTube Channel",
                'duration': 10,  # minutes
                'views': 1000,
                'likes': 100,
                'published_date': "2023-01-01",
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
        except Exception as e:
            # Fallback to even more basic info if there's an error
            return {
                'id': video_id,
                'title': f"Video {video_id}",
                'channel': "Unknown Channel",
                'duration': 0,
                'views': 0,
                'likes': 0,
                'published_date': "Unknown",
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }
        
    def extract_transcript(self, video_id):
        """
        Extract transcript from a YouTube video.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            str: Transcript text
        """
        def clean_transcript(text):
            """Clean the transcript text by removing timestamps and other artifacts"""
            # Remove SRT timestamps
            text = re.sub(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+', '', text)
            # Remove sequence numbers
            text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        print(f"Attempting to get transcript for video ID: {video_id}", flush=True)
        
        # First try YouTubeTranscriptApi as it's more reliable
        try:
            print("Trying YouTubeTranscriptApi...", flush=True)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            if transcript_list:
                return ' '.join(entry['text'] for entry in transcript_list)
        except Exception as e:
            print(f"YouTubeTranscriptApi error: {str(e)}", flush=True)
        
        # If that fails, try PyTube
        try:
            print("Trying PyTube...", flush=True)
            session = requests.Session()
            session.headers.update(HEADERS)
            yt = YouTube(
                url=f'https://www.youtube.com/watch?v={video_id}',
                use_oauth=False,
                allow_oauth_cache=True
            )
            yt.use_oauth = False
            yt.allow_oauth_cache = True
            
            if not yt.captions:
                print("No captions available", flush=True)
                return "No captions available for this video"
                
            caption = None
            # Try to get English captions
            if 'en' in yt.captions:
                caption = yt.captions['en']
            elif 'a.en' in yt.captions:  # Try auto-generated English
                caption = yt.captions['a.en']
                
            if caption:
                transcript = caption.generate_srt_captions()
                return clean_transcript(transcript)
                
            return "No English transcript available for this video"
                
        except Exception as e:
            error_message = str(e)
            print(f"PyTube error: {error_message}", flush=True)
            
            if "HTTP Error 400" in error_message:
                return "Unable to access video. The video might be private or restricted."
            elif "Video unavailable" in error_message:
                return "This video is unavailable or doesn't exist."
            else:
                return f"Error extracting transcript: {error_message}"
            
        except Exception as e:
            error_message = str(e).lower()
            print(f"Transcript error: {error_message}", flush=True)
            
            # Check error message strings since the exception types might not be directly available
            if "no transcript" in error_message:
                return "No transcript found for this video. The video might not have captions enabled."
            elif "transcript is disabled" in error_message:
                return "Transcripts are disabled for this video by the content creator."
            elif "available transcript" in error_message:
                return "No transcript is available in the requested language. Try a different video."
            elif "invalid parameter" in error_message or "not found" in error_message:
                return "Invalid YouTube video ID or video not found. Please check the URL."
            else:
                return f"Error extracting transcript: {str(e)}"
    
    def process_video(self, url):
        """
        Process a YouTube video by extracting its ID, information, and transcript.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            tuple: (video_info, transcript)
        """
        try:
            # Extract video ID from URL
            video_id = self.extract_video_id(url)
            
            # Get video information
            video_info = self.get_video_info(video_id)
            
            # Extract transcript
            transcript = self.extract_transcript(video_id)
            
            # Check if transcript is an error message
            if transcript.startswith("No transcript") or transcript.startswith("Error") or transcript.startswith("Transcript") or transcript.startswith("Invalid"):
                print(f"Transcript issue detected: {transcript}", flush=True)
                return video_info, transcript
                
            # Validate transcript
            if not transcript or len(transcript) < 10:
                return video_info, "No valid transcript available for this video. The video might not have captions or subtitles."
            
            return video_info, transcript
        
        except ValueError as e:
            # Handle invalid URL error
            error_msg = str(e)
            print(f"URL Error: {error_msg}", flush=True)
            # Create a minimal video info for error display
            video_info = {
                'id': 'error',
                'title': 'Error: Invalid URL',
                'channel': 'Error',
                'duration': 0
            }
            return video_info, f"Invalid YouTube URL: {error_msg}"
        
        except Exception as e:
            # Handle other errors
            error_msg = str(e)
            print(f"Processing Error: {error_msg}", flush=True)
            # Create a minimal video info for error display
            video_info = {
                'id': 'error',
                'title': 'Error Processing Video',
                'channel': 'Error',
                'duration': 0
            }
            return video_info, f"Error processing video: {error_msg}"
