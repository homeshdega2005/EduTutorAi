import os
import json
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import secrets
import string

class GoogleAuth:
    """Handle Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "your_google_client_id")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "your_google_client_secret")
        self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # For installed applications
        self.scopes = [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/classroom.courses.readonly',
            'https://www.googleapis.com/auth/classroom.rosters.readonly'
        ]
    
    def get_authorization_url(self):
        """Generate Google OAuth authorization URL"""
        try:
            # Create client configuration
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            }
            
            # Create flow
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store flow in session state for later use
            st.session_state.oauth_flow = flow
            
            return auth_url
        except Exception as e:
            st.error(f"Failed to generate authorization URL: {str(e)}")
            return None
    
    def handle_callback(self, auth_code):
        """Handle OAuth callback and exchange code for tokens"""
        try:
            if 'oauth_flow' not in st.session_state:
                raise Exception("OAuth flow not found. Please restart the authentication process.")
            
            flow = st.session_state.oauth_flow
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # Get user info
            user_info = self.get_user_info(credentials)
            
            # Store credentials in session state
            st.session_state.google_credentials = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            return user_info
        except Exception as e:
            st.error(f"Failed to handle OAuth callback: {str(e)}")
            return None
    
    def get_user_info(self, credentials):
        """Get user information from Google API"""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email')
            }
        except Exception as e:
            st.error(f"Failed to get user info: {str(e)}")
            return None
    
    def get_credentials_from_session(self):
        """Reconstruct credentials from session state"""
        try:
            if 'google_credentials' not in st.session_state:
                return None
            
            creds_info = st.session_state.google_credentials
            credentials = Credentials(
                token=creds_info['token'],
                refresh_token=creds_info['refresh_token'],
                token_uri=creds_info['token_uri'],
                client_id=creds_info['client_id'],
                client_secret=creds_info['client_secret'],
                scopes=creds_info['scopes']
            )
            
            return credentials
        except Exception as e:
            st.error(f"Failed to reconstruct credentials: {str(e)}")
            return None
