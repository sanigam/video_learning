import os
import json
from utils.google_adk_manager import GoogleADKManager

class SummarizerAgent:
    def __init__(self):
        """Initialize the SummarizerAgent class."""
        self.adk_manager = GoogleADKManager()
        
    def generate_overview(self, transcript, video_info):
        """
        Generate a brief overview of the video content.
        
        Args:
            transcript (str): Video transcript
            video_info (dict): Information about the video
            
        Returns:
            dict: Overview information including brief description and primary topic
        """
        # Validate transcript input
        if not transcript or not isinstance(transcript, str):
            return {
                'description': "Unable to generate overview: Invalid transcript format.",
                'primary_topic': "Unknown",
                'target_audience': "Unknown",
                'content_type': "Unknown"
            }
            
        if len(transcript.strip()) < 50:
            return {
                'description': "Unable to generate overview: Transcript too short or empty.",
                'primary_topic': "Unknown",
                'target_audience': "Unknown",
                'content_type': "Unknown"
            }
        
        # Create prompt for overview generation
        system_prompt = """
        You are an expert educational content analyzer. Your task is to create a brief overview of a video 
        based on its transcript. Focus on identifying what the video is about in a succinct manner.
        
        Create an overview with these components:
        1. A 1-2 sentence description of what the video covers
        2. The primary topic of the video
        3. The likely target audience
        4. The content type (educational, tutorial, documentary, etc.)
        
        Format your response as a JSON object with the following structure:
        {
            "description": "Brief description of the video content...",
            "primary_topic": "Main topic of the video",
            "target_audience": "Who this video is for",
            "content_type": "Type of content"
        }
        
        Be concise and informative.
        """
        
        # Handle large transcripts by taking a sample from beginning and middle
        MAX_CHUNK_SIZE = 2000
        if len(transcript) > MAX_CHUNK_SIZE:
            # Take some from beginning and middle
            beginning = transcript[:int(MAX_CHUNK_SIZE*0.7)]
            middle_start = int(len(transcript)/2) - int(MAX_CHUNK_SIZE*0.15)
            middle = transcript[middle_start:middle_start+int(MAX_CHUNK_SIZE*0.3)]
            transcript_sample = beginning + "..." + middle
        else:
            transcript_sample = transcript
        
        user_prompt = f"""
        Video Title: {video_info.get('title', 'Unknown')}
        Video Channel: {video_info.get('channel', 'Unknown')}
        
        Transcript Sample:
        {transcript_sample}
        
        Please provide a brief overview of this video content.
        """
        
        try:
            # Use Google ADK API to generate overview
            overview_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.3
            )
            
            # Try to parse the JSON response
            try:
                overview = json.loads(overview_text)
                
                # Ensure we have all expected fields
                if "description" not in overview:
                    overview["description"] = "Overview not available."
                
                if "primary_topic" not in overview:
                    overview["primary_topic"] = "Topic not identified."
                    
                if "target_audience" not in overview:
                    overview["target_audience"] = "Audience not identified."
                    
                if "content_type" not in overview:
                    overview["content_type"] = "Content type not identified."
                    
                return overview
                
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured error response
                print(f"JSON parsing error for overview")
                
                return {
                    'description': "Unable to generate overview: Invalid response format.",
                    'primary_topic': "Processing Error",
                    'target_audience': "Unknown",
                    'content_type': "Unknown"
                }
            
        except Exception as e:
            # Provide a more detailed error message
            error_message = str(e)
            
            return {
                'description': f"Unable to generate overview: {error_message[:100]}...",
                'primary_topic': "Error",
                'target_audience': "Unknown",
                'content_type': "Unknown"
            }
    
    def generate_summary(self, transcript, video_info, summary_length="Moderate"):
        """
        Generate a summary of the video transcript.
        
        Args:
            transcript (str): Video transcript
            video_info (dict): Information about the video
            summary_length (str): Length of summary ('Concise', 'Moderate', 'Comprehensive')
            
        Returns:
            dict: Summary information including key points and summary text
        """
        # Validate transcript input before processing
        if not transcript or not isinstance(transcript, str):
            return {
                'summary_text': "Unable to generate summary: Invalid transcript format.",
                'key_points': [
                    "Invalid transcript data",
                    "Please ensure the video has captions available"
                ],
                'topics': ["Error: Invalid Input"]
            }
            
        if len(transcript.strip()) < 50:
            return {
                'summary_text': "Unable to generate summary: Transcript too short or empty.",
                'key_points': [
                    "Insufficient transcript content",
                    "The video may have limited or no captions"
                ],
                'topics': ["Error: Insufficient Content"]
            }
        
        # Configure length settings based on preference
        max_length_map = {
            "Concise": 150,
            "Moderate": 300,
            "Comprehensive": 500
        }
        
        num_key_points_map = {
            "Concise": 3,
            "Moderate": 5,
            "Comprehensive": 8
        }
        
        max_length = max_length_map.get(summary_length, 300)
        num_key_points = num_key_points_map.get(summary_length, 5)
        
        # Create prompt for summary generation
        system_prompt = f"""
        You are an expert educational content summarizer. Your task is to create a clear, insightful summary 
        of a video transcript. Focus on the main ideas and key takeaways.
        
        Create a summary with these components:
        1. A summary text of approximately {max_length} words
        2. {num_key_points} key points from the video
        3. A list of main topics covered
        
        Format your response as a JSON object with the following structure:
        {{
            "summary_text": "Summary of the video...",
            "key_points": ["Point 1", "Point 2", ...],
            "topics": ["Topic 1", "Topic 2", ...]
        }}
        
        The summary should be informative and capture the essence of the educational content.
        """
        
        # Handle large transcripts by chunking
        MAX_CHUNK_SIZE = 7500  # Reserve some space for the prompt
        if len(transcript) > MAX_CHUNK_SIZE:
            # Use the first chunk, which likely contains the most important information
            transcript_chunk = transcript[:MAX_CHUNK_SIZE] + "\n[Note: This is a portion of the full transcript due to length constraints]"
        else:
            transcript_chunk = transcript
        
        user_prompt = f"""
        Video Title: {video_info.get('title', 'Unknown')}
        Video Channel: {video_info.get('channel', 'Unknown')}
        
        Transcript:
        {transcript_chunk}
        
        Please provide a {summary_length.lower()} summary of this video content.
        """
        
        try:
            # Use Google ADK API to generate summary
            summary_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.5
            )
            
            # Try to parse the JSON response
            try:
                # Clean the response text - remove any markdown code block indicators
                if "```" in summary_text:
                    # Get the content between code fences if present
                    parts = summary_text.split("```")
                    if len(parts) >= 3:  # At least one full code block
                        # Take the content within the first code block
                        # This skips the first part (before ````json) and takes what's between the backticks
                        summary_text = parts[1]
                        # Remove language identifier if exists
                        if summary_text.startswith("json"):
                            summary_text = summary_text[4:].strip()
                    else:
                        # Handle case where there's only an opening code fence
                        summary_text = parts[-1].strip()
                
                # Now parse the cleaned text
                summary = json.loads(summary_text)
                
                # Ensure we have all expected fields
                if "summary_text" not in summary:
                    summary["summary_text"] = "Summary not available."
                
                if "key_points" not in summary or not summary["key_points"]:
                    summary["key_points"] = ["Key points not available."]
                    
                if "topics" not in summary or not summary["topics"]:
                    summary["topics"] = ["Topics not available."]
                    
                return summary
                
            except json.JSONDecodeError as json_err:
                # If JSON parsing fails, create a structured error response
                print(f"JSON parsing error: {str(json_err)}")
                print(f"Raw text: {summary_text[:150]}...")
                
                return {
                    'summary_text': "Unable to generate summary: Invalid response format.",
                    'key_points': [
                        "Error parsing AI response",
                        f"JSON error: {str(json_err)}",
                        f"Raw response: {summary_text[:100]}..."
                    ],
                    'topics': ["Error: Response Formatting Issue"]
                }
            
        except Exception as e:
            # Provide a more detailed error message
            error_type = type(e).__name__
            error_message = str(e)
            
            return {
                'summary_text': f"Unable to generate summary due to an error: {error_type}",
                'key_points': [
                    f"Error: {error_message[:100]}",
                    "This may be due to API rate limits, connection issues, or content policies",
                    "Please try again with a different video or transcript"
                ],
                'topics': ["Error: " + error_type]
            }
            
    def refine_summary(self, summary, feedback):
        """
        Refine the summary based on user feedback.
        
        Args:
            summary (dict): Existing summary
            feedback (str): User feedback
            
        Returns:
            dict: Refined summary
        """
        try:
            # System prompt for refining summary
            system_prompt = """
            You are an expert educational content summarizer. Your task is to refine an existing summary
            based on user feedback. Incorporate the feedback while maintaining clarity and conciseness.
            
            Format your response as a JSON object with the following structure:
            {
                "summary_text": "Refined summary of the video...",
                "key_points": ["Refined Point 1", "Refined Point 2", ...],
                "topics": ["Topic 1", "Topic 2", ...]
            }
            """
            
            # Create prompt for summary refinement
            user_prompt = f"""
            Original Summary:
            {summary.get('summary_text', 'No summary available.')}
            
            Original Key Points:
            {', '.join(summary.get('key_points', ['No key points available.']))}
            
            Original Topics:
            {', '.join(summary.get('topics', ['No topics available.']))}
            
            User Feedback:
            {feedback}
            
            Please refine the summary based on this feedback.
            """
            
            # Use Google ADK Gemini API to refine summary
            refined_summary_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.5
            )
            
            # Try to parse the JSON response
            try:
                refined_summary = json.loads(refined_summary_text)
                
                # Ensure we have all expected fields
                if "summary_text" not in refined_summary:
                    refined_summary["summary_text"] = summary.get("summary_text", "Summary not available.")
                
                if "key_points" not in refined_summary or not refined_summary["key_points"]:
                    refined_summary["key_points"] = summary.get("key_points", ["Key points not available."])
                    
                if "topics" not in refined_summary or not refined_summary["topics"]:
                    refined_summary["topics"] = summary.get("topics", ["Topics not available."])
                    
                return refined_summary
                
            except json.JSONDecodeError:
                print(f"Error parsing refined summary JSON: {refined_summary_text[:100]}...")
                return summary
            
        except Exception as e:
            # Return original summary if refinement fails
            print(f"Error refining summary: {str(e)}")
            return summary
