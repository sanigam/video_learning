import streamlit as st
import os
import json
from pathlib import Path
from glob import glob

def get_iap_email():
    """
    Get the user email from Google Identity-Aware Proxy (IAP) headers.
    
    Returns:
        str or None: The authenticated user's email if available, None otherwise
    """
    try:
        # Use st.context.headers (recommended approach) with fallback to deprecated method
        try:
            # Modern Streamlit versions (>1.22.0)
            headers = st.context.headers
        except (AttributeError, ImportError):
            # Fallback for older Streamlit versions
            try:
                from streamlit.web.server.websocket_headers import _get_websocket_headers
                headers = _get_websocket_headers()
                print("Warning: Using deprecated _get_websocket_headers(). Update Streamlit version.")
            except ImportError:
                print("Could not access request headers through any method.")
                return None
        
        user_email = headers.get('X-Goog-Authenticated-User-Email')
        
        if user_email:
            # The value is typically in the format 'accounts.google.com:email@example.com'
            return user_email.split(':', 1)[-1]
    except Exception as e:
        print(f"Error retrieving IAP email: {str(e)}")
    
    return None

def check_app_engine_user():
    """
    Check for authenticated user in App Engine environment and set session state.
    
    This function uses IAP headers to get the authenticated user's email
    and updates the session state if a user is found.
    
    Returns:
        bool: True if a user was found and loaded, False otherwise
    """
    # First try the IAP header method
    email = get_iap_email()
    
    # If that fails, try environment variables (older App Engine approach)
    if not email:
        email = os.environ.get('USER_EMAIL')
    
    if email:
        print(f"Found authenticated user: {email}")
        
        # Check if the session is new or if the user has changed
        is_new_session = 'user_email' not in st.session_state
        is_different_user = (not is_new_session and st.session_state.user_email != email)
        
        # Update session state with the authenticated email
        if is_new_session or is_different_user:
            # If we're detecting a different user, it might be due to a session change
            if is_different_user:
                print(f"User changed from {st.session_state.user_email} to {email}")
                
            # Set the user email in session state
            st.session_state.user_email = email
        
        # Load any existing settings for this user
        return check_and_load_user_settings(email)
    
    return False

def check_and_load_user_settings(email=None):
    """
    Check for existing user settings files and load if email matches.
    If email is None, try to use the email from session state.
    
    Args:
        email (str, optional): User email to look for
    
    Returns:
        bool: True if settings were loaded, False otherwise
    """
    if email is None:
        # Try to get email from session state
        email = st.session_state.get('user_email', '')
    
    # If no email provided or in session state, can't load user-specific settings
    if not email:
        return False
    
    # Generate the expected filename for this email
    sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
    user_settings_file = f"user_settings_{sanitized_email}.json"
    
    # Check if the file exists
    if os.path.exists(user_settings_file):
        try:
            # Load the settings
            with open(user_settings_file, 'r') as f:
                settings = json.load(f)
            
            # Update session state with these settings
            for key, value in settings.items():
                st.session_state[key] = value
            
            print(f"Loaded settings for user: {email}")
            return True
        except Exception as e:
            print(f"Error loading settings for {email}: {str(e)}")
            return False
    
    # Check for App Engine environment variables that might indicate a logged-in user
    # This is a placeholder for when deployed on App Engine
    app_engine_email = os.environ.get('USER_EMAIL')
    if app_engine_email and app_engine_email == email:
        print(f"Detected App Engine user: {app_engine_email}")
        # You would add App Engine specific logic here
        return True
    
    return False

def initialize_session_state():
    """
    Initialize session state variables if they don't exist.
    """
    # Check for App Engine user when deployed
    try:
        check_app_engine_user()
    except:
        # Not running in App Engine, continue without login
        pass
    
    # Check for existing user settings files to load
    # Look for any user settings file
    user_settings_files = glob("user_settings_*.json")
    if user_settings_files:
        # Take the most recently modified file
        latest_file = max(user_settings_files, key=os.path.getmtime)
        try:
            with open(latest_file, 'r') as f:
                settings = json.load(f)
                # Update session state with these settings
                for key, value in settings.items():
                    st.session_state[key] = value
            print(f"Loaded settings from: {latest_file}")
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
    
    # Video processing variables
    if 'video_url' not in st.session_state:
        st.session_state.video_url = ""
        
    if 'processed_video_url' not in st.session_state:
        st.session_state.processed_video_url = ""
        
    if 'video_info' not in st.session_state:
        st.session_state.video_info = None
        
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
        
    # Summary variables
    if 'summary' not in st.session_state:
        st.session_state.summary = None
        
    # Quiz variables
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
        
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
        
    if 'quiz_feedback' not in st.session_state:
        st.session_state.quiz_feedback = {}
        
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
        
    # Flashcard variables
    if 'flashcards' not in st.session_state:
        st.session_state.flashcards = None
        
    if 'current_flashcard' not in st.session_state:
        st.session_state.current_flashcard = 0
        
    # Learning path variables
    if 'user_progress' not in st.session_state:
        st.session_state.user_progress = 0
        
    if 'learning_recommendations' not in st.session_state:
        st.session_state.learning_recommendations = None
    
    if 'skill_level' not in st.session_state:
        st.session_state.skill_level = "Beginner"
        
    # AI model settings
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = "gemini-1.5-flash"
        
    # Video overview
    if 'video_overview' not in st.session_state:
        st.session_state.video_overview = None
        
    # Video overview
    if 'video_overview' not in st.session_state:
        st.session_state.skill_level = "Beginner"
    
    if 'completed_milestones' not in st.session_state:
        st.session_state.completed_milestones = []
    
    if 'watched_videos' not in st.session_state:
        st.session_state.watched_videos = []
    
    if 'learning_categories' not in st.session_state:
        st.session_state.learning_categories = {}
    
    if 'preferred_learning_style' not in st.session_state:
        st.session_state.preferred_learning_style = "Visual"
        
    # Navigation control (separate from the widget)
    if 'next_page' not in st.session_state:
        st.session_state.next_page = None
        
    # Chat assistant variables
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your learning assistant. How can I help you with your video learning today?"}
        ]
        
    # User settings
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
        
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
        
    # Video history tracking
    if 'video_history' not in st.session_state:
        st.session_state.video_history = []
