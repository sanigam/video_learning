# filepath: /Users/sanigam/Desktop/Work/hack_jun_2025/components/learning_path_agent.py
import os
import json
from utils.google_adk_manager import GoogleADKManager

class LearningPathAgent:
    def __init__(self):
        """Initialize the LearningPathAgent class."""
        self.adk_manager = GoogleADKManager()
        self.user_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users")
        # Ensure user data directory exists
        os.makedirs(self.user_data_dir, exist_ok=True)
        
    def generate_recommendations(self, interests=None, goals=None, learning_style=None, user_progress=0, video_history=None, skill_level="Beginner", completed_milestones=None):
        """
        Generate personalized learning recommendations.
        
        Args:
            interests (list): User's learning interests
            goals (str): User's learning goals
            learning_style (str): User's preferred learning style
            user_progress (int): User's current progress (0-100)
            video_history (list): List of previously watched videos
            skill_level (str): User's skill level (Beginner, Intermediate, Advanced)
            completed_milestones (list): List of milestones the user has completed
            
        Returns:
            dict: Personalized recommendations
        """
        if interests is None:
            interests = []
        
        if video_history is None:
            video_history = []
            
        if completed_milestones is None:
            completed_milestones = []
            
        # System prompt for personalized recommendations
        system_prompt = f"""
        You are an expert educational advisor specializing in personalized learning paths.
        Your task is to create a tailored learning plan based on the user's interests, goals, learning preferences, and current skill level.
        
        Create recommendations that:
        1. Match the user's stated interests
        2. Help achieve their learning goals
        3. Align with their preferred learning style ({learning_style if learning_style else 'Visual'})
        4. Consider their current progress level ({user_progress}%)
        5. Build upon their previous learning (videos they've already watched)
        6. Are appropriate for their skill level: {skill_level}
        7. Account for milestones they've already completed
        
        Format your response as a JSON object with the following structure:
        {{
            "next_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
            "recommended_videos": [
                {{
                    "id": "unique_id",
                    "title": "Video Title",
                    "channel": "Channel Name",
                    "url": "Video URL",
                    "reason": "Reason for recommendation",
                    "category": "Subject category (e.g., Programming, Math, Physics, etc.)",
                    "difficulty": "Beginner/Intermediate/Advanced",
                    "duration_minutes": estimated_duration_in_minutes
                }},
                // more videos...
            ],
            "additional_resources": [
                {{
                    "id": "unique_id",
                    "title": "Resource Title",
                    "type": "Book/Article/Course/Tool/Website",
                    "url": "Resource URL if applicable",
                    "description": "Brief description of the resource",
                    "reason": "Why this resource is recommended"
                }},
                // more resources...
            ],
            "milestones": [
                {{
                    "id": "milestone_id",
                    "name": "Milestone Name",
                    "progress": progress_percentage,
                    "objective": "What the user will learn/achieve with this milestone",
                    "estimated_completion_hours": estimated_hours_to_complete
                }},
                // more milestones...
            ],
            "skill_assessments": [
                {{
                    "skill": "Specific skill name",
                    "current_level": "Beginner/Intermediate/Advanced",
                    "next_goal": "Next proficiency goal for this skill",
                    "recommended_practice": "Specific practice activity"
                }},
                // more skill assessments...
            ]
        }}
        """
        
        user_prompt = f"""
        User Interests: {', '.join(interests) if interests else 'Not specified'}
        Learning Goals: {goals if goals else 'Not specified'}
        Learning Style: {learning_style if learning_style else 'Visual'}
        Current Progress: {user_progress}%
        Skill Level: {skill_level}
        
        Previously watched videos:
        {', '.join([video.get('title', 'Unknown Video') for video in video_history]) if video_history else 'None'}
        
        Completed milestones:
        {', '.join(completed_milestones) if completed_milestones else 'None'}
        
        Please create a comprehensive personalized learning path for this user with:
        1. 3-5 specific next steps to progress their learning
        2. 4-6 recommended videos that match their interests, goals, and skill level
        3. 2-3 additional learning resources beyond videos (books, articles, courses, tools, websites)
        4. 3-5 learning milestones with clear objectives and estimated completion time
        5. 2-3 skill assessments with current and target skill levels
        """
        
        try:
            # Use Google ADK API to generate recommendations
            recommendations_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.7
            )
            
            recommendations = json.loads(recommendations_text)
            
            # Ensure we have all expected fields
            if "next_steps" not in recommendations or not recommendations["next_steps"]:
                recommendations["next_steps"] = [
                    "Complete introductory content in your area of interest",
                    "Practice applying concepts with hands-on exercises",
                    "Review and solidify your understanding of core concepts",
                    "Work through a beginner-friendly project",
                    "Join a community of practice to share your learning"
                ]
            
            if "recommended_videos" not in recommendations or not recommendations["recommended_videos"]:
                recommendations["recommended_videos"] = [
                    {
                        'id': 'video1',
                        'title': 'Introduction to Machine Learning',
                        'channel': 'Tech Learning',
                        'url': 'https://www.youtube.com/watch?v=example1',
                        'reason': 'Aligns with your learning interests',
                        'category': 'Computer Science',
                        'difficulty': skill_level,
                        'duration_minutes': 15
                    },
                    {
                        'id': 'video2',
                        'title': 'Neural Networks Explained',
                        'channel': 'Data Science Basics',
                        'url': 'https://www.youtube.com/watch?v=example2',
                        'reason': 'Helps achieve your learning goals',
                        'category': 'Computer Science',
                        'difficulty': skill_level,
                        'duration_minutes': 20
                    }
                ]
            
            if "additional_resources" not in recommendations:
                recommendations["additional_resources"] = [
                    {
                        'id': 'resource1',
                        'title': 'Beginner\'s Guide to Data Science',
                        'type': 'Book',
                        'url': 'https://example.com/book1',
                        'description': 'A comprehensive introduction to data science concepts',
                        'reason': 'Perfect for beginners to build a solid foundation'
                    },
                    {
                        'id': 'resource2',
                        'title': 'Interactive Python Course',
                        'type': 'Course',
                        'url': 'https://example.com/course1',
                        'description': 'Hands-on Python programming course',
                        'reason': 'Practical coding experience to reinforce concepts'
                    }
                ]
                
            if "milestones" not in recommendations or not recommendations["milestones"]:
                recommendations["milestones"] = [
                    {
                        'id': 'milestone1',
                        'name': 'Beginner Concepts',
                        'progress': 75,
                        'objective': 'Understand fundamental principles in your area of interest',
                        'estimated_completion_hours': 5
                    },
                    {
                        'id': 'milestone2',
                        'name': 'Intermediate Knowledge',
                        'progress': 40,
                        'objective': 'Apply basic concepts to solve practical problems',
                        'estimated_completion_hours': 10
                    },
                    {
                        'id': 'milestone3',
                        'name': 'Advanced Applications',
                        'progress': 10,
                        'objective': 'Develop expertise in specific advanced topics',
                        'estimated_completion_hours': 15
                    }
                ]
                
            if "skill_assessments" not in recommendations:
                recommendations["skill_assessments"] = [
                    {
                        'skill': 'Basic Understanding',
                        'current_level': skill_level,
                        'next_goal': 'Intermediate proficiency',
                        'recommended_practice': 'Complete a small project applying the concepts'
                    },
                    {
                        'skill': 'Practical Application',
                        'current_level': skill_level,
                        'next_goal': 'Consistent problem-solving ability',
                        'recommended_practice': 'Solve practice exercises related to the topic'
                    }
                ]
            
            return recommendations
            
        except Exception as e:
            # Fallback to basic recommendations if there's an error
            return {
                'next_steps': [
                    "Start with fundamentals in your area of interest",
                    "Watch introductory videos on the subject",
                    "Practice with simple exercises to reinforce learning",
                    "Join online forums or communities in your field",
                    "Set specific learning goals with deadlines"
                ],
                'recommended_videos': [
                    {
                        'id': 'fallback1',
                        'title': 'Introduction to the Subject',
                        'channel': 'Educational Channel',
                        'url': 'https://www.youtube.com/watch?v=example1',
                        'reason': 'Good starting point for beginners',
                        'category': 'General Education',
                        'difficulty': 'Beginner',
                        'duration_minutes': 15
                    },
                    {
                        'id': 'fallback2',
                        'title': 'Core Concepts Explained',
                        'channel': 'Learning Hub',
                        'url': 'https://www.youtube.com/watch?v=example2',
                        'reason': 'Covers essential knowledge',
                        'category': 'General Education',
                        'difficulty': 'Beginner',
                        'duration_minutes': 20
                    }
                ],
                'additional_resources': [
                    {
                        'id': 'fallbackres1',
                        'title': 'Beginner\'s Guide',
                        'type': 'Article',
                        'url': 'https://example.com/beginners-guide',
                        'description': 'A comprehensive introduction to the subject',
                        'reason': 'Gives you a solid foundation'
                    },
                    {
                        'id': 'fallbackres2',
                        'title': 'Practice Exercises',
                        'type': 'Website',
                        'url': 'https://example.com/exercises',
                        'description': 'Interactive exercises to practice skills',
                        'reason': 'Hands-on practice is essential for learning'
                    }
                ],
                'milestones': [
                    {
                        'id': 'fallbackmile1',
                        'name': 'Basic Understanding',
                        'progress': 50,
                        'objective': 'Grasp fundamental concepts of the subject',
                        'estimated_completion_hours': 5
                    },
                    {
                        'id': 'fallbackmile2',
                        'name': 'Practical Application',
                        'progress': 25,
                        'objective': 'Apply concepts to solve simple problems',
                        'estimated_completion_hours': 10
                    }
                ],
                'skill_assessments': [
                    {
                        'skill': 'Subject Knowledge',
                        'current_level': 'Beginner',
                        'next_goal': 'Intermediate understanding',
                        'recommended_practice': 'Complete online quizzes on the topic'
                    }
                ]
            }
            
    def save_user_data(self, email, user_settings, learning_path):
        """
        Save user settings and personalized learning path.
        
        Args:
            email (str): User's email address
            user_settings (dict): User's settings
            learning_path (dict): User's personalized learning path
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not email:
            return False
            
        try:
            # Create a sanitized filename from email
            filename = email.replace('@', '_at_').replace('.', '_dot_') + '.json'
            file_path = os.path.join(self.user_data_dir, filename)
            
            user_data = {
                'email': email,
                'settings': user_settings,
                'learning_path': learning_path,
                'auth_source': user_settings.get('auth_source', 'direct')
            }
            
            with open(file_path, 'w') as f:
                json.dump(user_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving user data: {str(e)}")
            return False
    
    def load_user_data(self, email):
        """
        Load user settings and personalized learning path.
        
        Args:
            email (str): User's email address
        
        Returns:
            dict: User data including settings and learning path, or None if not found
        """
        if not email:
            return None
            
        try:
            # Create a sanitized filename from email
            filename = email.replace('@', '_at_').replace('.', '_dot_') + '.json'
            file_path = os.path.join(self.user_data_dir, filename)
            
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r') as f:
                user_data = json.load(f)
                
            return user_data
        except Exception as e:
            print(f"Error loading user data: {str(e)}")
            return None
    
    def is_auth_email(self, user_settings):
        """
        Check if user's email came from IAP/Google authentication.
        
        Args:
            user_settings (dict): User's settings
        
        Returns:
            bool: True if email came from authentication, False otherwise
        """
        # Check auth_source in user settings
        auth_source = user_settings.get('auth_source', '')
        return auth_source.lower() in ['google', 'iap', 'oauth']
    
    def can_change_email(self, user_settings):
        """
        Check if user is allowed to change their email.
        
        Args:
            user_settings (dict): User's settings
        
        Returns:
            bool: True if user can change email, False otherwise
        """
        return not self.is_auth_email(user_settings)
    
    def update_email(self, old_email, new_email, user_settings):
        """
        Update user's email if allowed.
        
        Args:
            old_email (str): User's current email
            new_email (str): User's requested new email
            user_settings (dict): User's settings
        
        Returns:
            tuple: (bool success, str message)
        """
        if not self.can_change_email(user_settings):
            return False, "Email cannot be changed for accounts authenticated through Google/IAP."
            
        try:
            # Load existing user data
            user_data = self.load_user_data(old_email)
            if not user_data:
                return False, "User data not found."
                
            # Update email in user_data
            user_data['email'] = new_email
            user_settings['email'] = new_email
            
            # Save with new email
            success = self.save_user_data(new_email, user_settings, user_data.get('learning_path', {}))
            if not success:
                return False, "Failed to save user data with new email."
                
            # Remove old file
            old_filename = old_email.replace('@', '_at_').replace('.', '_dot_') + '.json'
            old_file_path = os.path.join(self.user_data_dir, old_filename)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
                
            return True, "Email updated successfully."
            
        except Exception as e:
            return False, f"Error updating email: {str(e)}"
    
    def get_or_create_user_data(self, email, default_settings=None):
        """
        Get existing user data or create new data if not found.
        
        Args:
            email (str): User's email address
            default_settings (dict): Default user settings if new user
            
        Returns:
            dict: User data including settings and learning path
        """
        if not default_settings:
            default_settings = {
                'email': email,
                'auth_source': 'direct',
                'learning_style': 'Visual',
                'skill_level': 'Beginner',
                'interests': []
            }
            
        user_data = self.load_user_data(email)
        if user_data:
            return user_data
            
        # Create new user data
        new_user_data = {
            'email': email,
            'settings': default_settings,
            'learning_path': {}
        }
        
        # Save new user data
        self.save_user_data(email, default_settings, {})
        
        return new_user_data
    
    def update_recommendations(self, current_recommendations, new_activity):
        """
        Update recommendations based on new user activity.
        
        Args:
            current_recommendations (dict): Current recommendations
            new_activity (dict): New user activity data
            
        Returns:
            dict: Updated recommendations
        """
        try:
            # System prompt for updating recommendations
            system_prompt = """
            You are an expert educational advisor specializing in personalized learning paths.
            Your task is to update an existing learning path based on new user activity.
            
            Format your response as a JSON object with the same structure as the input recommendations:
            {
                "next_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
                "recommended_videos": [
                    {
                        "id": "unique_id",
                        "title": "Video Title",
                        "channel": "Channel Name",
                        "url": "Video URL",
                        "reason": "Reason for recommendation"
                    },
                    // more videos...
                ],
                "milestones": [
                    {
                        "name": "Milestone Name",
                        "progress": progress_percentage
                    },
                    // more milestones...
                ]
            }
            """
            
            # Extract current recommendations
            current_next_steps = current_recommendations.get('next_steps', [])
            current_videos = current_recommendations.get('recommended_videos', [])
            current_milestones = current_recommendations.get('milestones', [])
            
            # Format activity information
            activity_type = new_activity.get('type', '')
            activity_data = new_activity.get('data', {})
            
            # Prepare the user prompt
            user_prompt = f"""
            Current Learning Path:
            - Next Steps: {', '.join(current_next_steps)}
            - Recommended Videos: {', '.join([v.get('title', 'Unknown') for v in current_videos])}
            - Milestones: {', '.join([f"{m.get('name', 'Unknown')}: {m.get('progress', 0)}%" for m in current_milestones])}
            
            New User Activity:
            - Activity Type: {activity_type}
            - Details: {activity_data}
            
            Please update the learning path based on this new activity. For example:
            - If they completed a video, mark related milestone progress higher
            - If they started a new topic, suggest more videos on that topic
            - If they're struggling, suggest more fundamental content
            
            Return the updated learning path.
            """
            
            # Use Google ADK API to update recommendations
            updated_recommendations_text = self.adk_manager.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.5
            )
            
            updated_recommendations = json.loads(updated_recommendations_text)
            
            # Ensure we have all expected fields
            if "next_steps" not in updated_recommendations:
                updated_recommendations["next_steps"] = current_next_steps
            
            if "recommended_videos" not in updated_recommendations:
                updated_recommendations["recommended_videos"] = current_videos
                
            if "milestones" not in updated_recommendations:
                updated_recommendations["milestones"] = current_milestones
                
            return updated_recommendations
            
        except Exception as e:
            # Return original recommendations if update fails
            print(f"Error updating recommendations: {str(e)}")
            return current_recommendations
