import os
import requests
import json
import streamlit as st
from typing import List, Dict, Any

class HuggingFaceService:
    """Handle Hugging Face API interactions for quiz generation"""
    
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "your_huggingface_api_key")
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        # Using a capable text generation model
        self.model_id = "microsoft/DialoGPT-large"
    
    def generate_quiz_questions(self, topic: str, difficulty: str = "medium", num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate quiz questions using Hugging Face API"""
        try:
            # Create a detailed prompt for quiz generation
            prompt = self._create_quiz_prompt(topic, difficulty, num_questions)
            
            # Make API request
            response = self._make_api_request(prompt)
            
            if response:
                # Parse the response into structured quiz questions
                questions = self._parse_quiz_response(response, num_questions)
                return questions
            else:
                return self._generate_fallback_quiz(topic, num_questions)
                
        except Exception as e:
            st.error(f"Failed to generate quiz questions: {str(e)}")
            return self._generate_fallback_quiz(topic, num_questions)
    
    def _create_quiz_prompt(self, topic: str, difficulty: str, num_questions: int) -> str:
        """Create a structured prompt for quiz generation"""
        prompt = f"""Generate {num_questions} multiple choice questions about {topic} at {difficulty} difficulty level.

Format each question exactly as follows:
Question: [Question text]
A) [Option A]
B) [Option B]  
C) [Option C]
D) [Option D]
Correct Answer: [A, B, C, or D]
Explanation: [Brief explanation of the correct answer]

Topic: {topic}
Difficulty: {difficulty}
Number of questions: {num_questions}

Questions:
"""
        return prompt
    
    def _make_api_request(self, prompt: str) -> str:
        """Make API request to Hugging Face"""
        try:
            # Try text generation model first
            url = f"{self.base_url}/gpt2"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 1000,
                    "temperature": 0.7,
                    "do_sample": True,
                    "num_return_sequences": 1
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                else:
                    return result.get('generated_text', '')
            else:
                st.warning(f"API request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"API request failed: {str(e)}")
            return None
    
    def _parse_quiz_response(self, response: str, num_questions: int) -> List[Dict[str, Any]]:
        """Parse the API response into structured quiz questions"""
        try:
            questions = []
            lines = response.split('\n')
            current_question = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Question:'):
                    if current_question:
                        questions.append(current_question)
                    current_question = {
                        'question': line.replace('Question:', '').strip(),
                        'options': {},
                        'correct_answer': '',
                        'explanation': ''
                    }
                elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                    option_key = line[0]
                    option_text = line[2:].strip()
                    if 'options' in current_question:
                        current_question['options'][option_key] = option_text
                elif line.startswith('Correct Answer:'):
                    current_question['correct_answer'] = line.replace('Correct Answer:', '').strip()
                elif line.startswith('Explanation:'):
                    current_question['explanation'] = line.replace('Explanation:', '').strip()
            
            # Add the last question
            if current_question and current_question.get('question'):
                questions.append(current_question)
            
            # If parsing failed, return fallback
            if len(questions) == 0:
                return self._generate_fallback_quiz(response.split('\n')[0] if response else "General Knowledge", num_questions)
            
            return questions[:num_questions]
            
        except Exception as e:
            st.error(f"Failed to parse quiz response: {str(e)}")
            return self._generate_fallback_quiz("General Knowledge", num_questions)
    
    def _generate_fallback_quiz(self, topic: str, num_questions: int) -> List[Dict[str, Any]]:
        """Generate fallback quiz questions when API fails"""
        fallback_questions = [
            {
                'question': f"What is an important concept in {topic}?",
                'options': {
                    'A': f"Basic principle of {topic}",
                    'B': f"Advanced theory in {topic}",
                    'C': f"Common misconception about {topic}",
                    'D': f"Unrelated concept"
                },
                'correct_answer': 'A',
                'explanation': f"The basic principles form the foundation of understanding {topic}."
            },
            {
                'question': f"Which of the following best describes {topic}?",
                'options': {
                    'A': f"A complex field of study",
                    'B': f"An area requiring practical application",
                    'C': f"A theoretical framework",
                    'D': f"All of the above"
                },
                'correct_answer': 'D',
                'explanation': f"{topic} encompasses theoretical knowledge and practical applications."
            },
            {
                'question': f"What is the primary goal when studying {topic}?",
                'options': {
                    'A': f"To memorize facts about {topic}",
                    'B': f"To understand core concepts and applications",
                    'C': f"To pass examinations only",
                    'D': f"To impress others with knowledge"
                },
                'correct_answer': 'B',
                'explanation': f"Understanding core concepts and their applications is key to mastering {topic}."
            },
            {
                'question': f"How can knowledge of {topic} be applied in real-world scenarios?",
                'options': {
                    'A': f"Through theoretical analysis only",
                    'B': f"By solving practical problems",
                    'C': f"In academic discussions exclusively",
                    'D': f"It has no practical applications"
                },
                'correct_answer': 'B',
                'explanation': f"Knowledge of {topic} is most valuable when applied to solve real-world problems."
            },
            {
                'question': f"What approach is most effective for learning {topic}?",
                'options': {
                    'A': f"Passive reading only",
                    'B': f"Active practice and application",
                    'C': f"Memorization without understanding",
                    'D': f"Avoiding challenging concepts"
                },
                'correct_answer': 'B',
                'explanation': f"Active practice and application reinforce understanding and retention of {topic}."
            }
        ]
        
        return fallback_questions[:num_questions]
    
    def evaluate_answer(self, question: Dict[str, Any], user_answer: str) -> Dict[str, Any]:
        """Evaluate user's answer and provide feedback"""
        try:
            is_correct = user_answer.upper() == question['correct_answer'].upper()
            
            result = {
                'is_correct': is_correct,
                'correct_answer': question['correct_answer'],
                'explanation': question.get('explanation', ''),
                'user_answer': user_answer,
                'score': 1 if is_correct else 0
            }
            
            return result
            
        except Exception as e:
            st.error(f"Failed to evaluate answer: {str(e)}")
            return {
                'is_correct': False,
                'correct_answer': question.get('correct_answer', ''),
                'explanation': question.get('explanation', ''),
                'user_answer': user_answer,
                'score': 0
            }
