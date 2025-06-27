import time
from typing import Dict, List, Any

class QuizParser:
    """Utility class for parsing and calculating quiz results"""
    
    def __init__(self):
        pass
    
    def calculate_quiz_results(self, questions: List[Dict[str, Any]], user_answers: Dict[int, str], start_time: float) -> Dict[str, Any]:
        """Calculate quiz results based on questions and user answers"""
        try:
            total_questions = len(questions)
            correct_answers = 0
            time_taken = time.time() - start_time
            
            # Calculate correct answers
            for i, question in enumerate(questions):
                user_answer = user_answers.get(i)
                correct_answer = question.get('correct_answer')
                
                if user_answer and correct_answer and user_answer.upper() == correct_answer.upper():
                    correct_answers += 1
            
            # Calculate percentage
            percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            results = {
                'score': correct_answers,
                'total_questions': total_questions,
                'percentage': round(percentage, 2),
                'time_taken': round(time_taken, 2),
                'questions_breakdown': self._get_questions_breakdown(questions, user_answers)
            }
            
            return results
            
        except Exception as e:
            # Return default results on error
            return {
                'score': 0,
                'total_questions': len(questions) if questions else 0,
                'percentage': 0.0,
                'time_taken': 0.0,
                'questions_breakdown': []
            }
    
    def _get_questions_breakdown(self, questions: List[Dict[str, Any]], user_answers: Dict[int, str]) -> List[Dict[str, Any]]:
        """Get detailed breakdown of each question and answer"""
        breakdown = []
        
        for i, question in enumerate(questions):
            user_answer = user_answers.get(i, "Not answered")
            correct_answer = question.get('correct_answer', 'Unknown')
            is_correct = user_answer.upper() == correct_answer.upper() if user_answer != "Not answered" else False
            
            breakdown.append({
                'question_number': i + 1,
                'question': question.get('question', ''),
                'options': question.get('options', {}),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', '')
            })
        
        return breakdown
    
    def get_performance_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 97:
            return "A+"
        elif percentage >= 93:
            return "A"
        elif percentage >= 90:
            return "A-"
        elif percentage >= 87:
            return "B+"
        elif percentage >= 83:
            return "B"
        elif percentage >= 80:
            return "B-"
        elif percentage >= 77:
            return "C+"
        elif percentage >= 73:
            return "C"
        elif percentage >= 70:
            return "C-"
        elif percentage >= 67:
            return "D+"
        elif percentage >= 65:
            return "D"
        else:
            return "F"
    
    def get_performance_feedback(self, percentage: float) -> Dict[str, str]:
        """Get performance feedback based on score"""
        if percentage >= 90:
            return {
                'level': 'Excellent',
                'message': 'Outstanding performance! You have mastered this topic.',
                'color': 'success'
            }
        elif percentage >= 80:
            return {
                'level': 'Good',
                'message': 'Great job! You have a solid understanding of the material.',
                'color': 'success'
            }
        elif percentage >= 70:
            return {
                'level': 'Satisfactory',
                'message': 'Good work! There\'s room for improvement in some areas.',
                'color': 'info'
            }
        elif percentage >= 60:
            return {
                'level': 'Needs Improvement',
                'message': 'You\'re on the right track, but consider reviewing the material.',
                'color': 'warning'
            }
        else:
            return {
                'level': 'Needs Significant Improvement',
                'message': 'Please review the material thoroughly and consider additional practice.',
                'color': 'error'
            }
    
    def analyze_topic_performance(self, quiz_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance across different topics"""
        if not quiz_history:
            return {}
        
        topic_stats = {}
        
        for quiz in quiz_history:
            topic = quiz.get('topic', 'Unknown')
            percentage = quiz.get('percentage', 0)
            
            if topic not in topic_stats:
                topic_stats[topic] = {
                    'total_quizzes': 0,
                    'total_score': 0,
                    'best_score': 0,
                    'worst_score': 100,
                    'scores': []
                }
            
            topic_stats[topic]['total_quizzes'] += 1
            topic_stats[topic]['total_score'] += percentage
            topic_stats[topic]['best_score'] = max(topic_stats[topic]['best_score'], percentage)
            topic_stats[topic]['worst_score'] = min(topic_stats[topic]['worst_score'], percentage)
            topic_stats[topic]['scores'].append(percentage)
        
        # Calculate averages and trends
        for topic, stats in topic_stats.items():
            stats['average_score'] = stats['total_score'] / stats['total_quizzes']
            
            # Calculate trend (improvement over time)
            scores = stats['scores']
            if len(scores) > 1:
                recent_avg = sum(scores[-3:]) / len(scores[-3:])  # Last 3 quizzes
                early_avg = sum(scores[:3]) / len(scores[:3])    # First 3 quizzes
                stats['trend'] = recent_avg - early_avg
            else:
                stats['trend'] = 0
        
        return topic_stats
    
    def get_difficulty_analysis(self, quiz_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance across different difficulty levels"""
        if not quiz_history:
            return {}
        
        difficulty_stats = {}
        
        for quiz in quiz_history:
            difficulty = quiz.get('difficulty', 'medium')
            percentage = quiz.get('percentage', 0)
            
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {
                    'total_quizzes': 0,
                    'total_score': 0,
                    'scores': []
                }
            
            difficulty_stats[difficulty]['total_quizzes'] += 1
            difficulty_stats[difficulty]['total_score'] += percentage
            difficulty_stats[difficulty]['scores'].append(percentage)
        
        # Calculate averages
        for difficulty, stats in difficulty_stats.items():
            stats['average_score'] = stats['total_score'] / stats['total_quizzes']
            stats['success_rate'] = len([s for s in stats['scores'] if s >= 70]) / len(stats['scores']) * 100
        
        return difficulty_stats
    
    def generate_study_recommendations(self, topic_performance: Dict[str, Any], difficulty_analysis: Dict[str, Any]) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        # Topic-based recommendations
        if topic_performance:
            # Find weakest topics
            sorted_topics = sorted(topic_performance.items(), key=lambda x: x[1]['average_score'])
            
            if sorted_topics:
                weakest_topic = sorted_topics[0]
                if weakest_topic[1]['average_score'] < 70:
                    recommendations.append(f"Focus on improving your understanding of {weakest_topic[0]} - your average score is {weakest_topic[1]['average_score']:.1f}%")
                
                # Find topics with negative trends
                declining_topics = [topic for topic, stats in topic_performance.items() if stats['trend'] < -10]
                if declining_topics:
                    recommendations.append(f"Review {', '.join(declining_topics)} as your performance seems to be declining in these areas")
        
        # Difficulty-based recommendations
        if difficulty_analysis:
            for difficulty, stats in difficulty_analysis.items():
                if stats['average_score'] < 60:
                    recommendations.append(f"Consider practicing more {difficulty} level questions - your success rate is {stats['success_rate']:.1f}%")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Keep up the great work! Continue practicing regularly to maintain your performance.")
        
        return recommendations[:3]  # Return top 3 recommendations
