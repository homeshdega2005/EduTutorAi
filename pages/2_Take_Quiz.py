import streamlit as st
import time
from datetime import datetime
from utils.session_manager import SessionManager
from services.huggingface_service import HuggingFaceService
from services.pinecone_service import PineconeService
from utils.quiz_parser import QuizParser

st.set_page_config(
    page_title="Take Quiz - EduTutor AI",
    page_icon="📝",
    layout="wide"
)

def main():
    """Take Quiz main function"""
    st.title("📝 Take Quiz")
    
    # Initialize services
    session_manager = SessionManager()
    hf_service = HuggingFaceService()
    pinecone_service = PineconeService()
    quiz_parser = QuizParser()
    
    # Check authentication
    if not session_manager.is_authenticated():
        st.error("Please log in to take a quiz.")
        st.stop()
    
    user_info = session_manager.get_user_info()
    
    # Check if user is a student
    if user_info.get('role') != 'student':
        st.error("Only students can take quizzes.")
        st.stop()
    
    # Initialize session state for quiz
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = None
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = None
    
    # Quiz setup phase
    if not st.session_state.quiz_started:
        st.subheader("🎯 Quiz Setup")
        st.write("Configure your personalized quiz below:")
        
        with st.form("quiz_setup"):
            col1, col2 = st.columns(2)
            
            with col1:
                topic = st.text_input(
                    "Quiz Topic",
                    placeholder="e.g., Python Programming, Mathematics, History",
                    help="Enter the subject or topic you want to be quizzed on"
                )
                
                difficulty = st.selectbox(
                    "Difficulty Level",
                    ["easy", "medium", "hard"],
                    index=1,
                    help="Choose the difficulty level for your quiz"
                )
            
            with col2:
                num_questions = st.slider(
                    "Number of Questions",
                    min_value=3,
                    max_value=10,
                    value=5,
                    help="Select how many questions you want in your quiz"
                )
                
                time_limit = st.selectbox(
                    "Time Limit (minutes)",
                    [5, 10, 15, 20, 30],
                    index=2,
                    help="Choose time limit for the entire quiz"
                )
            
            submitted = st.form_submit_button("Generate Quiz", type="primary")
            
            if submitted:
                if not topic.strip():
                    st.error("Please enter a quiz topic.")
                else:
                    with st.spinner("Generating your personalized quiz..."):
                        # Generate quiz questions
                        questions = hf_service.generate_quiz_questions(
                            topic=topic.strip(),
                            difficulty=difficulty,
                            num_questions=num_questions
                        )
                        
                        if questions:
                            st.session_state.quiz_questions = questions
                            st.session_state.quiz_topic = topic.strip()
                            st.session_state.quiz_difficulty = difficulty
                            st.session_state.quiz_time_limit = time_limit * 60  # Convert to seconds
                            st.session_state.user_answers = {}
                            st.session_state.current_question = 0
                            st.session_state.quiz_started = True
                            st.session_state.quiz_start_time = time.time()
                            st.session_state.quiz_completed = False
                            st.success(f"Generated {len(questions)} questions on {topic}!")
                            st.rerun()
                        else:
                            st.error("Failed to generate quiz questions. Please try again.")
    
    # Quiz taking phase
    elif st.session_state.quiz_started and not st.session_state.quiz_completed:
        questions = st.session_state.quiz_questions
        current_q = st.session_state.current_question
        
        # Calculate time remaining
        elapsed_time = time.time() - st.session_state.quiz_start_time
        time_remaining = st.session_state.quiz_time_limit - elapsed_time
        
        # Time's up check
        if time_remaining <= 0:
            st.warning("⏰ Time's up! Submitting your quiz...")
            st.session_state.quiz_completed = True
            st.rerun()
        
        # Quiz header with progress
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"📚 {st.session_state.quiz_topic}")
            progress = (current_q + 1) / len(questions)
            st.progress(progress, f"Question {current_q + 1} of {len(questions)}")
        
        with col2:
            st.metric("Difficulty", st.session_state.quiz_difficulty.title())
        
        with col3:
            minutes_remaining = int(time_remaining // 60)
            seconds_remaining = int(time_remaining % 60)
            st.metric("Time Left", f"{minutes_remaining:02d}:{seconds_remaining:02d}")
        
        st.divider()
        
        # Display current question
        if current_q < len(questions):
            question = questions[current_q]
            
            st.subheader(f"Question {current_q + 1}")
            st.write(question['question'])
            
            # Display options
            options = question.get('options', {})
            if options:
                # Get previously selected answer
                prev_answer = st.session_state.user_answers.get(current_q)
                
                # Create radio button for options
                option_list = [f"{key}) {value}" for key, value in options.items()]
                selected_option = st.radio(
                    "Select your answer:",
                    option_list,
                    index=None if prev_answer is None else list(options.keys()).index(prev_answer),
                    key=f"question_{current_q}"
                )
                
                if selected_option:
                    # Extract the answer key (A, B, C, D)
                    answer_key = selected_option.split(')')[0]
                    st.session_state.user_answers[current_q] = answer_key
            
            # Navigation buttons
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                if current_q > 0:
                    if st.button("⬅️ Previous", use_container_width=True):
                        st.session_state.current_question = current_q - 1
                        st.rerun()
            
            with col2:
                if current_q < len(questions) - 1:
                    if st.button("Next ➡️", use_container_width=True):
                        st.session_state.current_question = current_q + 1
                        st.rerun()
            
            with col3:
                # Show progress summary
                answered = len(st.session_state.user_answers)
                if st.button(f"Progress ({answered}/{len(questions)})", use_container_width=True):
                    st.info(f"You have answered {answered} out of {len(questions)} questions.")
            
            with col4:
                if st.button("Submit Quiz", type="primary", use_container_width=True):
                    # Confirm submission
                    answered = len(st.session_state.user_answers)
                    if answered < len(questions):
                        st.warning(f"You have only answered {answered} out of {len(questions)} questions. Unanswered questions will be marked as incorrect.")
                    
                    if st.button("Confirm Submit", type="secondary"):
                        st.session_state.quiz_completed = True
                        st.rerun()
    
    # Quiz results phase
    elif st.session_state.quiz_completed:
        if st.session_state.quiz_results is None:
            # Calculate results
            with st.spinner("Calculating your results..."):
                results = quiz_parser.calculate_quiz_results(
                    st.session_state.quiz_questions,
                    st.session_state.user_answers,
                    st.session_state.quiz_start_time
                )
                
                # Store results in database
                quiz_data = {
                    'topic': st.session_state.quiz_topic,
                    'difficulty': st.session_state.quiz_difficulty,
                    'questions': st.session_state.quiz_questions,
                    'user_answers': st.session_state.user_answers,
                    'score': results['score'],
                    'total_questions': results['total_questions'],
                    'percentage': results['percentage'],
                    'time_taken': results['time_taken']
                }
                
                success = pinecone_service.store_quiz_result(user_info['user_id'], quiz_data)
                if success:
                    st.session_state.quiz_results = results
                else:
                    st.error("Failed to save quiz results.")
        
        # Display results
        if st.session_state.quiz_results:
            results = st.session_state.quiz_results
            
            st.balloons()
            st.title("🎉 Quiz Completed!")
            
            # Results summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Score", f"{results['score']}/{results['total_questions']}")
            
            with col2:
                percentage = results['percentage']
                color = "normal"
                if percentage >= 80:
                    color = "normal"
                elif percentage >= 60:
                    color = "normal"
                else:
                    color = "inverse"
                st.metric("Percentage", f"{percentage:.1f}%")
            
            with col3:
                st.metric("Time Taken", f"{results['time_taken']:.1f}s")
            
            with col4:
                if percentage >= 90:
                    grade = "A+"
                elif percentage >= 80:
                    grade = "A"
                elif percentage >= 70:
                    grade = "B"
                elif percentage >= 60:
                    grade = "C"
                else:
                    grade = "F"
                st.metric("Grade", grade)
            
            # Performance feedback
            st.divider()
            st.subheader("📊 Performance Analysis")
            
            if percentage >= 80:
                st.success("🎯 Excellent work! You have a strong understanding of this topic.")
            elif percentage >= 60:
                st.info("👍 Good job! You have a solid grasp of the material with room for improvement.")
            else:
                st.warning("📚 Keep studying! Consider reviewing the material and trying again.")
            
            # Detailed results
            if st.checkbox("Show detailed results"):
                st.subheader("📝 Question-by-Question Review")
                
                for i, question in enumerate(st.session_state.quiz_questions):
                    user_answer = st.session_state.user_answers.get(i, "Not answered")
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
                if st.button("Take Another Quiz", type="primary", use_container_width=True):
                    # Reset quiz state
                    for key in ['quiz_started', 'quiz_questions', 'current_question', 
                               'user_answers', 'quiz_start_time', 'quiz_completed', 'quiz_results']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            with col2:
                if st.button("View Quiz History", use_container_width=True):
                    st.switch_page("pages/3_Quiz_History.py")
            
            with col3:
                if st.button("Back to Dashboard", use_container_width=True):
                    st.switch_page("pages/1_Student_Dashboard.py")

if __name__ == "__main__":
    main()
