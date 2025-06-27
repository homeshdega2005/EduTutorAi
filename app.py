import streamlit as st
import os
from dotenv import load_dotenv
from auth.google_auth import GoogleAuth
from utils.session_manager import SessionManager
from services.pinecone_service import PineconeService

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="EduTutor AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize all services"""
    try:
        pinecone_service = PineconeService()
        return pinecone_service
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        return None

def main():
    """Main application entry point"""
    st.title("🎓 EduTutor AI - Personalized Learning Platform")
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Initialize services
    pinecone_service = init_services()
    if not pinecone_service:
        st.stop()
    
    # Check if user is authenticated
    if not session_manager.is_authenticated():
        st.subheader("Welcome to EduTutor AI")
        st.write("Please log in to access your personalized learning dashboard.")
        
        # Create two columns for login options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔐 Manual Login")
            with st.form("manual_login"):
                user_id = st.text_input("User ID")
                role = st.selectbox("Role", ["student", "educator"])
                submit_manual = st.form_submit_button("Login")
                
                if submit_manual and user_id:
                    session_manager.login_user(user_id, "manual", role)
                    st.success("Login successful!")
                    st.rerun()
        
        with col2:
            st.subheader("🔍 Google Login")
            google_auth = GoogleAuth()
            
            if st.button("Login with Google", type="primary"):
                try:
                    # Initialize Google OAuth flow
                    auth_url = google_auth.get_authorization_url()
                    st.write("Please visit this URL to authorize the application:")
                    st.code(auth_url)
                    st.write("After authorization, you'll receive a code. Enter it below:")
                    
                    auth_code = st.text_input("Authorization Code")
                    if auth_code:
                        user_info = google_auth.handle_callback(auth_code)
                        if user_info:
                            # Default role for Google login is student
                            role = "student"
                            session_manager.login_user(user_info['email'], "google", role, user_info)
                            st.success(f"Welcome, {user_info['name']}!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Google authentication failed: {str(e)}")
    else:
        # User is authenticated - show main navigation
        user_info = session_manager.get_user_info()
        
        # Sidebar navigation
        st.sidebar.title(f"Welcome, {user_info.get('name', user_info['user_id'])}!")
        st.sidebar.write(f"Role: {user_info['role'].title()}")
        st.sidebar.write(f"Login Method: {user_info['login_method'].title()}")
        
        # Logout button
        if st.sidebar.button("Logout"):
            session_manager.logout_user()
            st.rerun()
        
        # Main content area
        st.write("Welcome to your personalized learning dashboard!")
        st.write("Use the sidebar to navigate to different sections of the platform.")
        
        # Download project option
        st.divider()
        st.subheader("📁 Project Download")
        
        try:
            with open("edututor-ai-project.zip", "rb") as zip_file:
                st.download_button(
                    label="Download Complete EduTutor AI Project",
                    data=zip_file.read(),
                    file_name="edututor-ai-project.zip",
                    mime="application/zip",
                    help="Download the complete project source code as a zip file"
                )
        except FileNotFoundError:
            st.info("Project zip file not found in current directory.")
        
        # Display available pages based on role
        if user_info['role'] == 'student':
            st.subheader("📚 Student Features")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info("**Student Dashboard**\nView your learning progress and statistics")
            
            with col2:
                st.info("**Take Quiz**\nAccess AI-generated personalized quizzes")
            
            with col3:
                st.info("**Quiz History**\nReview your past quiz attempts and scores")
        
        elif user_info['role'] == 'educator':
            st.subheader("👨‍🏫 Educator Features")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("**Educator Dashboard**\nView student analytics and progress tracking")
            
            with col2:
                st.info("**Student Management**\nManage student profiles and assignments")
        
        # Google Classroom sync status
        if user_info['login_method'] == 'google':
            st.subheader("🔗 Google Classroom Integration")
            if st.button("Sync with Google Classroom"):
                try:
                    from services.classroom_service import ClassroomService
                    classroom_service = ClassroomService()
                    courses = classroom_service.get_courses()
                    if courses:
                        st.success(f"Successfully synced {len(courses)} courses from Google Classroom!")
                        session_manager.update_user_data('synced_courses', courses)
                    else:
                        st.info("No courses found in your Google Classroom.")
                except Exception as e:
                    st.error(f"Failed to sync with Google Classroom: {str(e)}")

if __name__ == "__main__":
    main()
