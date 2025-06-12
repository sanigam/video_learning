"""
Utility for managing user reset operations and tracking reset events.
"""

import os
from pathlib import Path
import time

class ResetManager:
    def __init__(self):
        """Initialize the Reset Manager"""
        # Get the data directory
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.reset_users_dir = os.path.join(self.data_dir, "reset_users")
        
        # Ensure the reset users directory exists
        Path(self.reset_users_dir).mkdir(parents=True, exist_ok=True)
    
    def record_reset(self, email):
        """
        Records a user reset event
        
        Args:
            email (str): User email that was reset
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not email:
                return False
                
            # Generate sanitized filename
            sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
            reset_marker = os.path.join(self.reset_users_dir, f"{sanitized_email}.reset")
            
            # Create timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            # Write reset marker file with timestamp
            with open(reset_marker, 'w') as f:
                f.write(f"User {email} was reset at {timestamp}")
                
            return True
            
        except Exception as e:
            print(f"Error recording reset for {email}: {str(e)}")
            return False
    
    def check_if_reset(self, email):
        """
        Check if a user has been reset
        
        Args:
            email (str): User email to check
            
        Returns:
            bool: True if reset marker exists, False otherwise
        """
        if not email:
            return False
            
        # Generate sanitized filename
        sanitized_email = email.replace('@', '_at_').replace('.', '_dot_')
        reset_marker = os.path.join(self.reset_users_dir, f"{sanitized_email}.reset")
        
        return os.path.exists(reset_marker)