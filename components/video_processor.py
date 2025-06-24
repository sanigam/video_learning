import re
import os
import requests
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.google_adk_manager import GoogleADKManager

# Load environment variables
load_dotenv()

# Configure requests with custom headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

class VideoProcessor:
    def __init__(self):
        """Initialize the VideoProcessor class."""
        try:
            self.gemini_manager = GoogleADKManager()
        except Exception as e:
            print(f"Warning: Could not initialize Gemini manager: {e}")
            self.gemini_manager = None
        
        # Path to the sample transcript file
        self.sample_transcript_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'sample_transcript_clean.txt'
        )
        
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
    
    def load_sample_transcript(self):
        """
        Load the sample transcript from file.
        
        Returns:
            str: Sample transcript content
        """
        try:
            with open(self.sample_transcript_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            print(f"Error loading sample transcript: {e}")
            # Fallback hardcoded sample
            return "This is a sample transcript about artificial intelligence and machine learning technologies. AI and ML are transforming how we interact with technology and solve complex problems. Machine learning enables systems to learn from data and improve over time without explicit programming."
    
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
        Extract transcript from a YouTube video using a three-tier fallback system:
        1. YouTubeTranscriptApi (most reliable)
        2. Gemini AI transcription (fallback)
        3. Sample transcript (demo fallback)
        
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
        
        # Tier 1: Try YouTubeTranscriptApi (most reliable and fast)
        try:
            print("Tier 1: Trying YouTubeTranscriptApi...", flush=True)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            if transcript_list:
                transcript = ' '.join(entry['text'] for entry in transcript_list)
                if transcript and len(transcript.strip()) > 50:  # Ensure meaningful content
                    print("✓ Successfully extracted transcript using YouTubeTranscriptApi", flush=True)
                    return transcript
        except Exception as e:
            print(f"✗ YouTubeTranscriptApi failed: {str(e)}", flush=True)
        
        # Tier 2: Try Gemini AI transcription (slower but more capable)
        if self.gemini_manager:
            try:
                print("Tier 2: Trying Gemini AI transcription...", flush=True)
                transcript = self.gemini_manager.transcribe_youtube_video(video_id)
                
                # Check if Gemini returned a valid transcript
                if transcript and not transcript.startswith("Failed to transcribe") and len(transcript.strip()) > 50:
                    print("✓ Successfully extracted transcript using Gemini AI", flush=True)
                    return transcript
                else:
                    print("✗ Gemini AI returned insufficient transcript content", flush=True)
            except Exception as e:
                print(f"✗ Gemini AI transcription failed: {str(e)}", flush=True)
        else:
            print("✗ Gemini manager not available", flush=True)
        
        # Tier 3: Use sample transcript for demonstration purposes
        try:
            print("Tier 3: Using sample transcript for demonstration...", flush=True)
            sample_transcript = self.load_sample_transcript()
            
            # Add a note about using sample content
            demo_message = f"[DEMO MODE] The following is a sample transcript as the original video transcript could not be extracted:\n\n{sample_transcript}"
            print("✓ Loaded sample transcript for demonstration", flush=True)
            return demo_message
            
        except Exception as e:
            print(f"✗ Even sample transcript failed: {str(e)}", flush=True)
            return "Unable to extract transcript from any source. Please try a different video or check your internet connection."
    
    def process_video(self, url):
        """
        Process a YouTube video by extracting its ID, information, and transcript.
        Uses a three-tier fallback system for transcript extraction.
        
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
            
            # Extract transcript using three-tier fallback system
            transcript = self.extract_transcript(video_id)
            
            # Always return the transcript - it will either be:
            # 1. Real transcript from YouTubeTranscriptApi
            # 2. AI-generated transcript from Gemini
            # 3. Sample transcript for demonstration
            # 4. Error message explaining the issue
            
            # Validate transcript length for meaningful content
            if transcript and len(transcript.strip()) < 10:
                print("Warning: Very short transcript detected", flush=True)
                # Still proceed - the sample transcript will be used for demo
            
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
            # Handle other errors - still try to provide sample transcript for demo
            error_msg = str(e)
            print(f"Processing Error: {error_msg}", flush=True)
            
            # Create a minimal video info for error display
            video_info = {
                'id': 'error',
                'title': 'Error Processing Video',
                'channel': 'Error',
                'duration': 0
            }
            
            # Try to provide sample transcript even in error case for demonstration
            try:
                sample_transcript = self.load_sample_transcript()
                demo_message = f"[DEMO MODE] Video processing encountered an error, but here's a sample transcript for demonstration:\n\nError: {error_msg}\n\nSample Content:\n{sample_transcript}"
                return video_info, demo_message
            except:
                return video_info, f"Error processing video: {error_msg}"
