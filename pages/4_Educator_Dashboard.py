import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.session_manager import SessionManager
from services.pinecone_service import PineconeService

st.set_page_config(
    page_title="Educator Dashboard - EduTutor AI",
    page_icon="👨‍🏫",
    layout="wide"
)

def main():
    """Educator Dashboard main function"""
    st.title("👨‍🏫 Educator Dashboard")
    
    # Initialize services
    session_manager = SessionManager()
    pinecone_service = PineconeService()
    
    # Check authentication
    if not session_manager.is_authenticated():
        st.error("Please log in to access the educator dashboard.")
        st.stop()
    
    user_info = session_manager.get_user_info()
    
    # Check if user is an educator
    if user_info.get('role') != 'educator':
        st.error("This dashboard is only available for educators.")
        st.stop()
    
    st.subheader(f"Welcome, {user_info.get('name', user_info['user_id'])}!")
    st.write("Monitor student progress and analyze learning analytics.")
    
    # Get all student profiles
    with st.spinner("Loading student data..."):
        student_profiles = pinecone_service.get_all_student_profiles()
    
    if not student_profiles:
        st.info("No student data available yet. Students need to create profiles and take quizzes for data to appear here.")
        return
    
    # Overview metrics
    st.subheader("📊 Overview")
    
    total_students = len(student_profiles)
    active_students = len([s for s in student_profiles if s.get('quiz_count', 0) > 0])
    total_quizzes = sum(s.get('quiz_count', 0) for s in student_profiles)
    avg_performance = sum(s.get('average_score', 0) for s in student_profiles) / total_students if total_students > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", total_students)
    
    with col2:
        st.metric("Active Students", active_students)
    
    with col3:
        st.metric("Total Quizzes", total_quizzes)
    
    with col4:
        st.metric("Avg Performance", f"{avg_performance:.1f}%")
    
    # Student performance analysis
    st.divider()
    st.subheader("📈 Student Performance Analysis")
    
    # Convert to DataFrame for easier analysis
    df_students = pd.DataFrame(student_profiles)
    df_students['created_at'] = pd.to_datetime(df_students['created_at'])
    
    # Performance distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # Score distribution
        if not df_students.empty and 'average_score' in df_students.columns:
            fig_dist = px.histogram(
                df_students[df_students['average_score'] > 0],
                x='average_score',
                nbins=10,
                title='Student Score Distribution',
                labels={'average_score': 'Average Score (%)', 'count': 'Number of Students'}
            )
            st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        # Activity levels
        activity_data = df_students['quiz_count'].value_counts().sort_index()
        fig_activity = px.bar(
            x=activity_data.index,
            y=activity_data.values,
            title='Student Activity Levels',
            labels={'x': 'Number of Quizzes Taken', 'y': 'Number of Students'}
        )
        st.plotly_chart(fig_activity, use_container_width=True)
    
    # Student registration over time
    col3, col4 = st.columns(2)
    
    with col3:
        # Registration trend
        df_students['month'] = df_students['created_at'].dt.to_period('M')
        monthly_registrations = df_students['month'].value_counts().sort_index()
        
        fig_reg = px.line(
            x=[str(m) for m in monthly_registrations.index],
            y=monthly_registrations.values,
            title='Student Registration Trend',
            labels={'x': 'Month', 'y': 'New Registrations'},
            markers=True
        )
        st.plotly_chart(fig_reg, use_container_width=True)
    
    with col4:
        # Learning levels
        level_counts = df_students['learning_level'].value_counts()
        fig_levels = px.pie(
            values=level_counts.values,
            names=level_counts.index,
            title='Student Learning Levels'
        )
        st.plotly_chart(fig_levels, use_container_width=True)
    
    # Detailed student list
    st.divider()
    st.subheader("👥 Student Details")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_quizzes = st.slider("Minimum Quizzes Taken", 0, max(df_students['quiz_count']) if not df_students.empty else 10, 0)
    
    with col2:
        learning_levels = df_students['learning_level'].unique() if not df_students.empty else ['beginner']
        selected_levels = st.multiselect("Learning Levels", learning_levels, default=learning_levels)
    
    with col3:
        sort_by = st.selectbox("Sort By", ["Name", "Quiz Count", "Average Score", "Registration Date"])
    
    # Apply filters
    filtered_students = df_students[
        (df_students['quiz_count'] >= min_quizzes) &
        (df_students['learning_level'].isin(selected_levels))
    ].copy()
    
    # Sort students
    if sort_by == "Name":
        filtered_students = filtered_students.sort_values('name')
    elif sort_by == "Quiz Count":
        filtered_students = filtered_students.sort_values('quiz_count', ascending=False)
    elif sort_by == "Average Score":
        filtered_students = filtered_students.sort_values('average_score', ascending=False)
    elif sort_by == "Registration Date":
        filtered_students = filtered_students.sort_values('created_at', ascending=False)
    
    # Display student table
    if not filtered_students.empty:
        # Prepare table data
        table_data = []
        for _, student in filtered_students.iterrows():
            table_data.append({
                'Name': student.get('name', 'Unknown'),
                'Email': student.get('email', 'N/A'),
                'Quizzes': student.get('quiz_count', 0),
                'Avg Score': f"{student.get('average_score', 0):.1f}%",
                'Level': student.get('learning_level', 'beginner').title(),
                'Registered': student.get('created_at').strftime('%Y-%m-%d') if pd.notna(student.get('created_at')) else 'Unknown',
                'Last Active': student.get('updated_at', '')[:10] if student.get('updated_at') else 'Unknown'
            })
        
        df_table = pd.DataFrame(table_data)
        
        # Column configuration
        column_config = {
            'Name': st.column_config.TextColumn("Student Name", width="large"),
            'Email': st.column_config.TextColumn("Email", width="large"),
            'Quizzes': st.column_config.NumberColumn("Quizzes Taken", width="small"),
            'Avg Score': st.column_config.ProgressColumn("Avg Score", min_value=0, max_value=100, width="medium"),
            'Level': st.column_config.TextColumn("Level", width="medium"),
            'Registered': st.column_config.DateColumn("Registered", width="medium"),
            'Last Active': st.column_config.DateColumn("Last Active", width="medium")
        }
        
        st.dataframe(
            df_table,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )
        
        # Individual student analysis
        if st.checkbox("View individual student details"):
            student_names = [f"{s.get('name', 'Unknown')} ({s.get('email', 'N/A')})" 
                           for _, s in filtered_students.iterrows()]
            
            selected_student_idx = st.selectbox(
                "Select a student:",
                range(len(student_names)),
                format_func=lambda i: student_names[i]
            )
            
            if selected_student_idx is not None:
                selected_student = filtered_students.iloc[selected_student_idx]
                
                st.subheader(f"📊 {selected_student.get('name', 'Unknown')} - Detailed Analysis")
                
                # Student overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Quizzes", selected_student.get('quiz_count', 0))
                
                with col2:
                    st.metric("Average Score", f"{selected_student.get('average_score', 0):.1f}%")
                
                with col3:
                    st.metric("Learning Level", selected_student.get('learning_level', 'beginner').title())
                
                with col4:
                    total_score = selected_student.get('total_score', 0)
                    st.metric("Total Points", int(total_score))
                
                # Get student's quiz history
                student_id = selected_student.get('user_id')
                if student_id:
                    quiz_history = pinecone_service.get_quiz_history(student_id)
                    
                    if quiz_history:
                        # Convert to DataFrame
                        df_quiz = pd.DataFrame(quiz_history)
                        df_quiz['completed_at'] = pd.to_datetime(df_quiz['completed_at'])
                        df_quiz = df_quiz.sort_values('completed_at')
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Performance trend
                            fig_trend = px.line(
                                df_quiz,
                                x='completed_at',
                                y='percentage',
                                title=f'{selected_student.get("name", "Student")} - Performance Trend',
                                labels={'percentage': 'Score (%)', 'completed_at': 'Date'},
                                markers=True
                            )
                            st.plotly_chart(fig_trend, use_container_width=True)
                        
                        with col2:
                            # Topic performance
                            topic_performance = df_quiz.groupby('topic')['percentage'].mean().reset_index()
                            fig_topics = px.bar(
                                topic_performance,
                                x='topic',
                                y='percentage',
                                title=f'{selected_student.get("name", "Student")} - Topic Performance',
                                labels={'percentage': 'Average Score (%)', 'topic': 'Topic'}
                            )
                            fig_topics.update_xaxis(tickangle=45)
                            st.plotly_chart(fig_topics, use_container_width=True)
                        
                        # Recent quiz results
                        st.write("**Recent Quiz Results:**")
                        recent_quizzes = quiz_history[:5]  # Last 5 quizzes
                        
                        for i, quiz in enumerate(recent_quizzes):
                            with st.expander(f"Quiz {i+1}: {quiz.get('topic', 'Unknown')} - {quiz.get('completed_at', '')[:10]}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Score:** {quiz.get('score', 0)}/{quiz.get('total_questions', 0)}")
                                with col2:
                                    st.write(f"**Percentage:** {quiz.get('percentage', 0):.1f}%")
                                with col3:
                                    st.write(f"**Time:** {quiz.get('time_taken', 0):.1f}s")
                                
                                st.write(f"**Difficulty:** {quiz.get('difficulty', 'medium').title()}")
                    else:
                        st.info("No quiz history available for this student.")
    else:
        st.info("No students match the current filter criteria.")
    
    # Google Classroom integration for educators
    if user_info.get('login_method') == 'google':
        st.divider()
        st.subheader("🔗 Google Classroom Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Sync Google Classroom Data", type="primary"):
                try:
                    from services.classroom_service import ClassroomService
                    classroom_service = ClassroomService()
                    
                    with st.spinner("Syncing classroom data..."):
                        sync_data = classroom_service.sync_classroom_data(user_info['user_id'])
                        
                        if sync_data:
                            st.success("Successfully synced Google Classroom data!")
                            
                            # Display sync summary
                            courses = sync_data.get('courses', [])
                            total_students = sum(len(students) for students in sync_data.get('students', {}).values())
                            total_assignments = sum(len(work) for work in sync_data.get('coursework', {}).values())
                            
                            st.write(f"**Synced:** {len(courses)} courses, {total_students} students, {total_assignments} assignments")
                        else:
                            st.error("Failed to sync Google Classroom data.")
                except Exception as e:
                    st.error(f"Sync failed: {str(e)}")
        
        with col2:
            st.info("**Google Classroom Integration**\n\nSync your classroom data to view student rosters and assignments alongside quiz performance.")
    
    # Export functionality
    st.divider()
    st.subheader("📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Student List", use_container_width=True):
            if not df_table.empty:
                csv_data = df_table.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"student_list_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("Generate Report", use_container_width=True):
            st.info("Advanced reporting feature coming soon!")
    
    with col3:
        if st.button("Student Analytics", use_container_width=True):
            st.info("Detailed analytics dashboard coming soon!")

if __name__ == "__main__":
    main()
