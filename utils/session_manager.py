import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

class SessionManager:
    """Manage user session state and authentication"""
    
    def __init__(self):
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user_info' not in st.session_state:
            st.session_state.user_info = {}
        
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def login_user(self, user_id: str, login_method: str, role: str, additional_info: Dict[str, Any] = None) -> bool:
        """Log in a user and store their information"""
        try:
            user_info = {
                'user_id': user_id,
                'login_method': login_method,  # 'manual' or 'google'
                'role': role,  # 'student' or 'educator'
                'login_time': datetime.now().isoformat(),
                'session_id': self._generate_session_id()
            }
            
            # Add additional information based on login method
            if login_method == 'google' and additional_info:
                user_info.update({
                    'name': additional_info.get('name', ''),
                    'email': additional_info.get('email', ''),
                    'picture': additional_info.get('picture', ''),
                    'google_id': additional_info.get('id', ''),
                    'verified_email': additional_info.get('verified_email', False)
                })
            elif login_method == 'manual':
                user_info.update({
                    'name': user_id,  # Use user_id as name for manual login
                    'email': f"{user_id}@edututor.local"  # Generate local email
                })
            
            # Store in session state
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            st.session_state.login_time = datetime.now()
            
            return True
            
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return False
    
    def logout_user(self) -> bool:
        """Log out the current user"""
        try:
            # Clear authentication state
            st.session_state.authenticated = False
            st.session_state.user_info = {}
            st.session_state.login_time = None
            
            # Clear any cached data
            if 'google_credentials' in st.session_state:
                del st.session_state.google_credentials
            
            if 'oauth_flow' in st.session_state:
                del st.session_state.oauth_flow
            
            # Clear quiz-related session data
            quiz_keys = [
                'quiz_started', 'quiz_questions', 'current_question',
                'user_answers', 'quiz_start_time', 'quiz_completed', 'quiz_results'
            ]
            
            for key in quiz_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            return True
            
        except Exception as e:
            st.error(f"Logout failed: {str(e)}")
            return False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        return st.session_state.get('user_info', {})
    
    def update_user_info(self, updates: Dict[str, Any]) -> bool:
        """Update user information in session"""
        try:
            if not self.is_authenticated():
                return False
            
            current_info = st.session_state.user_info
            current_info.update(updates)
            current_info['last_updated'] = datetime.now().isoformat()
            
            st.session_state.user_info = current_info
            return True
            
        except Exception as e:
            st.error(f"Failed to update user info: {str(e)}")
            return False
    
    def update_user_data(self, key: str, value: Any) -> bool:
        """Update specific user data"""
        try:
            if not self.is_authenticated():
                return False
            
            st.session_state.user_info[key] = value
            return True
            
        except Exception as e:
            st.error(f"Failed to update user data: {str(e)}")
            return False
    
    def get_session_duration(self) -> Optional[float]:
        """Get current session duration in minutes"""
        if not self.is_authenticated() or not st.session_state.login_time:
            return None
        
        current_time = datetime.now()
        duration = current_time - st.session_state.login_time
        return duration.total_seconds() / 60  # Return in minutes
    
    def is_session_expired(self, max_duration_hours: int = 24) -> bool:
        """Check if session has expired"""
        if not self.is_authenticated():
            return True
        
        duration_minutes = self.get_session_duration()
        if duration_minutes is None:
            return True
        
        max_duration_minutes = max_duration_hours * 60
        return duration_minutes > max_duration_minutes
    
    def refresh_session(self) -> bool:
        """Refresh the current session"""
        try:
            if not self.is_authenticated():
                return False
            
            st.session_state.login_time = datetime.now()
            self.update_user_info({'last_activity': datetime.now().isoformat()})
            
            return True
            
        except Exception as e:
            st.error(f"Failed to refresh session: {str(e)}")
            return False
    
    def get_user_role(self) -> str:
        """Get current user's role"""
        user_info = self.get_user_info()
        return user_info.get('role', 'student')
    
    def is_student(self) -> bool:
        """Check if current user is a student"""
        return self.get_user_role() == 'student'
    
    def is_educator(self) -> bool:
        """Check if current user is an educator"""
        return self.get_user_role() == 'educator'
    
    def get_login_method(self) -> str:
        """Get current user's login method"""
        user_info = self.get_user_info()
        return user_info.get('login_method', 'manual')
    
    def is_google_user(self) -> bool:
        """Check if user logged in via Google"""
        return self.get_login_method() == 'google'
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        import hashlib
        import time
        import random
        
        # Create session ID from timestamp and random number
        timestamp = str(time.time())
        random_num = str(random.randint(1000, 9999))
        session_string = f"{timestamp}_{random_num}"
        
        # Hash it for security
        session_id = hashlib.md5(session_string.encode()).hexdigest()
        return session_id[:16]  # Use first 16 characters
    
    def validate_session(self) -> bool:
        """Validate current session"""
        try:
            # Check if user is authenticated
            if not self.is_authenticated():
                return False
            
            # Check if session has expired
            if self.is_session_expired():
                self.logout_user()
                return False
            
            # Check if required user info is present
            user_info = self.get_user_info()
            required_fields = ['user_id', 'role', 'login_method']
            
            for field in required_fields:
                if field not in user_info:
                    return False
            
            # Refresh session activity
            self.refresh_session()
            
            return True
            
        except Exception as e:
            st.error(f"Session validation failed: {str(e)}")
            return False
    
    def clear_all_session_data(self) -> bool:
        """Clear all session data (use with caution)"""
        try:
            # Get all session state keys
            keys_to_clear = list(st.session_state.keys())
            
            # Clear each key
            for key in keys_to_clear:
                del st.session_state[key]
            
            # Reinitialize basic session state
            self._initialize_session_state()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to clear session data: {str(e)}")
            return False
