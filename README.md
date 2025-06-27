# EduTutor AI - Personalized Learning Platform

## Overview

EduTutor AI is a comprehensive educational platform that provides personalized learning experiences through AI-generated quizzes, performance analytics, and Google Classroom integration. Built with Streamlit and powered by Hugging Face AI models.

## Features

### Core Functionality
- **AI-Powered Quiz Generation**: Create personalized quizzes using Hugging Face models
- **Performance Analytics**: Detailed charts and insights on learning progress
- **Multi-Role Support**: Separate dashboards for students and educators
- **Google Classroom Integration**: Sync courses, students, and assignments
- **Flexible Authentication**: Manual login or Google OAuth

### Student Features
- Personal dashboard with performance metrics
- Interactive quiz-taking with timer and navigation
- Comprehensive quiz history with filtering
- Topic and difficulty analysis
- Study recommendations based on performance

### Educator Features
- Student progress monitoring and analytics
- Class performance overview
- Individual student detailed analysis
- Google Classroom data synchronization
- Export functionality for reports

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Dependencies
Install required packages:

```bash
pip install streamlit google-api-python-client google-auth google-auth-oauthlib pandas plotly python-dotenv requests
```

### Environment Setup

1. Copy `.env.example` to `.env`
2. Configure your API keys:

```env
# Hugging Face API Configuration
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Pinecone Configuration (Optional)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=edututor

# Google OAuth Configuration (Optional)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Application Configuration
SECRET_KEY=your_secret_key_here
```

## Running the Application

### Local Development
```bash
streamlit run app.py --server.port 5000
```

### Production Deployment
The application is configured for deployment on Replit with proper server settings.

## Usage

### Getting Started
1. Launch the application
2. Choose login method:
   - **Manual Login**: Enter any User ID and select role (student/educator)
   - **Google Login**: Authenticate with Google for classroom integration

### For Students
1. Access the Student Dashboard to view performance metrics
2. Take quizzes by selecting topic, difficulty, and question count
3. Review quiz history with detailed analytics
4. Track progress across different subjects

### For Educators
1. Monitor student progress on the Educator Dashboard
2. View class-wide analytics and performance trends
3. Access individual student detailed reports
4. Sync Google Classroom data for integrated management

## Architecture

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **AI Services**: Hugging Face API for quiz generation
- **Authentication**: Google OAuth 2.0 with manual fallback
- **Data Storage**: Pinecone vector database with local storage fallback
- **Visualization**: Plotly for interactive charts and analytics

### Project Structure
```
edututor-ai/
├── auth/                 # Authentication modules
├── pages/               # Streamlit pages
├── services/            # Core business logic services
├── utils/               # Utility functions and helpers
├── .streamlit/          # Streamlit configuration
├── app.py              # Main application entry point
└── .env.example        # Environment configuration template
```

## Configuration

### Streamlit Settings
Located in `.streamlit/config.toml`:
- Server runs on 0.0.0.0:5000 for proper deployment
- Headless mode enabled for production

### API Integration
- **Hugging Face**: Uses GPT-2 model for quiz generation with fallback questions
- **Google Classroom**: Full integration for course and student management
- **Pinecone**: Vector database for user profiles and quiz storage

## Data Privacy

- User data is stored securely with proper authentication
- Google OAuth follows secure authorization flows
- Local storage fallback ensures functionality without external dependencies
- No sensitive data is logged or exposed

## Troubleshooting

### Common Issues
1. **Package Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Verify environment variables are set correctly
3. **Port Conflicts**: Application uses port 5000 by default
4. **Google Auth**: Requires proper OAuth app configuration

### Development Notes
- Application includes comprehensive error handling
- Fallback mechanisms ensure core functionality without API keys
- Session management maintains user state across interactions

## Contributing

This project follows a modular architecture making it easy to:
- Add new quiz generation models
- Integrate additional authentication providers
- Extend analytics and reporting features
- Add new educational content types

## Support

The platform is designed to be self-contained with minimal external dependencies. Core features work with manual login and local storage, while enhanced features require API configuration.