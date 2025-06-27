import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.session_manager import SessionManager
from services.pinecone_service import PineconeService

st.set_page_config(
    page_title="Quiz History - EduTutor AI",
    page_icon="📚",
    layout="wide"
)

def main():
    """Quiz History main function"""
    st.title("📚 Quiz History")
    
    # Initialize services
    session_manager = SessionManager()
    pinecone_service = PineconeService()
    
    # Check authentication
    if not session_manager.is_authenticated():
        st.error("Please log in to view your quiz history.")
        st.stop()
    
    user_info = session_manager.get_user_info()
    
    # Check if user is a student
    if user_info.get('role') != 'student':
        st.error("Quiz history is only available for students.")
        st.stop()
    
    # Get quiz history
    quiz_history = pinecone_service.get_quiz_history(user_info['user_id'])
    
    if not quiz_history:
        st.info("No quiz history found. Take your first quiz to see your results here!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Take Your First Quiz", type="primary", use_container_width=True):
                st.switch_page("pages/2_Take_Quiz.py")
        return
    
    # Filter controls
    st.subheader("🔍 Filter Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Topic filter
        all_topics = sorted(list(set([quiz.get('topic', 'Unknown') for quiz in quiz_history])))
        selected_topics = st.multiselect(
            "Topics",
            all_topics,
            default=all_topics,
            help="Filter by quiz topics"
        )
    
    with col2:
        # Difficulty filter
        all_difficulties = sorted(list(set([quiz.get('difficulty', 'medium') for quiz in quiz_history])))
        selected_difficulties = st.multiselect(
            "Difficulty",
            all_difficulties,
            default=all_difficulties,
            help="Filter by difficulty level"
        )
    
    with col3:
        # Date range filter
        date_range = st.selectbox(
            "Date Range",
            ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
            help="Filter by date range"
        )
    
    with col4:
        # Score filter
        min_score = st.slider(
            "Minimum Score (%)",
            0, 100, 0,
            help="Filter by minimum score percentage"
        )
    
    # Apply filters
    filtered_history = quiz_history.copy()
    
    # Topic filter
    if selected_topics:
        filtered_history = [q for q in filtered_history if q.get('topic') in selected_topics]
    
    # Difficulty filter
    if selected_difficulties:
        filtered_history = [q for q in filtered_history if q.get('difficulty') in selected_difficulties]
    
    # Date range filter
    if date_range != "All Time":
        cutoff_date = datetime.now()
        if date_range == "Last 7 Days":
            cutoff_date -= timedelta(days=7)
        elif date_range == "Last 30 Days":
            cutoff_date -= timedelta(days=30)
        elif date_range == "Last 90 Days":
            cutoff_date -= timedelta(days=90)
        
        filtered_history = [q for q in filtered_history 
                           if datetime.fromisoformat(q.get('completed_at', '')) >= cutoff_date]
    
    # Score filter
    filtered_history = [q for q in filtered_history if q.get('percentage', 0) >= min_score]
    
    st.divider()
    
    if not filtered_history:
        st.warning("No quizzes match your current filters. Try adjusting the filter criteria.")
        return
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    total_quizzes = len(filtered_history)
    avg_score = sum(q.get('percentage', 0) for q in filtered_history) / total_quizzes
    best_score = max(q.get('percentage', 0) for q in filtered_history)
    total_time = sum(q.get('time_taken', 0) for q in filtered_history)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Quizzes", total_quizzes)
    
    with col2:
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col3:
        st.metric("Best Score", f"{best_score:.1f}%")
    
    with col4:
        st.metric("Total Time", f"{total_time/60:.1f} min")
    
    # Charts
    st.subheader("📈 Performance Charts")
    
    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(filtered_history)
    df['completed_at'] = pd.to_datetime(df['completed_at'])
    df = df.sort_values('completed_at')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Score trend over time
        fig_trend = px.line(
            df,
            x='completed_at',
            y='percentage',
            title='Score Trend Over Time',
            labels={'percentage': 'Score (%)', 'completed_at': 'Date'},
            markers=True
        )
        fig_trend.update_layout(showlegend=False)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        # Score distribution
        fig_hist = px.histogram(
            df,
            x='percentage',
            nbins=10,
            title='Score Distribution',
            labels={'percentage': 'Score (%)', 'count': 'Number of Quizzes'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # Performance by topic
        topic_stats = df.groupby('topic')['percentage'].agg(['mean', 'count']).reset_index()
        topic_stats.columns = ['Topic', 'Average Score', 'Quiz Count']
        topic_stats = topic_stats.sort_values('Average Score', ascending=True)
        
        fig_topics = px.bar(
            topic_stats,
            x='Average Score',
            y='Topic',
            orientation='h',
            title='Average Score by Topic',
            labels={'Average Score': 'Average Score (%)'},
            color='Average Score',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_topics, use_container_width=True)
    
    with col4:
        # Performance by difficulty
        diff_stats = df.groupby('difficulty')['percentage'].agg(['mean', 'count']).reset_index()
        diff_stats.columns = ['Difficulty', 'Average Score', 'Quiz Count']
        diff_stats['Difficulty'] = diff_stats['Difficulty'].str.title()
        
        fig_diff = px.bar(
            diff_stats,
            x='Difficulty',
            y='Average Score',
            title='Performance by Difficulty',
            labels={'Average Score': 'Average Score (%)'},
            color='Average Score',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_diff, use_container_width=True)
    
    # Detailed quiz list
    st.subheader("📋 Detailed Quiz List")
    
    # Prepare data for table display
    table_data = []
    for i, quiz in enumerate(filtered_history):
        table_data.append({
            '#': i + 1,
            'Date': quiz.get('completed_at', '')[:10],
            'Time': quiz.get('completed_at', '')[11:16],
            'Topic': quiz.get('topic', 'Unknown'),
            'Difficulty': quiz.get('difficulty', 'medium').title(),
            'Questions': quiz.get('total_questions', 0),
            'Score': f"{quiz.get('score', 0)}/{quiz.get('total_questions', 0)}",
            'Percentage': f"{quiz.get('percentage', 0):.1f}%",
            'Duration': f"{quiz.get('time_taken', 0):.1f}s",
            'Quiz ID': quiz.get('quiz_id', 'Unknown')
        })
    
    df_table = pd.DataFrame(table_data)
    
    # Display table with styling
    def color_percentage(val):
        if 'Percentage' in val.name:
            percentage = float(val.replace('%', ''))
            if percentage >= 80:
                return 'background-color: #d4edda'
            elif percentage >= 60:
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        return ''
    
    # Use column configuration for better display
    column_config = {
        '#': st.column_config.NumberColumn("Quiz #", width="small"),
        'Date': st.column_config.DateColumn("Date", width="medium"),
        'Time': st.column_config.TextColumn("Time", width="small"),
        'Topic': st.column_config.TextColumn("Topic", width="large"),
        'Difficulty': st.column_config.TextColumn("Difficulty", width="medium"),
        'Questions': st.column_config.NumberColumn("Questions", width="small"),
        'Score': st.column_config.TextColumn("Score", width="medium"),
        'Percentage': st.column_config.ProgressColumn("Score %", min_value=0, max_value=100, width="medium"),
        'Duration': st.column_config.TextColumn("Duration", width="medium"),
        'Quiz ID': st.column_config.TextColumn("Quiz ID", width="medium")
    }
    
    st.dataframe(
        df_table,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )
    
    # Quiz details expander
    if st.checkbox("Show detailed quiz breakdown"):
        st.subheader("🔍 Quiz Details")
        
        # Select quiz to view details
        quiz_options = [f"Quiz {i+1}: {q.get('topic', 'Unknown')} ({q.get('completed_at', '')[:10]})" 
                       for i, q in enumerate(filtered_history)]
        
        selected_quiz_idx = st.selectbox(
            "Select a quiz to view details:",
            range(len(quiz_options)),
            format_func=lambda i: quiz_options[i]
        )
        
        if selected_quiz_idx is not None:
            selected_quiz = filtered_history[selected_quiz_idx]
            
            # Quiz header
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Topic:** {selected_quiz.get('topic', 'Unknown')}")
                st.write(f"**Difficulty:** {selected_quiz.get('difficulty', 'medium').title()}")
            with col2:
                st.write(f"**Date:** {selected_quiz.get('completed_at', '')[:10]}")
                st.write(f"**Time:** {selected_quiz.get('completed_at', '')[11:16]}")
            with col3:
                st.write(f"**Score:** {selected_quiz.get('score', 0)}/{selected_quiz.get('total_questions', 0)}")
                st.write(f"**Percentage:** {selected_quiz.get('percentage', 0):.1f}%")
            
            # Questions and answers
            questions = selected_quiz.get('questions', [])
            user_answers = selected_quiz.get('user_answers', {})
            
            if questions:
                for i, question in enumerate(questions):
                    user_answer = user_answers.get(str(i), "Not answered")
                    correct_answer = question.get('correct_answer', 'Unknown')
                    is_correct = user_answer == correct_answer
                    
                    with st.expander(f"Question {i+1} - {'✅ Correct' if is_correct else '❌ Incorrect'}"):
                        st.write(f"**Question:** {question['question']}")
                        
                        options = question.get('options', {})
                        for key, value in options.items():
                            icon = ""
                            if key == correct_answer:
                                icon = "✅"
                            elif key == user_answer and not is_correct:
                                icon = "❌"
                            st.write(f"{icon} {key}) {value}")
                        
                        st.write(f"**Your answer:** {user_answer}")
                        st.write(f"**Correct answer:** {correct_answer}")
                        
                        if question.get('explanation'):
                            st.write(f"**Explanation:** {question['explanation']}")
    
    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Take New Quiz", type="primary", use_container_width=True):
            st.switch_page("pages/2_Take_Quiz.py")
    
    with col2:
        if st.button("View Dashboard", use_container_width=True):
            st.switch_page("pages/1_Student_Dashboard.py")
    
    with col3:
        # Export functionality
        if st.button("Export History", use_container_width=True):
            csv_data = df_table.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"quiz_history_{user_info['user_id']}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
