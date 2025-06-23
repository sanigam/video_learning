import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
import time

# Import our custom modules
from components.video_processor import VideoProcessor
from components.summarizer_agent import SummarizerAgent
from components.quiz_agent import QuizAgent
from components.flashcard_agent import FlashcardAgent
from components.learning_path_agent import LearningPathAgent
from components.chat_assistant_agent import ChatAssistantAgent
from components.user_settings import UserSettings
from utils.session_state import initialize_session_state

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CognitoStream: AI-Enhanced Video Learning Platform",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
def load_css():
    css = """
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .section-header {
            font-size: 1.5rem;
            color: #1E3A8A;
            margin-top: 1rem;
            margin-bottom: 1rem;
            font-weight: bold;
        }
        .card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8f9fa;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
        }
        .info-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #e9f5ff;
            margin-bottom: 1rem;
        }
        .success-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d1e7dd;
            margin-bottom: 1rem;
        }
        .warning-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #fff3cd;
            margin-bottom: 1rem;
        }
        .sidebar-content {
            padding: 1rem;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Initialize app
def main():
    # Load custom CSS
    load_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Check for IAP authentication
    from utils.session_state import get_iap_email, check_app_engine_user
    
    # First try to use the dedicated function that handles all App Engine auth scenarios
    iap_authenticated = check_app_engine_user()
    
    # If that didn't work but we still need authentication, try direct approach
    if not iap_authenticated and not st.session_state.get('user_email'):
        iap_email = get_iap_email()
        if iap_email:
            st.session_state.user_email = iap_email
            print(f"Automatically authenticated with IAP email: {iap_email}")
            iap_authenticated = True
    
    # Load user settings based on email if available
    if st.session_state.get('user_email'):
        user_settings = UserSettings()
        email = st.session_state.user_email
        
        # Try to load settings for this email
        settings = user_settings.load_settings_by_email(email)
        
        # Apply these settings to session state
        for key, value in settings.items():
            # Always update email and explicitly defined learning preference keys
            learning_preference_keys = [
                'learning_interests', 'learning_goals', 'preferred_learning_style', 
                'skill_level', 'learning_recommendations', 'completed_milestones', 
                'user_progress', 'learning_path'
            ]
            
            if key not in st.session_state or key == 'user_email' or key in learning_preference_keys:
                st.session_state[key] = value
                
        # Log successful settings load
        if iap_authenticated:
            print(f"Loaded settings for authenticated user: {email}")
        else:
            print(f"Loaded settings for manually entered email: {email}")
    
    # Initialize the AI model with the selected model from session state
    from utils.google_adk_manager import GoogleADKManager
    adk_manager = GoogleADKManager()
    adk_manager.set_model(st.session_state.ai_model)
    
    # Handle programmatic navigation changes
    if st.session_state.next_page is not None:
        initial_page = st.session_state.next_page
        st.session_state.next_page = None
    else:
        initial_page = st.session_state.get("navigation_value", "Video Processing")
    
    # Display header
    st.markdown("<div class='main-header'>CognitoStream: AI-Enhanced Video Learning Platform</div>", unsafe_allow_html=True)
    
    # Sidebar for navigation and user settings
    with st.sidebar:
        #put logo at the top
        st.image("logo.png", width=200)
        st.markdown("<div class='section-header'>Navigation</div>", unsafe_allow_html=True)
        
        # Navigation options
        page = st.radio(
            "Select Feature",
            [
                "Video Processing", 
                "Video Summaries", 
                "Interactive Quizzes", 
                "Flashcards",
                "Personalized Learning Path",
                "Chat Assistant",
                "User Settings"
            ],
            key="navigation",
            index=[
                "Video Processing", 
                "Video Summaries", 
                "Interactive Quizzes", 
                "Flashcards",
                "Personalized Learning Path",
                "Chat Assistant",
                "User Settings"
            ].index(initial_page)
        )
        # Store the current value
        st.session_state.navigation_value = page
        
        # AI Model Settings
        st.markdown("---")
        st.markdown("<div class='section-header'>AI Model Settings</div>", unsafe_allow_html=True)
        
        # Model selection dropdown
        model_options = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        
        # Initialize model in session state if not present
        if 'ai_model' not in st.session_state:
            st.session_state.ai_model = "gemini-1.5-flash"
            
        selected_model = st.selectbox(
            "AI Model",
            options=model_options,
            index=model_options.index(st.session_state.ai_model),
            help="Select the Gemini model to use for AI tasks"
        )
        
        # Update the model if changed
        if selected_model != st.session_state.ai_model:
            st.session_state.ai_model = selected_model
            from utils.google_adk_manager import GoogleADKManager
            adk_manager = GoogleADKManager()
            adk_manager.set_model(selected_model)
            st.success(f"Model updated to {selected_model}")
        
        # Display user info if available
        if st.session_state.get('user_email') or st.session_state.get('user_name'):
            st.markdown("---")
            # Prioritize email for identification but use name for display if available
            user_identifier = st.session_state.get('user_email', '')
            # If no name is provided, use the part before @ in the email
            display_name = st.session_state.get('user_name', '') or (user_identifier.split('@')[0] if user_identifier else 'User')
            st.markdown(f"**Welcome, {display_name}!**")
            if st.session_state.get('user_progress'):
                st.progress(st.session_state.user_progress / 100.0)
                st.write(f"Learning Progress: {st.session_state.user_progress}%")
        
        # Add footer to the sidebar
        st.markdown("---")
        st.markdown("Made with ❤️ for Education.")
        st.markdown("<div style='font-size: 0.8em; color: gray; margin-top: 15px;'>© 2025 AI-Enhanced Video Learning Platform. All rights reserved.</div>", unsafe_allow_html=True)
    
    # Main content based on navigation
    if page == "Video Processing":
        display_video_processing()
    elif page == "Video Summaries":
        display_video_summaries()
    elif page == "Interactive Quizzes":
        display_quizzes()
    elif page == "Flashcards":
        display_flashcards()
    elif page == "Personalized Learning Path":
        display_learning_path()
    elif page == "Chat Assistant":
        display_chat_assistant()
    elif page == "User Settings":
        display_user_settings()

# Video Processing Page
def display_video_processing():
    st.markdown("<div class='section-header'>Video Processing</div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("Input a YouTube video URL to extract transcript and analyze content.")
        
        # If we're coming from a recommendation, pre-populate the URL
        default_url = st.session_state.get('video_url', "")
        video_url = st.text_input("YouTube Video URL", value=default_url, key="video_url_input")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            process_btn = st.button("Process Video", type="primary")
        with col2:
            clear_btn = st.button("Clear", type="secondary")
        
        if process_btn and video_url:
            with st.spinner("Processing video..."):
                try:
                    video_processor = VideoProcessor()
                    video_info, transcript = video_processor.process_video(video_url)
                    
                    # Save to session state using processed_video_url, not the widget key
                    st.session_state.processed_video_url = video_url
                    st.session_state.video_info = video_info
                    st.session_state.transcript = transcript
                    
                    # Add to watched videos if not already there
                    video_entry = {
                        'url': video_url,
                        'title': video_info['title'],
                        'channel': video_info['channel'],
                        'duration': video_info['duration'],
                        'timestamp': pd.Timestamp.now().isoformat()
                    }
                    
                    # Check if this video is already in watch history
                    if not any(vid.get('url') == video_url for vid in st.session_state.watched_videos):
                        st.session_state.watched_videos.append(video_entry)
                        # Update progress slightly for each new video watched
                        st.session_state.user_progress += 2
                        if st.session_state.user_progress > 100:
                            st.session_state.user_progress = 100
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.write("✅ Video processed successfully!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display video info
                    st.subheader("Video Information")
                    st.write(f"**Title:** {video_info['title']}")
                    st.write(f"**Channel:** {video_info['channel']}")
                    st.write(f"**Duration:** {video_info['duration']} minutes")
                    
                    # Generate and display video overview
                    with st.spinner("Generating video overview..."):
                        summarizer = SummarizerAgent()
                        video_overview = summarizer.generate_overview(transcript, video_info)
                        st.session_state.video_overview = video_overview
                    
                    # Display the overview
                    st.subheader("Video Overview")
                    with st.container():
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        
                        # Create two columns for better visual layout
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            st.markdown(f"### About this Video")
                            st.write(f"{video_overview['description']}")
                        
                        with col2:
                            st.markdown("### Quick Facts")
                            st.markdown(f"**Primary Topic:** {video_overview['primary_topic']}")
                            st.markdown(f"**Target Audience:** {video_overview['target_audience']}")
                            st.markdown(f"**Content Type:** {video_overview['content_type']}")
                            
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display full transcript
                    st.subheader("Full Transcript")
                    with st.expander("Transcript Content", expanded=False):
                        st.text_area("", value=transcript, height=400, disabled=True, key="full_transcript_text")
                    
                except Exception as e:
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.error(f"Error processing video: {str(e)}")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        if clear_btn:
            # Clear stored video information
            st.session_state.processed_video_url = ""
            st.session_state.video_info = None
            st.session_state.transcript = None
            st.session_state.video_overview = None
            # Also clear the URL in session state for recommendation clicks
            st.session_state.video_url = ""
            st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

# Video Summaries Page        
def display_video_summaries():
    st.markdown("<div class='section-header'>AI-Generated Video Summaries</div>", unsafe_allow_html=True)
    
    if not st.session_state.get('transcript'):
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.info("Please process a video first to generate summaries.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Options for summary length
        summary_length = st.select_slider(
            "Summary Length",
            options=["Concise", "Moderate", "Comprehensive"],
            value="Moderate"
        )
        
        generate_btn = st.button("Generate Summary", type="primary")
        
        if generate_btn:
            with st.spinner("Generating summary..."):
                try:
                    summarizer = SummarizerAgent()
                    summary = summarizer.generate_summary(
                        st.session_state.transcript,
                        st.session_state.video_info,
                        summary_length
                    )
                    
                    # Save to session state
                    st.session_state.summary = summary
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success("Summary generated successfully!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.error(f"Error generating summary: {str(e)}")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # Display summary if available
        if st.session_state.get('summary'):
            st.subheader("Video Summary")
            
            if 'key_points' in st.session_state.summary:
                st.write("**Key Points:**")
                for point in st.session_state.summary['key_points']:
                    st.write(f"• {point}")
            
            if 'summary_text' in st.session_state.summary:
                st.write("**Summary:**")
                st.write(st.session_state.summary['summary_text'])
                
            if 'topics' in st.session_state.summary:
                st.write("**Main Topics:**")
                for topic in st.session_state.summary['topics']:
                    st.write(f"• {topic}")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Interactive Quizzes Page
def display_quizzes():
    st.markdown("<div class='section-header'>Interactive Quizzes</div>", unsafe_allow_html=True)
    
    if not st.session_state.get('transcript'):
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.info("Please process a video first to generate quizzes.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Quiz generation options
        col1, col2 = st.columns(2)
        with col1:
            num_questions = st.slider("Number of Questions", min_value=3, max_value=10, value=5)
        with col2:
            difficulty = st.select_slider(
                "Difficulty Level",
                options=["Easy", "Medium", "Hard"],
                value="Medium"
            )
        
        generate_btn = st.button("Generate Quiz", type="primary")
        
        if generate_btn:
            with st.spinner("Generating quiz questions..."):
                try:
                    quiz_agent = QuizAgent()
                    questions = quiz_agent.generate_quiz(
                        st.session_state.transcript,
                        st.session_state.video_info,
                        num_questions,
                        difficulty
                    )
                    
                    # Save to session state
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_feedback = {}
                    st.session_state.quiz_submitted = False
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success(f"Generated {len(questions)} quiz questions!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.error(f"Error generating quiz: {str(e)}")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display quiz if available
        if st.session_state.get('quiz_questions'):
            st.subheader("Quiz")
            
            with st.form(key="quiz_form"):
                for i, q in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Question {i+1}:** {q['question']}")
                    options = q['options']
                    
                    # Use radio buttons for multiple choice
                    answer = st.radio(
                        f"Select your answer for question {i+1}:",
                        options,
                        key=f"q_{i}"
                    )
                    
                    # Store answer in session state
                    st.session_state.quiz_answers[i] = answer
                    
                    st.markdown("---")
                
                submit_quiz = st.form_submit_button("Submit Quiz")
                
                if submit_quiz:
                    st.session_state.quiz_submitted = True
            
            # Show results after submission
            if st.session_state.quiz_submitted:
                correct_count = 0
                
                st.subheader("Quiz Results")
                for i, q in enumerate(st.session_state.quiz_questions):
                    user_answer = st.session_state.quiz_answers.get(i)
                    correct_answer = q['correct_answer']
                    
                    if user_answer == correct_answer:
                        result_icon = "✅"
                        result_color = "green"
                        correct_count += 1
                        feedback = q.get('correct_feedback', "Great job! That's correct.")
                    else:
                        result_icon = "❌"
                        result_color = "red"
                        feedback = q.get('incorrect_feedback', f"The correct answer is: {correct_answer}")
                    
                    st.markdown(f"**Question {i+1}:** {q['question']}")
                    st.markdown(f"Your answer: <span style='color:{result_color}'>{user_answer} {result_icon}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Feedback:** {feedback}")
                    st.markdown("---")
                
                # Display final score
                score_percentage = (correct_count / len(st.session_state.quiz_questions)) * 100
                st.markdown(f"### Your Score: <span style='color:{'green' if score_percentage >= 70 else 'orange'}'>{score_percentage:.1f}%</span>", unsafe_allow_html=True)
                
                # Update user progress in session state
                if 'user_progress' not in st.session_state:
                    st.session_state.user_progress = 0
                
                # Increment progress based on quiz performance
                progress_increment = int(score_percentage / 10)
                st.session_state.user_progress = min(100, st.session_state.user_progress + progress_increment)
                
                # Button to clear quiz results
                if st.button("Take Another Quiz"):
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_feedback = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()

# Flashcards Page
def display_flashcards():
    st.markdown("<div class='section-header'>Flashcards</div>", unsafe_allow_html=True)
    
    if not st.session_state.get('transcript'):
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.info("Please process a video first to generate flashcards.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Flashcard generation options
        col1, col2 = st.columns(2)
        with col1:
            num_cards = st.slider("Number of Flashcards", min_value=5, max_value=20, value=10)
        with col2:
            focus_area = st.selectbox(
                "Focus Area",
                ["Key Concepts", "Definitions", "Examples", "Mixed"],
                index=3
            )
        
        generate_btn = st.button("Generate Flashcards", type="primary")
        
        if generate_btn:
            with st.spinner("Generating flashcards..."):
                try:
                    flashcard_agent = FlashcardAgent()
                    flashcards = flashcard_agent.generate_flashcards(
                        st.session_state.transcript,
                        st.session_state.video_info,
                        num_cards,
                        focus_area
                    )
                    
                    # Save to session state
                    st.session_state.flashcards = flashcards
                    st.session_state.current_flashcard = 0
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success(f"Generated {len(flashcards)} flashcards!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.error(f"Error generating flashcards: {str(e)}")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display flashcards if available
        if st.session_state.get('flashcards'):
            st.subheader("Study with Flashcards")
            
            flashcards = st.session_state.flashcards
            current_idx = st.session_state.current_flashcard
            
            # Flashcard navigation
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button("⬅️ Previous") and current_idx > 0:
                    st.session_state.current_flashcard -= 1
                    st.rerun()
            
            with col3:
                if st.button("Next ➡️") and current_idx < len(flashcards) - 1:
                    st.session_state.current_flashcard += 1
                    st.rerun()
            
            # Display current flashcard
            with col2:
                card_front = flashcards[current_idx]['front']
                card_back = flashcards[current_idx]['back']
                
                # Flashcard container with flip effect
                if 'show_answer' not in st.session_state:
                    st.session_state.show_answer = False
                    
                card_container = st.container()
                with card_container:
                    st.markdown(
                        f"""
                        <div style='
                            background-color: white;
                            padding: 2rem;
                            border-radius: 1rem;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            height: 200px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            font-size: 1.2rem;
                        '>
                            {card_back if st.session_state.show_answer else card_front}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                flip_btn = st.button("Flip Card")
                if flip_btn:
                    st.session_state.show_answer = not st.session_state.show_answer
                    st.rerun()
            
            # Progress indicator
            st.progress((current_idx + 1) / len(flashcards))
            st.write(f"Card {current_idx + 1} of {len(flashcards)}")

# Add helper functions before display_learning_path function
def extract_youtube_id(youtube_url):
    """Extract the YouTube video ID from a URL"""
    import re
    # Regular expressions to extract YouTube video ID from different URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    return None

def display_recommended_videos(videos, category_prefix=""):
    """Helper function to display recommended videos with watch status and embedded player"""
    for i, video in enumerate(videos):
        # Check if this video has been watched
        video_url = video.get('url', '')
        video_id = extract_youtube_id(video_url)
        already_watched = any(v.get('url') == video_url for v in st.session_state.watched_videos)
        
        # Create a unique key for each video component
        unique_id = video.get('id', f'vid{i}')
        button_key = f"watch_{category_prefix}_{unique_id}_{i}"
        embed_key = f"embed_{category_prefix}_{unique_id}_{i}"
        
        # Video card with information and embedded player option
        with st.expander(f"**{video['title']}**" + (" ✓" if already_watched else ""), expanded=False):
            # Video metadata
            st.write(f"**Channel:** {video['channel']}")
            st.write(f"**Why recommended:** {video.get('reason', 'Recommended based on your interests')}")
            if 'difficulty' in video:
                st.write(f"**Difficulty:** {video['difficulty']}")
            if 'duration_minutes' in video:
                st.write(f"**Duration:** {video['duration_minutes']} minutes")
            
            # Status message if already watched
            if already_watched:
                st.info("You've already watched this video")
            
            # Video player controls
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Watch in Player", key=button_key):
                    # Toggle display of video player
                    current_state = st.session_state.get(f"show_video_{embed_key}", False)
                    st.session_state[f"show_video_{embed_key}"] = not current_state
                    
                    # If we're showing the video and it hasn't been watched, add to watched history
                    if not already_watched and not current_state:
                        # Create a video entry to add to watch history
                        video_entry = {
                            'url': video_url,
                            'title': video['title'],
                            'channel': video['channel'],
                            'duration': video.get('duration_minutes', 0),
                            'timestamp': pd.Timestamp.now().isoformat()
                        }
                        st.session_state.watched_videos.append(video_entry)
                        # Update progress for new video watched
                        st.session_state.user_progress += 2
                        if st.session_state.user_progress > 100:
                            st.session_state.user_progress = 100
                        st.rerun()
                
            with col2:
                if st.button("Process Video", key=f"process_{button_key}"):
                    # Redirect to video processing page with this URL
                    st.session_state.video_url = video_url 
                    st.session_state.next_page = "Video Processing"
                    st.rerun()
            
            with col3:
                # Open in YouTube button
                youtube_link = f"https://www.youtube.com/watch?v={video_id}" if video_id else video_url
                st.markdown(f"[Open in YouTube]({youtube_link})", unsafe_allow_html=True)
            
            # Display embedded YouTube player if requested
            if st.session_state.get(f"show_video_{embed_key}", False) and video_id:
                st.components.v1.iframe(
                    src=f"https://www.youtube.com/embed/{video_id}",
                    width=600,
                    height=400,
                    scrolling=True
                )

def display_learning_path():
    st.markdown("<div class='section-header'>Personalized Learning Path</div>", unsafe_allow_html=True)
    
    # Check for user email as the primary identifier
    if not st.session_state.get('user_email'):
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.info("Please set up your email in User Settings to get personalized recommendations.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("Go to User Settings"):
            # Use next_page instead of directly modifying navigation
            st.session_state.next_page = "User Settings"
            # Set a flag to indicate we came from the learning path
            st.session_state.from_learning_path = True
            st.rerun()
        return
        
    # Load user settings to ensure all preferences are available
    if st.session_state.get('user_email'):
        user_settings = UserSettings()
        user_settings.load_settings_by_email(st.session_state.get('user_email'))
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # Initial assessment if needed
        if 'learning_interests' not in st.session_state or 'learning_goals' not in st.session_state or 'preferred_learning_style' not in st.session_state:
            st.subheader("Learning Preferences")
            
            # Get default values from session state if they exist
            default_interests = st.session_state.get('learning_interests', [])
            
            learning_interests = st.multiselect(
                "What topics are you interested in?",
                [
                    "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology",
                    "History", "Literature", "Philosophy", "Economics", "Business",
                    "Art", "Music", "Language Learning", "Personal Development", "Other"
                ],
                default=default_interests,
                key="interests"
            )
            
            learning_goals = st.text_area(
                "What are your learning goals? What do you want to achieve?",
                value=st.session_state.get('learning_goals', ''),
                key="goals"
            )
            
            learning_style = st.select_slider(
                "How do you prefer to learn?",
                options=["Visual", "Auditory", "Reading/Writing", "Kinesthetic"],
                value=st.session_state.get('preferred_learning_style', "Visual"),
                key="learning_style"
            )
            
            skill_level = st.select_slider(
                "What is your current skill level in these topics?",
                options=["Beginner", "Intermediate", "Advanced"],
                value=st.session_state.get('skill_level', "Beginner"),
                key="skill_level_input"
            )
            
            if st.button("Save Preferences"):
                st.session_state.learning_interests = learning_interests
                st.session_state.learning_goals = learning_goals
                st.session_state.preferred_learning_style = learning_style
                st.session_state.skill_level = skill_level
                
                # Generate personalized path
                learning_path_agent = LearningPathAgent()
                recommendations = learning_path_agent.generate_recommendations(
                    interests=learning_interests,
                    goals=learning_goals,
                    learning_style=st.session_state.preferred_learning_style,
                    user_progress=st.session_state.get('user_progress', 0),
                    video_history=st.session_state.get('video_history', []),
                    skill_level=st.session_state.skill_level,
                    completed_milestones=st.session_state.get('completed_milestones', [])
                )
                
                st.session_state.learning_recommendations = recommendations
                
                # Save learning preferences to user settings file
                if st.session_state.get('user_email'):
                    # Save preferences to user's settings file
                    user_settings = UserSettings()
                    user_settings.save_learning_preferences(st.session_state.user_email)
                    
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success("Learning preferences saved!")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.warning("Your learning preferences are not being saved between sessions. Set up your email in User Settings.")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.rerun()
        else:
            # Display existing preferences
            st.subheader("Your Learning Profile")
            st.write(f"**Interests:** {', '.join(st.session_state.get('learning_interests', []))}")
            st.write(f"**Learning Goals:** {st.session_state.get('learning_goals', '')}")
            st.write(f"**Preferred Learning Style:** {st.session_state.get('preferred_learning_style', 'Visual')}")
            st.write(f"**Current Skill Level:** {st.session_state.get('skill_level', 'Beginner')}")
            
            if st.button("Update Preferences", key="update_preferences_btn"):
                # Set a flag in session state to show the preferences form
                st.session_state.show_preferences_form = True
                st.rerun()
                
            # If the update button was clicked, show the preferences form
            if st.session_state.get('show_preferences_form', False):
                st.subheader("Update Learning Preferences")
                
                # Get current values to use as defaults
                current_interests = st.session_state.get('learning_interests', [])
                current_goals = st.session_state.get('learning_goals', '')
                current_style = st.session_state.get('preferred_learning_style', 'Visual')
                current_skill = st.session_state.get('skill_level', 'Beginner')
                
                # Create a form for the update preferences
                with st.form(key="update_preferences_form"):
                    # Show form with current values pre-selected
                    learning_interests = st.multiselect(
                        "What topics are you interested in?",
                        [
                            "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology",
                            "History", "Literature", "Philosophy", "Economics", "Business",
                            "Art", "Music", "Language Learning", "Personal Development", "Other"
                        ],
                        default=current_interests,
                        key="update_interests"
                    )
                    
                    learning_goals = st.text_area(
                        "What are your learning goals? What do you want to achieve?",
                        value=current_goals,
                        key="update_goals"
                    )
                    
                    learning_style = st.select_slider(
                        "How do you prefer to learn?",
                        options=["Visual", "Auditory", "Reading/Writing", "Kinesthetic"],
                        value=current_style,
                        key="update_learning_style"
                    )
                    
                    skill_level = st.select_slider(
                        "What is your current skill level in these topics?",
                        options=["Beginner", "Intermediate", "Advanced"],
                        value=current_skill,
                        key="update_skill_level"
                    )
                    
                    # Include both submit and cancel buttons in the form
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        submit_button = st.form_submit_button("Save Updated Preferences", type="primary")
                    with col2:
                        cancel_button = st.form_submit_button("Cancel", type="secondary")
                
                # Handle form submission outside the form
                if submit_button:
                    # Update session state with new values
                    st.session_state.learning_interests = learning_interests
                    st.session_state.learning_goals = learning_goals
                    st.session_state.preferred_learning_style = learning_style
                    st.session_state.skill_level = skill_level
                    
                    # Generate new personalized path
                    learning_path_agent = LearningPathAgent()
                    recommendations = learning_path_agent.generate_recommendations(
                        interests=learning_interests,
                        goals=learning_goals,
                        learning_style=learning_style,
                        user_progress=st.session_state.get('user_progress', 0),
                        video_history=st.session_state.get('video_history', []),
                        skill_level=skill_level,
                        completed_milestones=st.session_state.get('completed_milestones', [])
                    )
                    
                    st.session_state.learning_recommendations = recommendations
                    
                    # Save to user settings file
                    if st.session_state.get('user_email'):
                        user_settings = UserSettings()
                        user_settings.save_learning_preferences(st.session_state.user_email)
                    
                    # Clear the form flag
                    st.session_state.show_preferences_form = False
                    st.success("Learning preferences updated successfully!")
                    time.sleep(1)  # Short pause to show the success message
                    st.rerun()
                
                if cancel_button:
                    # Clear the form flag without saving
                    st.session_state.show_preferences_form = False
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display personalized recommendations
    if 'learning_recommendations' in st.session_state:
        recommendations = st.session_state.get('learning_recommendations', {})
        
        # Check if recommendations is empty or has content
        has_recommendations = bool(recommendations and isinstance(recommendations, dict) and 
                                  (recommendations.get('next_steps') or 
                                   recommendations.get('recommended_videos')))
                                   
        if has_recommendations:
            st.subheader("Your Personalized Learning Recommendations")
            
            # Visual progress tracker
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### Overall Learning Progress: {st.session_state.get('user_progress', 0)}%")
                st.progress(st.session_state.get('user_progress', 0) / 100.0)
            with col2:
                skill_level = st.session_state.get('skill_level', "Beginner")
                if skill_level == "Beginner":
                    emoji = "🌱"
                elif skill_level == "Intermediate":
                    emoji = "🚀"
                else:
                    emoji = "🏆"
                st.markdown(f"### Skill Level: {emoji}")
                st.markdown(f"**{skill_level}**")
        
        recommendations = st.session_state.learning_recommendations
        
        # Statistics on learning activity
        videos_watched = len(st.session_state.get('watched_videos', []))
        milestones_completed = len(st.session_state.get('completed_milestones', []))
        
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.markdown(f"""
        **Learning Activity:**
        - Videos watched: {videos_watched}
        - Milestones completed: {milestones_completed}
        - Topics explored: {len(st.session_state.learning_interests) if st.session_state.learning_interests else 0}
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Next steps
        if 'next_steps' in recommendations:
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.write("**Recommended Next Steps:**")
            for i, step in enumerate(recommendations['next_steps']):
                st.write(f"{i+1}. {step}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Recommended videos
        if 'recommended_videos' in recommendations:
            st.write("**Recommended Videos:**")
            
            # Create tabs for different categories or difficulty levels
            video_categories = set(video['category'] for video in recommendations['recommended_videos'] if 'category' in video)
            if len(video_categories) > 1:
                # If multiple categories exist, create tabs
                tabs = st.tabs(["All"] + list(video_categories))
                
                # All videos tab
                with tabs[0]:
                    display_recommended_videos(recommendations['recommended_videos'], category_prefix="all")
                    
                # Category-specific tabs
                for i, category in enumerate(video_categories):
                    with tabs[i+1]:
                        category_videos = [v for v in recommendations['recommended_videos'] if v.get('category') == category]
                        # Use the category name (with no spaces) as a prefix for unique keys
                        category_prefix = category.replace(" ", "_").lower() 
                        display_recommended_videos(category_videos, category_prefix=category_prefix)
            else:
                # If only one category or no categories, display all videos
                display_recommended_videos(recommendations['recommended_videos'], category_prefix="single")
        
        # Additional resources
        if 'additional_resources' in recommendations:
            st.write("**Additional Learning Resources:**")
            for resource in recommendations['additional_resources']:
                with st.expander(f"{resource['title']} ({resource['type']})"):
                    st.write(f"**Description:** {resource['description']}")
                    st.write(f"**Why recommended:** {resource['reason']}")
                    if 'url' in resource and resource['url']:
                        st.markdown(f"[Access Resource]({resource['url']})")
        
        # Learning milestones
        if 'milestones' in recommendations:
            st.write("**Learning Milestones:**")
            milestones = recommendations['milestones']
            
            # Create a progress chart
            milestone_names = [m['name'] for m in milestones]
            milestone_progress = [m['progress'] for m in milestones]
            
            progress_df = pd.DataFrame({
                'Milestone': milestone_names,
                'Progress (%)': milestone_progress
            })
            
            st.bar_chart(progress_df.set_index('Milestone'))
            
            # Show milestone details with completion tracking
            for milestone in milestones:
                milestone_id = milestone.get('id', '')
                milestone_completed = milestone_id in st.session_state.completed_milestones
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{milestone['name']}**")
                    st.write(f"Objective: {milestone.get('objective', 'No objective specified')}")
                    st.write(f"Estimated time: {milestone.get('estimated_completion_hours', 0)} hours")
                    st.progress(milestone['progress'] / 100.0)
                with col2:
                    if milestone_completed:
                        st.success("Completed!")
                    else:
                        # Use index in the list as part of the key to ensure uniqueness
                        milestone_index = milestones.index(milestone)
                        if st.button("Mark Complete", key=f"complete_{milestone_id}_{milestone_index}"):
                            if milestone_id not in st.session_state.completed_milestones:
                                # Update milestone completion status
                                st.session_state.completed_milestones.append(milestone_id)
                                # Update user progress
                                st.session_state.user_progress += 5  # Increment progress by 5%
                                if st.session_state.user_progress > 100:
                                    st.session_state.user_progress = 100
                                
                                # Save updated learning preferences to user settings file
                                if st.session_state.get('user_email'):
                                    user_settings = UserSettings()
                                    user_settings.save_learning_preferences(st.session_state.user_email)
                                    print(f"Saved updated milestone completion for {st.session_state.user_email}")
                                
                                st.rerun()
                                
        # Skill assessments
        if 'skill_assessments' in recommendations:
            st.write("**Skill Assessments:**")
            for assessment in recommendations['skill_assessments']:
                st.markdown(f"""
                **{assessment['skill']}**  
                Current level: {assessment['current_level']}  
                Goal: {assessment['next_goal']}  
                Recommended practice: {assessment['recommended_practice']}
                """)
                st.progress(
                    0.25 if assessment['current_level'] == "Beginner" else 
                    0.5 if assessment['current_level'] == "Intermediate" else 
                    0.75 if assessment['current_level'] == "Advanced" else 0.1
                )

# Chat Assistant Page
def display_chat_assistant():
    st.markdown("<div class='section-header'>Chat Assistant</div>", unsafe_allow_html=True)
    
    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hello! I'm your learning assistant. How can I help you with your video learning today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask a question about the video content...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_agent = ChatAssistantAgent()
                
                # Context for the agent
                context = {
                    "transcript": st.session_state.get("transcript", ""),
                    "video_info": st.session_state.get("video_info", {}) or {},  # Ensure not None
                    "summary": st.session_state.get("summary", {}) or {},  # Ensure not None
                    "chat_history": st.session_state.chat_messages[:-1]  # Exclude the latest user message
                }
                
                response = chat_agent.generate_response(user_input, context)
                
                st.write(response)
                
                # Add assistant response to chat history
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

# User Settings Page
def display_user_settings():
    st.markdown("<div class='section-header'>User Settings</div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        # User profile settings
        st.subheader("User Profile")
        
        # Check if IAP authentication is available
        from utils.session_state import get_iap_email
        iap_email = get_iap_email()
        
        # Display IAP authentication status
        if iap_email:
            st.success(f"✓ Authenticated with Google App Engine as: {iap_email}")
            
            # Offer to use IAP email if different from current email
            current_email = st.session_state.get('user_email', '')
            if current_email and current_email != iap_email:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"Your current settings are using: {current_email}")
                with col2:
                    if st.button("Switch to IAP Email", type="primary"):
                        st.session_state.user_email = iap_email
                        
                        # Load any existing settings for this IAP email
                        user_settings = UserSettings()
                        settings = user_settings.load_settings_by_email(iap_email)
                        for key, value in settings.items():
                            if key != 'user_email':  # We already set the email
                                st.session_state[key] = value
                        
                        st.rerun()
            elif current_email == iap_email:
                st.info("✓ Your settings are currently using your Google authenticated email")
            else:
                # No email set yet, prompt to use IAP email
                if st.button("Use Google Authentication Email", type="primary"):
                    st.session_state.user_email = iap_email
                    
                    # Load any existing settings for this IAP email
                    user_settings = UserSettings()
                    settings = user_settings.load_settings_by_email(iap_email)
                    for key, value in settings.items():
                        if key != 'user_email':  # We already set the email
                            st.session_state[key] = value
                    
                    st.rerun()
        
        # Check if current email is from IAP
        current_email = st.session_state.get('user_email', '')
        email_from_iap = (iap_email and current_email == iap_email)
        
        # If email is from IAP, display it as readonly
        if email_from_iap:
            st.markdown(
                f"""
                <div style='margin-bottom: 10px;'>
                    <label style='font-size: 14px; font-weight: 500;'>Email Address</label>
                    <div style='padding: 8px; background-color: #f0f2f6; border-radius: 4px; color: #666666;'>
                        {current_email} <span style='background-color: #e6f7ff; color: #0078d4; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-left: 10px;'>IAP Authenticated</span>
                    </div>
                    <div style='font-size: 12px; color: #666666; margin-top: 4px;'>Email address is locked because you're authenticated with Google IAP</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Still need to store the email in session state
            user_email = current_email
        else:
            # Regular text input for manual email entry
            user_email = st.text_input(
                "Email Address (required)",
                value=current_email,
                key="settings_email",
                help="Your email address is used to identify you and save your settings across sessions"
            )
        
        user_name = st.text_input(
            "Display Name (optional)",
            value=st.session_state.get('user_name', ''),
            key="settings_name",
            help="Name to display in the interface (if not provided, your email will be used)"
        )
        
        # Accessibility settings
        st.subheader("Accessibility Settings")
        
        font_size = st.select_slider(
            "Font Size",
            options=["Small", "Medium", "Large"],
            value=st.session_state.get('font_size', 'Medium'),
            key="settings_font_size"
        )
        
        color_scheme = st.selectbox(
            "Color Scheme",
            ["Default", "High Contrast", "Dark Mode"],
            index=0 if 'color_scheme' not in st.session_state else 
                  ["Default", "High Contrast", "Dark Mode"].index(st.session_state.color_scheme),
            key="settings_color_scheme"
        )
        
        # Video playback settings
        st.subheader("Video Playback Settings")
        
        default_speed = st.slider(
            "Default Playback Speed",
            min_value=0.5,
            max_value=2.0,
            value=st.session_state.get('default_speed', 1.0),
            step=0.25,
            key="settings_playback_speed"
        )
        
        auto_captions = st.checkbox(
            "Auto-enable Captions",
            value=st.session_state.get('auto_captions', True),
            key="settings_auto_captions"
        )
        
        # Save settings
        if st.button("Save Settings", type="primary"):
            user_settings = UserSettings()
            
            # If user is authenticated via IAP, ensure we use that email
            if email_from_iap:
                # Force the email to be the IAP email
                user_email = iap_email
                
            settings_dict = {
                'user_email': user_email,  # Primary identifier first
                'user_name': user_name,
                'font_size': font_size,
                'color_scheme': color_scheme,
                'default_speed': default_speed,
                'auto_captions': auto_captions,
                'is_iap_authenticated': email_from_iap  # Track IAP authentication
            }
            
            if user_email:
                # Check if this is an IAP email
                from utils.session_state import get_iap_email
                iap_email = get_iap_email()
                
                # Add a note if using IAP authentication
                if iap_email and iap_email == user_email:
                    st.info("You're saving settings with your authenticated Google email. This email cannot be changed.")
                
                # If we have an email, attempt to load existing settings first
                existing_settings = user_settings.load_settings_by_email(user_email)
                
                # Merge with new settings, prioritizing the new ones
                for key, value in existing_settings.items():
                    if key not in settings_dict:
                        settings_dict[key] = value
                
                success = user_settings.save_settings(settings_dict)
                
                if success:
                    st.markdown("<div class='success-box'>", unsafe_allow_html=True)
                    st.success("Settings saved successfully for email: " + user_email)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # If we came from learning path, redirect back
                    if st.session_state.get('from_learning_path'):
                        st.session_state.next_page = "Personalized Learning Path"
                        st.session_state.pop('from_learning_path', None)  # Clear the flag
                        st.rerun()
                else:
                    st.error("Failed to save settings. Please try again.")
            else:
                # No email provided - check if IAP email is available
                from utils.session_state import get_iap_email
                iap_email = get_iap_email()
                
                if iap_email:
                    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                    st.info(f"You're authenticated as {iap_email}. Click 'Use Google Authentication Email' to use this email.")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # No email provided or available
                    st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                    st.warning("Email is required for settings persistence. Please add your email.")
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Update session state
            for key, value in settings_dict.items():
                st.session_state[key] = value
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Learning History Section
        st.subheader("Learning History")
        
        if st.session_state.watched_videos:
            st.write(f"You have watched {len(st.session_state.watched_videos)} videos:")
            
            with st.expander("View Watch History", expanded=True):
                for i, video in enumerate(sorted(st.session_state.watched_videos, 
                                        key=lambda x: x.get('timestamp', ''), reverse=True)):
                    # Extract video information
                    video_url = video.get('url', '')
                    video_id = extract_youtube_id(video_url)
                    video_title = video.get('title', 'Unknown Title')
                    
                    # Create unique keys for this history item
                    safe_title = video_title.replace(" ", "_")[:10]
                    embed_key = f"hist_embed_{safe_title}_{i}"
                    
                    # Display video metadata
                    st.markdown(f"""
                    **{i+1}. {video_title}**  
                    Channel: {video.get('channel', 'Unknown')}  
                    Duration: {video.get('duration', 0)} minutes  
                    Watched on: {pd.to_datetime(video.get('timestamp', '')).strftime('%Y-%m-%d %H:%M') if video.get('timestamp') else 'Unknown'}
                    """)
                    
                    # Video controls
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Watch Again", key=f"rewatch_hist_{safe_title}_{i}"):
                            # Toggle the embedded player
                            current_state = st.session_state.get(f"show_video_{embed_key}", False)
                            st.session_state[f"show_video_{embed_key}"] = not current_state
                            st.rerun()
                    
                    with col2:
                        if st.button("Process Video", key=f"process_hist_{safe_title}_{i}"):
                            st.session_state.video_url = video_url
                            st.session_state.next_page = "Video Processing"
                            st.rerun()
                    
                    # Display embedded player if requested
                    if st.session_state.get(f"show_video_{embed_key}", False) and video_id:
                        st.components.v1.iframe(
                            src=f"https://www.youtube.com/embed/{video_id}",
                            width=600,
                            height=400,
                            scrolling=True
                        )
                        
                    st.markdown("---")
        else:
            st.info("You haven't watched any videos yet. Process a video to start building your learning history.")
        
        # Completed Milestones
        if st.session_state.completed_milestones:
            st.write(f"You have completed {len(st.session_state.completed_milestones)} learning milestones!")
            if st.button("View Details in Learning Path"):
                st.session_state.next_page = "Personalized Learning Path"
                st.rerun()
        
        # Reset data option
        st.subheader("Reset User Data")
        
        # Add key for reset confirmation to session state if it doesn't exist
        if 'reset_confirmed' not in st.session_state:
            st.session_state.reset_confirmed = False
        
        # Show warning and info messages
        st.warning("⚠️ This will permanently delete all your settings and learning progress")
        st.info("Your data will be completely removed, and you'll start fresh the next time you log in.")
        
        # Put checkbox outside the form so it can update the session state
        reset_confirm = st.checkbox(
            "I understand this will delete all my learning progress and preferences",
            key="reset_confirm_checkbox"
        )
        
        # Update session state based on checkbox value
        st.session_state.reset_confirmed = reset_confirm
        
        # Now create the form with the submit button
        with st.form(key="reset_user_data_form"):
            # Button will use the current value of reset_confirm from session state
            submit_button = st.form_submit_button("Reset All User Data", type="secondary", disabled=not st.session_state.reset_confirmed)
            
            if submit_button and st.session_state.reset_confirmed:
                if st.session_state.get('user_email'):
                    # Get the email from session state
                    user_email = st.session_state.user_email
                    
                    # Use our simplified reset function for maximum reliability
                    try:
                        # Import the simple reset function
                        from simple_reset import reset_user
                        
                        # Show a progress message
                        with st.spinner("Deleting user data..."):
                            # Call the simple reset function
                            deletion_success = reset_user(user_email)
                    except Exception as e:
                        print(f"Error using simple_reset: {str(e)}")
                        deletion_success = False
                    
                    # Clear all user-related session state
                    keys_to_clear = [
                        'user_name', 'user_email', 'user_progress', 'learning_interests',
                        'learning_goals', 'preferred_learning_style', 'learning_recommendations',
                        'watched_videos', 'chat_messages', 'quiz_history', 'skill_level',
                        'completed_milestones', 'learning_categories', 'learning_path'
                    ]
                    
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Reset confirmation state
                    st.session_state.reset_confirmed = False
                    
                    if deletion_success:
                        st.success("✅ User data has been completely reset! You'll start fresh the next time you log in.")
                        st.info("You have been logged out. Sign in again to start with default settings.")
                        time.sleep(2)  # Give user more time to see the message
                        st.rerun()  # Force a rerun to refresh the UI
                    else:
                        st.warning("⚠️ User session cleared, but there was an issue deleting the settings file.")
                        st.info("Some data may still remain. Please contact support if you continue to have issues.")
                        time.sleep(3)  # Slightly longer pause for warning
                        st.rerun()  # Force a rerun to refresh the UI
                else:
                    st.error("No user is currently logged in. Please log in to reset user data.")

if __name__ == "__main__":
    main()
