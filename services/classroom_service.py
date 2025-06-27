import streamlit as st
from googleapiclient.discovery import build
from auth.google_auth import GoogleAuth
from datetime import datetime

class ClassroomService:
    """Handle Google Classroom API interactions"""
    
    def __init__(self):
        self.google_auth = GoogleAuth()
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Classroom service"""
        try:
            credentials = self.google_auth.get_credentials_from_session()
            if credentials:
                self.service = build('classroom', 'v1', credentials=credentials)
            else:
                st.warning("Google credentials not found. Please log in with Google first.")
        except Exception as e:
            st.error(f"Failed to initialize Classroom service: {str(e)}")
    
    def get_courses(self):
        """Get all courses for the authenticated user"""
        try:
            if not self.service:
                return None
            
            results = self.service.courses().list().execute()
            courses = results.get('courses', [])
            
            # Format course data
            formatted_courses = []
            for course in courses:
                formatted_courses.append({
                    'id': course.get('id'),
                    'name': course.get('name'),
                    'section': course.get('section', ''),
                    'description': course.get('description', ''),
                    'room': course.get('room', ''),
                    'owner_id': course.get('ownerId'),
                    'creation_time': course.get('creationTime'),
                    'update_time': course.get('updateTime'),
                    'enrollment_code': course.get('enrollmentCode'),
                    'course_state': course.get('courseState'),
                    'alternate_link': course.get('alternateLink')
                })
            
            return formatted_courses
        except Exception as e:
            st.error(f"Failed to fetch courses: {str(e)}")
            return None
    
    def get_students(self, course_id):
        """Get students enrolled in a specific course"""
        try:
            if not self.service:
                return None
            
            results = self.service.courses().students().list(courseId=course_id).execute()
            students = results.get('students', [])
            
            # Format student data
            formatted_students = []
            for student in students:
                profile = student.get('profile', {})
                formatted_students.append({
                    'course_id': course_id,
                    'user_id': student.get('userId'),
                    'email': profile.get('emailAddress'),
                    'name': profile.get('name', {}).get('fullName', ''),
                    'photo_url': profile.get('photoUrl', ''),
                    'student_id': student.get('studentId')
                })
            
            return formatted_students
        except Exception as e:
            st.error(f"Failed to fetch students for course {course_id}: {str(e)}")
            return None
    
    def get_course_work(self, course_id):
        """Get assignments/coursework for a specific course"""
        try:
            if not self.service:
                return None
            
            results = self.service.courses().courseWork().list(courseId=course_id).execute()
            coursework = results.get('courseWork', [])
            
            # Format coursework data
            formatted_coursework = []
            for work in coursework:
                formatted_coursework.append({
                    'course_id': course_id,
                    'id': work.get('id'),
                    'title': work.get('title'),
                    'description': work.get('description', ''),
                    'materials': work.get('materials', []),
                    'state': work.get('state'),
                    'alternate_link': work.get('alternateLink'),
                    'creation_time': work.get('creationTime'),
                    'update_time': work.get('updateTime'),
                    'due_date': work.get('dueDate'),
                    'due_time': work.get('dueTime'),
                    'max_points': work.get('maxPoints'),
                    'work_type': work.get('workType'),
                    'submission_modification_mode': work.get('submissionModificationMode')
                })
            
            return formatted_coursework
        except Exception as e:
            st.error(f"Failed to fetch coursework for course {course_id}: {str(e)}")
            return None
    
    def sync_classroom_data(self, user_id):
        """Sync all classroom data for a user"""
        try:
            sync_data = {
                'user_id': user_id,
                'sync_time': datetime.now().isoformat(),
                'courses': [],
                'students': {},
                'coursework': {}
            }
            
            # Get all courses
            courses = self.get_courses()
            if courses:
                sync_data['courses'] = courses
                
                # For each course, get students and coursework
                for course in courses:
                    course_id = course['id']
                    
                    # Get students
                    students = self.get_students(course_id)
                    if students:
                        sync_data['students'][course_id] = students
                    
                    # Get coursework
                    coursework = self.get_course_work(course_id)
                    if coursework:
                        sync_data['coursework'][course_id] = coursework
            
            return sync_data
        except Exception as e:
            st.error(f"Failed to sync classroom data: {str(e)}")
            return None
