import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils.session_manager import SessionManager
from services.pinecone_service import PineconeService

st.set_page_config(page_title="Student Dashboard - EduTutor AI",
                   page_icon="📊",
                   layout="wide")


def main():
    """Student Dashboard main function"""
    st.title("📊 Student Dashboard")

    # Initialize services
    session_manager = SessionManager()
    pinecone_service = PineconeService()

    # Check authentication
    if not session_manager.is_authenticated():
        st.error("Please log in to access your dashboard.")
        st.stop()

    user_info = session_manager.get_user_info()

    # Check if user is a student
    if user_info.get('role') != 'student':
        st.error("This dashboard is only available for students.")
        st.stop()

    # Get user profile
    user_profile = pinecone_service.get_user_profile(user_info['user_id'])
    if not user_profile:
        # Create new profile if doesn't exist
        pinecone_service.create_user_profile(user_info['user_id'], user_info)
        user_profile = pinecone_service.get_user_profile(user_info['user_id'])

    # Dashboard header
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader(
            f"Welcome back, {user_profile.get('name', user_info['user_id'])}!")
        st.write(
            f"Member since: {user_profile.get('created_at', 'Unknown')[:10]}")

    with col2:
        st.metric("Total Quizzes", user_profile.get('quiz_count', 0))

    with col3:
        avg_score = user_profile.get('average_score', 0)
        st.metric("Average Score", f"{avg_score:.1f}%")

    st.divider()

    # Get quiz history
    quiz_history = pinecone_service.get_quiz_history(user_info['user_id'])

    if quiz_history:
        # Performance overview
        st.subheader("📈 Performance Overview")

        # Create performance charts
        col1, col2 = st.columns(2)

        with col1:
            # Score trend chart
            df_scores = pd.DataFrame(quiz_history)
            df_scores['completed_at'] = pd.to_datetime(
                df_scores['completed_at'])
            df_scores = df_scores.sort_values('completed_at')

            fig_trend = px.line(df_scores,
                                x='completed_at',
                                y='percentage',
                                title='Quiz Score Trend',
                                labels={
                                    'percentage': 'Score (%)',
                                    'completed_at': 'Date'
                                })
            fig_trend.update_layout(showlegend=False)
            st.plotly_chart(fig_trend, use_container_width=True)

        with col2:
            # Topics performance
            topic_scores = df_scores.groupby(
                'topic')['percentage'].mean().reset_index()
            topic_scores = topic_scores.sort_values('percentage',
                                                    ascending=True)

            fig_topics = px.bar(topic_scores,
                                x='percentage',
                                y='topic',
                                orientation='h',
                                title='Average Score by Topic',
                                labels={
                                    'percentage': 'Average Score (%)',
                                    'topic': 'Topic'
                                })
            st.plotly_chart(fig_topics, use_container_width=True)

        # Recent quizzes
        st.subheader("🕒 Recent Quiz Results")

        # Display recent quizzes in a table
        recent_quizzes = quiz_history[:10]  # Last 10 quizzes
        quiz_data = []

        for quiz in recent_quizzes:
            quiz_data.append({
                'Date':
                quiz.get('completed_at', '')[:10],
                'Topic':
                quiz.get('topic', 'Unknown'),
                'Difficulty':
                quiz.get('difficulty', 'Medium').title(),
                'Score':
                f"{quiz.get('score', 0)}/{quiz.get('total_questions', 0)}",
                'Percentage':
                f"{quiz.get('percentage', 0):.1f}%",
                'Time':
                f"{quiz.get('time_taken', 0):.1f}s"
            })

        if quiz_data:
            df_recent = pd.DataFrame(quiz_data)
            st.dataframe(df_recent, use_container_width=True, hide_index=True)

        # Learning insights
        st.subheader("🎯 Learning Insights")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Strongest topics
            if len(topic_scores) > 0:
                best_topic = topic_scores.iloc[-1]
                st.success(f"**Strongest Topic**: {best_topic['topic']}")
                st.write(f"Average Score: {best_topic['percentage']:.1f}%")

        with col2:
            # Topics needing improvement
            if len(topic_scores) > 0:
                weak_topic = topic_scores.iloc[0]
                st.warning(f"**Needs Improvement**: {weak_topic['topic']}")
                st.write(f"Average Score: {weak_topic['percentage']:.1f}%")

        with col3:
            # Study streak
            if len(quiz_history) > 1:
                recent_dates = [
                    datetime.fromisoformat(q['completed_at']).date()
                    for q in quiz_history[:7]
                ]
                unique_dates = len(set(recent_dates))
                st.info(
                    f"**Recent Activity**: {unique_dates} days in last week")

        # Difficulty analysis
        st.subheader("⚖️ Difficulty Analysis")

        difficulty_scores = df_scores.groupby('difficulty')['percentage'].agg(
            ['mean', 'count']).reset_index()
        difficulty_scores.columns = [
            'Difficulty', 'Average Score', 'Quiz Count'
        ]
        difficulty_scores['Difficulty'] = difficulty_scores[
            'Difficulty'].str.title()

        col1, col2 = st.columns(2)

        with col1:
            # Difficulty performance
            fig_diff = px.bar(difficulty_scores,
                              x='Difficulty',
                              y='Average Score',
                              title='Performance by Difficulty Level',
                              color='Average Score',
                              color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_diff, use_container_width=True)

        with col2:
            # Quiz distribution
            fig_dist = px.pie(difficulty_scores,
                              values='Quiz Count',
                              names='Difficulty',
                              title='Quiz Distribution by Difficulty')
            st.plotly_chart(fig_dist, use_container_width=True)

    else:
        # No quiz history
        st.info(
            "No quiz history found. Take your first quiz to see your performance dashboard!"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Take Your First Quiz",
                         type="primary",
                         use_container_width=True):
                st.switch_page("pages/2_Take_Quiz.py")

    # Google Classroom integration status
    if user_info.get('login_method') == 'google':
        st.divider()
        st.subheader("🔗 Google Classroom Integration")

        synced_courses = user_profile.get('synced_courses', [])
        if synced_courses:
            st.success(
                f"✅ Synced with {len(synced_courses)} Google Classroom courses"
            )

            with st.expander("View Synced Courses"):
                for course in synced_courses[:5]:  # Show first 5 courses
                    st.write(f"**{course.get('name', 'Unknown Course')}**")
                    if course.get('section'):
                        st.write(f"Section: {course['section']}")
                    if course.get('description'):
                        st.write(
                            f"Description: {course['description'][:100]}...")
                    st.divider()
        else:
            st.warning("No Google Classroom courses synced yet.")
            if st.button("Sync with Google Classroom"):
                st.info(
                    "Please use the sync button on the main page to connect your Google Classroom."
                )

    # Quick actions
    st.divider()
    st.subheader("🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 Take New Quiz", use_container_width=True):
            st.switch_page("pages/2_Take_Quiz.py")

    with col2:
        if st.button("📚 View Quiz History", use_container_width=True):
            st.switch_page("pages/3_Quiz_History.py")

    with col3:
        if st.button("⚙️ Update Profile", use_container_width=True):
            st.info("Profile update functionality coming soon!")


if __name__ == "__main__":
    main()
