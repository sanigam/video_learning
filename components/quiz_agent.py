import os
import json
from utils.google_adk_manager import GoogleADKManager

class QuizAgent:
    def __init__(self):
        """Initialize the QuizAgent class."""
        self.adk_manager = GoogleADKManager()
        
    def generate_quiz(self, transcript, video_info, num_questions=5, difficulty="Medium"):
        """
        Generate quiz questions based on video transcript.
        
        Args:
            transcript (str): Video transcript
            video_info (dict): Information about the video
            num_questions (int): Number of questions to generate
            difficulty (str): Difficulty level ('Easy', 'Medium', 'Hard')
            
        Returns:
            list: List of question dictionaries
        """
        # System prompt for quiz generation
        system_prompt = f"""
        You are an expert educational quiz creator. Your task is to create engaging, 
        informative multiple-choice questions based on video content.
        
        For each question:
        1. Create a clear, concise question
        2. Provide 4 possible answers as an array of strings
        3. Indicate which answer is correct (the exact string from the options array)
        4. Provide brief explanatory feedback for correct and incorrect answers
        
        Adapt the questions to be {difficulty.lower()} difficulty level.
        
        Format your response as a JSON array of question objects, where each object has the following structure:
        [
            {{
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option B",
                "correct_feedback": "Feedback for correct answer",
                "incorrect_feedback": "Feedback for incorrect answer"
            }},
            // more questions...
        ]
        """
        
        user_prompt = f"""
        Video Title: {video_info.get('title', 'Unknown')}
        Video Channel: {video_info.get('channel', 'Unknown')}
        
        Transcript:
        {transcript[:8000]}  # Limit transcript length for API
        
        Please create {num_questions} {difficulty.lower()} difficulty multiple-choice questions based on this content.
        """
        
        try:
            # Use Google ADK API to generate quiz questions
            questions_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.7
            )
            
            questions_data = json.loads(questions_text)
            
            # Extract questions from the response
            if "questions" in questions_data:
                questions = questions_data["questions"]
            else:
                # If the model didn't use the "questions" key, assume the entire object is the array
                questions = questions_data
            
            if isinstance(questions, list):
                # Verify that questions have the correct format
                processed_questions = []
                for q in questions[:num_questions]:
                    if not all(key in q for key in ["question", "options", "correct_answer", "correct_feedback", "incorrect_feedback"]):
                        continue
                    
                    processed_questions.append(q)
                
                return processed_questions
            else:
                # Fallback to mock data if format is incorrect
                raise ValueError("Response format incorrect")
            
        except Exception as e:
            # Fallback to sample questions if there's an error
            sample_questions = [
                {
                    "question": "What is the main concept discussed in the video?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option B",
                    "correct_feedback": "That's correct! The video primarily focuses on Option B.",
                    "incorrect_feedback": "Not quite. The video primarily discusses Option B."
                },
                {
                    "question": "According to the video, which technique is most effective?",
                    "options": ["Technique 1", "Technique 2", "Technique 3", "Technique 4"],
                    "correct_answer": "Technique 3",
                    "correct_feedback": "Correct! The video demonstrates that Technique 3 is most effective.",
                    "incorrect_feedback": "Actually, the video specifically shows Technique 3 to be most effective."
                }
            ]
            
            # Generate the requested number of questions
            questions = sample_questions * (num_questions // 2 + 1)
            return questions[:num_questions]
            
    def evaluate_answer(self, question, user_answer):
        """
        Evaluate a user's answer to a quiz question.
        
        Args:
            question (dict): Question information
            user_answer (str): User's answer
            
        Returns:
            dict: Evaluation results
        """
        correct = user_answer == question['correct_answer']
        
        feedback = question['correct_feedback'] if correct else question['incorrect_feedback']
        
        return {
            'correct': correct,
            'feedback': feedback
        }
