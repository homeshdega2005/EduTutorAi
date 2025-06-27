# EduTutor AI - Personalized Learning Platform

## Overview

EduTutor AI is a Streamlit-based educational platform that provides personalized learning experiences through AI-generated quizzes and comprehensive learning analytics. The platform supports both students and educators, offering quiz generation, progress tracking, and performance analytics with Google Classroom integration.

## System Architecture

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python-based microservices architecture
- **Vector Database**: Pinecone (with local storage fallback)
- **AI Services**: Hugging Face API for quiz generation
- **Authentication**: Google OAuth 2.0 with manual login fallback
- **External Integrations**: Google Classroom API
- **Data Visualization**: Plotly for charts and analytics

### Architecture Pattern
The application follows a service-oriented architecture with clear separation of concerns:
- **Presentation Layer**: Streamlit pages and components
- **Service Layer**: Business logic services (HuggingFace, Pinecone, Classroom)
- **Authentication Layer**: Google OAuth and session management
- **Data Layer**: Pinecone vector database with local fallback
- **Utility Layer**: Common utilities for parsing and session management

## Key Components

### Core Services
1. **PineconeService**: Manages user profiles, quiz history, and learning analytics with local storage fallback
2. **HuggingFaceService**: Generates AI-powered quiz questions using Microsoft DialoGPT-large model
3. **ClassroomService**: Integrates with Google Classroom for course management
4. **GoogleAuth**: Handles OAuth authentication and credential management

### User Interface Components
- **Main App**: Authentication gateway and service initialization
- **Student Dashboard**: Personal analytics, progress tracking, and performance metrics
- **Take Quiz**: Interactive quiz interface with timer and real-time feedback
- **Quiz History**: Historical performance analysis and progress trends
- **Educator Dashboard**: Student progress monitoring and learning analytics

### Utility Components
- **SessionManager**: User authentication state and session data management
- **QuizParser**: Quiz result calculation and performance analysis

## Data Flow

### Authentication Flow
1. Users access the platform through the main app
2. Authentication options: Google OAuth or manual login
3. Session manager stores user credentials and role information
4. Role-based access control directs users to appropriate dashboards

### Quiz Generation Flow
1. Student selects topic and difficulty level
2. HuggingFace service generates quiz questions using AI
3. Questions are presented in interactive format with timer
4. Results are calculated and stored in Pinecone/local storage
5. Analytics are updated for both student and educator dashboards

### Data Storage Flow
1. User profiles and quiz data are stored in Pinecone vector database
2. Fallback to local storage when Pinecone is unavailable
3. Quiz results include detailed breakdowns and performance metrics
4. Educator analytics aggregate student performance data

## External Dependencies

### Required API Services
- **Pinecone**: Vector database for storing user profiles and quiz history
- **Hugging Face**: AI model access for quiz question generation
- **Google OAuth**: Authentication and Google Classroom integration

### Python Dependencies
- `streamlit`: Web application framework
- `pinecone-client`: Vector database client
- `google-api-python-client`: Google services integration
- `plotly`: Data visualization and charts
- `pandas`: Data manipulation and analysis

### Configuration Requirements
All sensitive configuration is managed through environment variables:
- Hugging Face API key for AI services
- Pinecone API credentials for vector database
- Google OAuth credentials for authentication

## Deployment Strategy

### Platform Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Deployment Target**: Autoscale deployment on Replit
- **Port Configuration**: Application runs on port 5000
- **Process Management**: Streamlit server with headless configuration

### Environment Setup
- Environment variables managed through `.env` file
- Fallback mechanisms for missing API credentials
- Local storage backup for offline functionality
- Graceful degradation when external services are unavailable

### Service Initialization
- Cached resource initialization for better performance
- Error handling and service availability checks
- User-friendly error messages for service failures

## Changelog
- June 26, 2025: Initial setup and complete implementation
- June 26, 2025: Added download functionality for project zip file
- June 26, 2025: Fixed Pinecone package dependency issues
- June 26, 2025: Integrated all requested features including AI quiz generation, Google Classroom sync, and analytics dashboards

## User Preferences

Preferred communication style: Simple, everyday language.