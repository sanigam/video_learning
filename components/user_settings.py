import streamlit as st
import json
import os
from pathlib import Path
import shutil

class UserSettings:
    def __init__(self, settings_file=None):
        """
        Initialize UserSettings class.
        
        Args:
            settings_file (str, optional): Path to settings file
        """
        # Create a data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        Path(self.data_dir).mkdir(exist_ok=True)
        
        if settings_file:
            self.settings_file = settings_file
        else:
            self.settings_file = os.path.join(self.data_dir, "user_settings.json")
        
        print(f"UserSettings initialized with settings_file: {self.settings_file}")
        
        self.default_settings = {
            'user_email': '',  # Primary user identifier
            'user_name': '',   # Optional display name
            'font_size': 'Medium',
            'color_scheme': 'Default',
            'default_speed': 1.0,
            'auto_captions': True,
            'is_iap_authenticated': False,  # Track if the email comes from IAP
            'learning_interests': [],
            'learning_goals': '',
            'preferred_learning_style': 'Visual',
            'learning_path': {},
            'learning_recommendations': {},  # Ensuring this is always present
            'completed_milestones': [],
            'user_progress': 0
        }
        
    def load_settings(self):
        """
        Load user settings from file or return defaults.
        
        Returns:
            dict: User settings
        """
        try:
            if Path(self.settings_file).exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            else:
                return self.default_settings
        except Exception:
            return self.default_settings
    
    def save_settings(self, settings):
        """
        Save user settings to session state and file.
        
        Args:
            settings (dict): User settings to save
        """
        try:
            # Update session state with settings
            for key, value in settings.items():
                st.session_state[key] = value
            
            # Preserve learning preferences in the settings if they exist in session state
            learning_preference_keys = [
                'learning_interests', 'learning_goals', 'preferred_learning_style', 
                'skill_level', 'learning_recommendations', 'completed_milestones', 
                'user_progress', 'learning_path'
            ]
            
            # Always include all learning preference keys that exist in session state
            for key in learning_preference_keys:
                if key in st.session_state:
                    # Handle null values - convert to appropriate empty defaults
                    if st.session_state[key] is None:
                        if key == 'learning_interests' or key == 'completed_milestones':
                            settings[key] = []
                        elif key == 'learning_goals':
                            settings[key] = ''
                        elif key in ['learning_path', 'learning_recommendations']:
                            settings[key] = {}
                        elif key == 'user_progress':
                            settings[key] = 0
                    else:
                        settings[key] = st.session_state[key]
                    print(f"Saved {key} from session state to settings")
            
            # Ensure learning_path and learning_recommendations are always synchronized
            # and both are included in the settings, never as null values
            if 'learning_recommendations' in settings:
                # Handle null values
                if settings['learning_recommendations'] is None:
                    settings['learning_recommendations'] = {}
                    
                settings['learning_path'] = settings['learning_recommendations']
                st.session_state['learning_path'] = settings['learning_recommendations']
                st.session_state['learning_recommendations'] = settings['learning_recommendations'] 
                print("Synchronized learning_path from learning_recommendations in settings")
            elif 'learning_path' in settings:
                # Handle null values
                if settings['learning_path'] is None:
                    settings['learning_path'] = {}
                    
                settings['learning_recommendations'] = settings['learning_path']
                st.session_state['learning_recommendations'] = settings['learning_path']
                st.session_state['learning_path'] = settings['learning_path']
                print("Synchronized learning_recommendations from learning_path in settings")
            else:
                # Neither exists, initialize both as empty objects
                settings['learning_path'] = {}
                settings['learning_recommendations'] = {}
                st.session_state['learning_path'] = {}
                st.session_state['learning_recommendations'] = {}
                print("Initialized both learning_path and learning_recommendations as empty objects")
            
            # If email is provided, use it to create a user-specific file
            email = settings.get('user_email', '')
            if email:
                # Create a filename based on email (sanitized to be file-system friendly)
                file_name = os.path.join(self.data_dir, f"user_settings_{email.replace('@', '_at_').replace('.', '_dot_')}.json")
                
                # Ensure the directory exists
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                
                # Save to user-specific file for persistence between sessions
                with open(file_name, 'w') as f:
                    json.dump(settings, f, indent=4)
                    
                print(f"Settings saved for user: {email} at path: {file_name}")
                
                # Make sure this becomes the active settings file for subsequent loads
                self.settings_file = file_name
                return True
            else:
                # If no email is provided, reject the save
                print("Cannot save settings: no email provided")
                return False
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def get_setting(self, key, default=None):
        """
        Get a specific setting value.
        
        Args:
            key (str): Setting key
            default (any, optional): Default value if key not found
            
        Returns:
            any: Setting value
        """
        if key in st.session_state:
            return st.session_state[key]
        
        settings = self.load_settings()
        return settings.get(key, default)
    
    def load_settings_by_email(self, email):
        """
        Load settings for a specific user by email.
        
        Args:
            email (str): User email address
            
        Returns:
            dict: User settings for the specified email
        """
        try:
            # If email is empty, return default settings
            if not email:
                return self.default_settings
            
            # Check if this user was previously reset
            was_reset = self.check_if_user_reset(email)
            
            # Check if this is an IAP authenticated email
            from utils.session_state import get_iap_email
            iap_email = get_iap_email()
            is_iap_auth = (iap_email and iap_email == email)
            
            # Generate sanitized filename
            user_settings_file = os.path.join(self.data_dir, f"user_settings_{email.replace('@', '_at_').replace('.', '_dot_')}.json")
            
            # Prepare settings based on reset status and file existence
            if was_reset or not Path(user_settings_file).exists():
                # Either user was reset or no settings file exists
                if was_reset:
                    print(f"User {email} was previously reset. Starting with fresh settings.")
                    # Clear reset marker to prevent constant reset
                    try:
                        sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
                        reset_marker = os.path.join(self.data_dir, "reset_users", f"{sanitized_email}.reset")
                        if os.path.exists(reset_marker):
                            os.remove(reset_marker)
                            print(f"Cleared reset marker for {email}")
                    except Exception as e:
                        print(f"Error clearing reset marker: {str(e)}")
                else:
                    print(f"No settings file found for {email}, using default settings")
                
                # Use default settings
                settings = self.default_settings.copy()
                settings['user_email'] = email
                if is_iap_auth:
                    settings['is_iap_authenticated'] = True
            else:
                # File exists and user wasn't reset - load from file
                print(f"Loading settings from: {user_settings_file}")
                with open(user_settings_file, 'r') as f:
                    settings = json.load(f)
                
                # If this is an IAP authenticated email, mark it in the settings
                if is_iap_auth and not settings.get('is_iap_authenticated'):
                    settings['is_iap_authenticated'] = True
                    # Update the file with this information
                    with open(user_settings_file, 'w') as f:
                        json.dump(settings, f, indent=4)
                
                # Define learning preference keys to load into session state
                learning_preference_keys = [
                    'learning_interests', 'learning_goals', 'preferred_learning_style', 
                    'skill_level', 'learning_recommendations', 'completed_milestones', 
                    'user_progress', 'learning_path'
                ]
                
                # Load all available learning preferences into session state
                for key in learning_preference_keys:
                    if key in settings:  # If the key exists in settings
                        # Handle null values appropriately
                        if settings[key] is None:
                            # Initialize with default value if null
                            if key == 'learning_interests':
                                st.session_state[key] = []
                            elif key == 'learning_goals':
                                st.session_state[key] = ''
                            elif key == 'preferred_learning_style':
                                st.session_state[key] = 'Visual'
                            elif key == 'skill_level':
                                st.session_state[key] = 'Beginner'
                            elif key in ['learning_path', 'learning_recommendations']:
                                st.session_state[key] = {}
                            elif key == 'completed_milestones':
                                st.session_state[key] = []
                            elif key == 'user_progress':
                                st.session_state[key] = 0
                            print(f"Initialized default value for {key} (was null in settings)")
                        else:
                                        # Always use the value from settings, overwriting any existing session state value
                            st.session_state[key] = settings[key]
                            
                            # For empty arrays/lists, ensure they're treated as valid values
                            if key == 'learning_interests' and isinstance(st.session_state[key], list) and not st.session_state[key]:
                                print(f"Loaded empty {key} from user settings (treated as valid)")
                            else:
                                print(f"Loaded {key} from user settings")
                    else:
                        # Key is missing in settings
                        # Only initialize if not already in session state
                        if key not in st.session_state or st.session_state.get(key) is None:
                            if key == 'learning_interests':
                                st.session_state[key] = []
                            elif key == 'learning_goals':
                                st.session_state[key] = ''
                            elif key == 'preferred_learning_style':
                                st.session_state[key] = 'Visual'
                            elif key == 'skill_level':
                                st.session_state[key] = 'Beginner'
                            elif key in ['learning_path', 'learning_recommendations']:
                                st.session_state[key] = {}
                            elif key == 'completed_milestones':
                                st.session_state[key] = []
                            elif key == 'user_progress':
                                st.session_state[key] = 0
                            print(f"Initialized default value for {key} (missing in settings)")
                
                # Ensure consistency between learning_recommendations and learning_path
                # Handle various cases including null values
                if 'learning_path' in settings and settings['learning_path'] and isinstance(settings['learning_path'], dict):
                    # Valid learning_path exists
                    st.session_state['learning_path'] = settings['learning_path']
                    st.session_state['learning_recommendations'] = settings['learning_path']
                    print("Synced learning_path and learning_recommendations from settings (using learning_path)")
                
                elif 'learning_recommendations' in settings and settings['learning_recommendations'] and isinstance(settings['learning_recommendations'], dict):
                    # Valid learning_recommendations exists
                    st.session_state['learning_path'] = settings['learning_recommendations']
                    st.session_state['learning_recommendations'] = settings['learning_recommendations']
                    print("Synced learning_path and learning_recommendations from settings (using learning_recommendations)")
                
                else:
                    # Neither exists with a valid non-empty value, initialize both
                    st.session_state['learning_path'] = {}
                    st.session_state['learning_recommendations'] = {}
                    settings['learning_path'] = {}
                    settings['learning_recommendations'] = {}
                    print("Initialized both learning_path and learning_recommendations as empty objects")
                
                # Update the settings file to be the user-specific one for future operations
                self.settings_file = user_settings_file
                
                # Load all settings into session state for immediate use
                for key, value in settings.items():
                    # Don't overwrite learning preferences that have already been set
                    learning_preference_keys = [
                        'learning_interests', 'learning_goals', 'preferred_learning_style', 
                        'skill_level', 'learning_recommendations', 'completed_milestones', 
                        'user_progress', 'learning_path'
                    ]
                    if key not in st.session_state or key not in learning_preference_keys:
                        st.session_state[key] = value
                
                return settings
            
            # If no user-specific file exists, return default settings with the email populated
            settings = self.default_settings.copy()
            settings['user_email'] = email
            
            # If this is an IAP authenticated email, mark it
            if is_iap_auth:
                settings['is_iap_authenticated'] = True
            
            return settings
        except Exception as e:
            print(f"Error loading settings for {email}: {str(e)}")
            return self.default_settings
    
    def apply_settings_to_ui(self):
        """
        Apply user settings to the UI appearance.
        """
        # Get current settings
        font_size = self.get_setting('font_size', 'Medium')
        color_scheme = self.get_setting('color_scheme', 'Default')
        
        # Font size settings
        font_size_values = {
            'Small': '0.9rem',
            'Medium': '1rem',
            'Large': '1.2rem'
        }
        
        font_size_value = font_size_values.get(font_size, '1rem')
        
        # Color scheme settings
        color_schemes = {
            'Default': {
                'bg_color': '#FFFFFF',
                'text_color': '#31333F',
                'accent_color': '#1E3A8A'
            },
            'High Contrast': {
                'bg_color': '#FFFFFF',
                'text_color': '#000000',
                'accent_color': '#0000CC'
            },
            'Dark Mode': {
                'bg_color': '#1E1E1E',
                'text_color': '#E0E0E0',
                'accent_color': '#4D8BF5'
            }
        }
        
        scheme = color_schemes.get(color_scheme, color_schemes['Default'])
        
        # Apply CSS with the settings
        css = f"""
        <style>
            .main-container {{
                font-size: {font_size_value};
                color: {scheme['text_color']};
            }}
            
            .main-header {{
                color: {scheme['accent_color']};
            }}
            
            .section-header {{
                color: {scheme['accent_color']};
            }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def save_learning_preferences(self, email):
        """
        Save current learning preferences from session state to user settings file.
        
        Args:
            email (str): User email address
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not email:
                print("Cannot save learning preferences: no email provided")
                return False
                
            # Generate sanitized filename
            user_settings_file = os.path.join(self.data_dir, f"user_settings_{email.replace('@', '_at_').replace('.', '_dot_')}.json")
            print(f"Looking for user settings file at: {user_settings_file}")
            
            # Load existing settings or create new ones
            if Path(user_settings_file).exists():
                with open(user_settings_file, 'r') as f:
                    settings = json.load(f)
                print(f"Loaded existing settings for {email}")
            else:
                settings = self.default_settings.copy()
                settings['user_email'] = email
                print(f"Created new settings for {email}")
            
            # Update settings with current learning preferences from session state
            learning_preference_keys = [
                'learning_interests', 'learning_goals', 'preferred_learning_style', 
                'skill_level', 'learning_recommendations', 'completed_milestones', 
                'user_progress', 'learning_path'
            ]
            
            # First ensure that all learning preference keys exist in session state
            # by transferring existing values from settings if they don't exist in session state
            for key in learning_preference_keys:
                if key in settings and settings[key] and key not in st.session_state:
                    st.session_state[key] = settings[key]
                    print(f"Restored {key} from settings to session state")
            
            # Now update settings with the current session state values
            for key in learning_preference_keys:
                if key in st.session_state:
                    # Check if the value has changed before updating
                    has_changed = False
                    if key not in settings:
                        has_changed = True
                    elif st.session_state[key] != settings.get(key):
                        has_changed = True
                        
                    # Ensure we don't save null values but convert them to empty defaults
                    if st.session_state[key] is None:
                        if key == 'learning_interests' or key == 'completed_milestones':
                            settings[key] = []
                        elif key == 'learning_goals':
                            settings[key] = ''
                        elif key in ['learning_path', 'learning_recommendations']:
                            settings[key] = {}
                        elif key == 'user_progress':
                            settings[key] = 0
                        if has_changed:
                            print(f"Updated {key} in settings from session state (null converted to default)")
                    else:
                        settings[key] = st.session_state[key]
                        if has_changed:
                            print(f"Updated {key} in settings from session state")
            
            # Ensure both learning_path and learning_recommendations are saved for consistency
            # and make sure they are never null/None but at least empty objects
            if 'learning_recommendations' in st.session_state:
                if st.session_state['learning_recommendations'] is None:
                    st.session_state['learning_recommendations'] = {}
                settings['learning_recommendations'] = st.session_state['learning_recommendations']
                settings['learning_path'] = st.session_state['learning_recommendations']
                st.session_state['learning_path'] = st.session_state['learning_recommendations']
                print("Synchronized learning_path from learning_recommendations")
            elif 'learning_path' in st.session_state:
                if st.session_state['learning_path'] is None:
                    st.session_state['learning_path'] = {}
                settings['learning_path'] = st.session_state['learning_path']
                settings['learning_recommendations'] = st.session_state['learning_path']
                st.session_state['learning_recommendations'] = st.session_state['learning_path']
                print("Synchronized learning_recommendations from learning_path")
            
            # Ensure the user_email is correctly set
            settings['user_email'] = email
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(user_settings_file), exist_ok=True)
            
            # Save to user-specific file
            with open(user_settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            # Update the settings file reference for future operations
            self.settings_file = user_settings_file
                
            print(f"Learning preferences saved for user: {email} at path: {user_settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving learning preferences: {str(e)}")
            return False
    
    def delete_user_settings(self, email):
        """
        Delete all settings for a specific user by email.
        
        Args:
            email (str): User email address
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not email:
            print("Cannot delete settings: no email provided")
            return False
            
        try:
            # Generate sanitized filename
            sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
            user_settings_file = os.path.join(self.data_dir, f"user_settings_{sanitized_email}.json")
            
            print(f"Attempting to delete user settings at: {user_settings_file}")
            
            if not Path(user_settings_file).exists():
                print(f"No settings file found for {email}")
                return True  # Consider it a success if the file doesn't exist
                
            # Create backup before deletion
            backup_file = f"{user_settings_file}.bak"
            shutil.copy2(user_settings_file, backup_file)
            print(f"Created backup at: {backup_file}")
            
            # Delete the file
            os.remove(user_settings_file)
            deleted = not os.path.exists(user_settings_file)
            
            if deleted:
                # Use the ResetManager to record the reset
                try:
                    from utils.reset_manager import ResetManager
                    reset_manager = ResetManager()
                    reset_manager.record_reset(email)
                    print(f"Recorded reset for user: {email}")
                except Exception as e:
                    # Fallback to direct file creation if ResetManager fails
                    reset_marker_dir = os.path.join(self.data_dir, "reset_users")
                    os.makedirs(reset_marker_dir, exist_ok=True)
                    reset_marker = os.path.join(reset_marker_dir, f"{sanitized_email}.reset")
                    with open(reset_marker, 'w') as f:
                        f.write(f"User {email} was reset")
                    print(f"Created reset marker at {reset_marker}")
                
                print(f"Successfully deleted settings for user: {email}")
                return True
            else:
                print(f"Failed to delete settings for user: {email}")
                return False
                
        except Exception as e:
            print(f"Error deleting settings for {email}: {str(e)}")
            return False
    
    def check_if_user_reset(self, email):
        """
        Check if a user has been reset previously
        
        Args:
            email (str): User email to check
            
        Returns:
            bool: True if user was reset, False otherwise
        """
        if not email:
            return False
            
        try:
            from utils.reset_manager import ResetManager
            reset_manager = ResetManager()
            return reset_manager.check_if_reset(email)
        except Exception as e:
            # Fallback to direct file check if ResetManager is not available
            sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
            reset_marker = os.path.join(self.data_dir, "reset_users", f"{sanitized_email}.reset")
            return os.path.exists(reset_marker)
