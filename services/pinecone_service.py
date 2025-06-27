import os
import json
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any
import hashlib

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    st.warning("Pinecone library not available. Using local storage fallback.")

class PineconeService:
    """Handle Pinecone vector database operations with fallback to local storage"""
    
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY", "your_pinecone_api_key")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "edututor")
        self.pc = None
        self.index = None
        
        if PINECONE_AVAILABLE and self.api_key != "your_pinecone_api_key":
            self._initialize_pinecone()
        else:
            st.warning("Using local storage fallback for user data.")
            self._initialize_local_storage()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone connection"""
        try:
            self.pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists, create if not
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Using standard embedding dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            
            self.index = self.pc.Index(self.index_name)
            st.success("Pinecone initialized successfully!")
            
        except Exception as e:
            st.error(f"Failed to initialize Pinecone: {str(e)}")
            self._initialize_local_storage()
    
    def _initialize_local_storage(self):
        """Initialize local storage fallback"""
        if 'user_profiles' not in st.session_state:
            st.session_state.user_profiles = {}
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = {}
    
    def create_user_profile(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Create or update user profile"""
        try:
            profile_data = {
                'user_id': user_id,
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'role': user_data.get('role', 'student'),
                'login_method': user_data.get('login_method', 'manual'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'quiz_count': 0,
                'total_score': 0,
                'average_score': 0,
                'preferred_topics': [],
                'learning_level': 'beginner',
                'google_info': user_data.get('google_info', {}),
                'synced_courses': user_data.get('synced_courses', [])
            }
            
            if self.index:
                # Use Pinecone
                vector_id = self._generate_vector_id(user_id)
                embedding = self._create_user_embedding(profile_data)
                
                self.index.upsert(vectors=[{
                    'id': vector_id,
                    'values': embedding,
                    'metadata': profile_data
                }])
            else:
                # Use local storage
                st.session_state.user_profiles[user_id] = profile_data
            
            return True
            
        except Exception as e:
            st.error(f"Failed to create user profile: {str(e)}")
            return False
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile by ID"""
        try:
            if self.index:
                # Use Pinecone
                vector_id = self._generate_vector_id(user_id)
                result = self.index.fetch(ids=[vector_id])
                
                if result.vectors and vector_id in result.vectors:
                    return result.vectors[vector_id].metadata
                else:
                    return None
            else:
                # Use local storage
                return st.session_state.user_profiles.get(user_id)
                
        except Exception as e:
            st.error(f"Failed to get user profile: {str(e)}")
            return None
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            # Update profile data
            profile.update(updates)
            profile['updated_at'] = datetime.now().isoformat()
            
            if self.index:
                # Use Pinecone
                vector_id = self._generate_vector_id(user_id)
                embedding = self._create_user_embedding(profile)
                
                self.index.upsert(vectors=[{
                    'id': vector_id,
                    'values': embedding,
                    'metadata': profile
                }])
            else:
                # Use local storage
                st.session_state.user_profiles[user_id] = profile
            
            return True
            
        except Exception as e:
            st.error(f"Failed to update user profile: {str(e)}")
            return False
    
    def store_quiz_result(self, user_id: str, quiz_data: Dict[str, Any]) -> bool:
        """Store quiz result and update user profile"""
        try:
            quiz_result = {
                'user_id': user_id,
                'quiz_id': quiz_data.get('quiz_id', self._generate_quiz_id()),
                'topic': quiz_data.get('topic', ''),
                'difficulty': quiz_data.get('difficulty', 'medium'),
                'questions': quiz_data.get('questions', []),
                'user_answers': quiz_data.get('user_answers', []),
                'score': quiz_data.get('score', 0),
                'total_questions': quiz_data.get('total_questions', 0),
                'percentage': quiz_data.get('percentage', 0),
                'time_taken': quiz_data.get('time_taken', 0),
                'completed_at': datetime.now().isoformat()
            }
            
            # Store quiz result
            if self.index:
                # Use Pinecone for quiz storage
                quiz_vector_id = f"quiz_{user_id}_{quiz_result['quiz_id']}"
                embedding = self._create_quiz_embedding(quiz_result)
                
                self.index.upsert(vectors=[{
                    'id': quiz_vector_id,
                    'values': embedding,
                    'metadata': quiz_result
                }])
            else:
                # Use local storage
                if user_id not in st.session_state.quiz_history:
                    st.session_state.quiz_history[user_id] = []
                st.session_state.quiz_history[user_id].append(quiz_result)
            
            # Update user profile with quiz statistics
            profile = self.get_user_profile(user_id)
            if profile:
                profile['quiz_count'] = profile.get('quiz_count', 0) + 1
                profile['total_score'] = profile.get('total_score', 0) + quiz_result['score']
                profile['average_score'] = profile['total_score'] / profile['quiz_count']
                
                # Update preferred topics
                topic = quiz_result['topic']
                preferred_topics = profile.get('preferred_topics', [])
                if topic not in preferred_topics:
                    preferred_topics.append(topic)
                profile['preferred_topics'] = preferred_topics
                
                self.update_user_profile(user_id, profile)
            
            return True
            
        except Exception as e:
            st.error(f"Failed to store quiz result: {str(e)}")
            return False
    
    def get_quiz_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get quiz history for a user"""
        try:
            if self.index:
                # Use Pinecone - query for user's quizzes
                query_filter = {"user_id": {"$eq": user_id}}
                results = self.index.query(
                    vector=[0.0] * 384,  # Dummy vector for metadata-only query
                    filter=query_filter,
                    top_k=100,
                    include_metadata=True
                )
                
                quiz_history = []
                for match in results.matches:
                    metadata = match.metadata
                    if metadata.get('quiz_id'):  # This is a quiz record
                        quiz_history.append(metadata)
                
                return sorted(quiz_history, key=lambda x: x.get('completed_at', ''), reverse=True)
            else:
                # Use local storage
                return st.session_state.quiz_history.get(user_id, [])
                
        except Exception as e:
            st.error(f"Failed to get quiz history: {str(e)}")
            return []
    
    def get_all_student_profiles(self) -> List[Dict[str, Any]]:
        """Get all student profiles for educator dashboard"""
        try:
            if self.index:
                # Use Pinecone - query for student profiles
                query_filter = {"role": {"$eq": "student"}}
                results = self.index.query(
                    vector=[0.0] * 384,  # Dummy vector for metadata-only query
                    filter=query_filter,
                    top_k=1000,
                    include_metadata=True
                )
                
                profiles = []
                for match in results.matches:
                    metadata = match.metadata
                    if not metadata.get('quiz_id'):  # This is a user profile, not a quiz
                        profiles.append(metadata)
                
                return profiles
            else:
                # Use local storage
                return [profile for profile in st.session_state.user_profiles.values() 
                       if profile.get('role') == 'student']
                
        except Exception as e:
            st.error(f"Failed to get student profiles: {str(e)}")
            return []
    
    def _generate_vector_id(self, user_id: str) -> str:
        """Generate vector ID for user profile"""
        return f"user_{hashlib.md5(user_id.encode()).hexdigest()}"
    
    def _generate_quiz_id(self) -> str:
        """Generate unique quiz ID"""
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12]
    
    def _create_user_embedding(self, profile_data: Dict[str, Any]) -> List[float]:
        """Create embedding vector for user profile"""
        # Simple embedding based on profile features
        # In production, you'd use a proper embedding model
        features = []
        
        # Role encoding
        role_encoding = {'student': 0.1, 'educator': 0.9}
        features.append(role_encoding.get(profile_data.get('role', 'student'), 0.1))
        
        # Learning level encoding
        level_encoding = {'beginner': 0.2, 'intermediate': 0.5, 'advanced': 0.8}
        features.append(level_encoding.get(profile_data.get('learning_level', 'beginner'), 0.2))
        
        # Quiz performance
        features.append(min(profile_data.get('average_score', 0) / 100.0, 1.0))
        
        # Pad to 384 dimensions
        while len(features) < 384:
            features.append(0.0)
        
        return features[:384]
    
    def _create_quiz_embedding(self, quiz_data: Dict[str, Any]) -> List[float]:
        """Create embedding vector for quiz result"""
        features = []
        
        # Score encoding
        features.append(quiz_data.get('percentage', 0) / 100.0)
        
        # Difficulty encoding
        difficulty_encoding = {'easy': 0.2, 'medium': 0.5, 'hard': 0.8}
        features.append(difficulty_encoding.get(quiz_data.get('difficulty', 'medium'), 0.5))
        
        # Topic hash (simple)
        topic = quiz_data.get('topic', '')
        topic_hash = sum(ord(c) for c in topic) / 1000.0 if topic else 0.0
        features.append(min(topic_hash, 1.0))
        
        # Pad to 384 dimensions
        while len(features) < 384:
            features.append(0.0)
        
        return features[:384]
