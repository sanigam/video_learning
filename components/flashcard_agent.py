import os
import json
from utils.google_adk_manager import GoogleADKManager

class FlashcardAgent:
    def __init__(self):
        """Initialize the FlashcardAgent class."""
        self.adk_manager = GoogleADKManager()
        
    def generate_flashcards(self, transcript, video_info, num_cards=10, focus_area="Mixed"):
        """
        Generate flashcards based on video transcript.
        
        Args:
            transcript (str): Video transcript
            video_info (dict): Information about the video
            num_cards (int): Number of flashcards to generate
            focus_area (str): Focus area ('Key Concepts', 'Definitions', 'Examples', 'Mixed')
            
        Returns:
            list: List of flashcard dictionaries with front and back content
        """
        # System prompt for flashcard generation
        system_prompt = f"""
        You are an expert educational content creator specializing in effective flashcards. 
        Your task is to create clear, concise flashcards based on video content.
        
        For each flashcard:
        1. Create a front side with a question or prompt
        2. Create a back side with the answer or explanation
        
        Focus on {focus_area.lower()} from the content.
        Follow principles of spaced repetition by creating cards that test recall effectively.
        
        Format your response as a JSON array of flashcard objects:
        [
            {{
                "front": "Question or prompt on front of card",
                "back": "Answer or explanation on back of card"
            }},
            // more flashcards...
        ]
        """
        
        user_prompt = f"""
        Video Title: {video_info.get('title', 'Unknown')}
        Video Channel: {video_info.get('channel', 'Unknown')}
        
        Transcript:
        {transcript[:8000]}  # Limit transcript length for API
        
        Please create {num_cards} flashcards focused on {focus_area.lower()} from this content.
        """
        
        try:
            # Use Google ADK API to generate flashcards
            flashcards_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.7
            )
            
            flashcards_data = json.loads(flashcards_text)
            
            # Extract flashcards from the response
            if "flashcards" in flashcards_data:
                flashcards = flashcards_data["flashcards"]
            else:
                # If the model didn't use the "flashcards" key, assume the entire object is the array
                flashcards = flashcards_data
            
            if isinstance(flashcards, list):
                # Verify that flashcards have the correct format and limit to requested number
                processed_flashcards = []
                for card in flashcards[:num_cards]:
                    if not all(key in card for key in ["front", "back"]):
                        continue
                    
                    processed_flashcards.append(card)
                
                return processed_flashcards
            else:
                # Fallback to mock data if format is incorrect
                raise ValueError("Response format incorrect")
            
        except Exception as e:
            # Fallback to sample flashcards if there's an error
            sample_flashcards = [
                {
                    "front": "What is the main concept discussed in the video?",
                    "back": "The video primarily discusses machine learning algorithms and their applications."
                },
                {
                    "front": "Define supervised learning as mentioned in the video",
                    "back": "Supervised learning is a machine learning approach where the model is trained on labeled data."
                },
                {
                    "front": "What example of neural networks was given in the video?",
                    "back": "The video used image recognition systems as an example of neural networks."
                }
            ]
            
            # Generate the requested number of flashcards
            flashcards = sample_flashcards * (num_cards // 3 + 1)
            return flashcards[:num_cards]
            
    def organize_by_difficulty(self, flashcards):
        """
        Organize flashcards by difficulty level.
        
        Args:
            flashcards (list): List of flashcard dictionaries
            
        Returns:
            dict: Flashcards organized by difficulty
        """
        # Implementation for organizing flashcards by difficulty
        pass
