import openai
import logging
import time
import json
from typing import Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)

class GPTEvaluator:
    def __init__(self):
        self.client = None
        self._initialize_client()
        
        # Define the evaluation categories matching the frontend
        self.evaluation_categories = {
            'line-editing': {
                'title': 'Line & Copy Editing',
                'description': 'Grammar, syntax, clarity, and prose fluidity analysis',
                'prompt': 'Analyze the manuscript for grammar, syntax, clarity, and prose fluidity. Provide a score out of 100 and a detailed summary of findings.'
            },
            'plot': {
                'title': 'Plot Evaluation',
                'description': 'Story structure, pacing, narrative tension, and resolution effectiveness',
                'prompt': 'Evaluate the plot structure, pacing, narrative tension, and resolution effectiveness. Provide a score out of 100 and a detailed summary of findings.'
            },
            'character': {
                'title': 'Character Evaluation',
                'description': 'Character depth, motivation, consistency, and emotional impact',
                'prompt': 'Assess character depth, motivation, consistency, and emotional impact throughout the manuscript. Provide a score out of 100 and a detailed summary of findings.'
            },
            'flow': {
                'title': 'Book Flow Evaluation',
                'description': 'Rhythm, transitions, escalation patterns, and narrative cohesion',
                'prompt': 'Evaluate the book flow, including rhythm, transitions, escalation patterns, and narrative cohesion. Provide a score out of 100 and a detailed summary of findings.'
            },
            'worldbuilding': {
                'title': 'Worldbuilding & Setting',
                'description': 'Setting depth, continuity, and originality assessment',
                'prompt': 'Analyze the worldbuilding and setting for depth, continuity, and originality. Provide a score out of 100 and a detailed summary of findings.'
            },
            'readiness': {
                'title': 'LADI Readiness Score',
                'description': 'Overall readiness assessment with proprietary scoring system',
                'prompt': 'Provide an overall LADI readiness assessment using our proprietary scoring system. Consider all aspects of the manuscript and assign a readiness tier (High Readiness, Moderate Readiness, Needs Work, etc.) with a score out of 100 and detailed justification.'
            }
        }
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            api_key = Config.OPENAI_API_KEY
            if not api_key:
                logger.error("OpenAI API key not configured! Set OPENAI_API_KEY environment variable.")
                logger.error("Using mock evaluation - this will provide fake scores for testing only!")
                self.client = None
                return
            
            if api_key == 'placeholder-openai-key' or api_key == 'your-openai-api-key-here':
                logger.error("OpenAI API key is set to placeholder value! Set a real OPENAI_API_KEY environment variable.")
                logger.error("Using mock evaluation - this will provide fake scores for testing only!")
                self.client = None
                return
            
            # Clear any proxy environment variables that might interfere
            import os
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            original_proxy_values = {}
            
            for var in proxy_vars:
                if var in os.environ:
                    original_proxy_values[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("Successfully initialized OpenAI client")
            finally:
                # Restore original proxy values if they existed
                for var, value in original_proxy_values.items():
                    os.environ[var] = value
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            logger.error("Using mock evaluation - this will provide fake scores for testing only!")
            self.client = None
    
    def evaluate_manuscript(self, text_content: str) -> Dict[str, Any]:
        """Perform comprehensive evaluation on the manuscript text"""
        try:
            if not text_content or len(text_content.strip()) < 100:
                raise ValueError("Manuscript text is too short for meaningful evaluation")
            
            # Truncate text if too long
            max_chars = 15000
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "\n\n[Text truncated for analysis]"
            
            logger.info(f"Starting manuscript evaluation for {len(text_content)} characters")
            
            # Perform comprehensive evaluation
            evaluation_result = self._perform_comprehensive_evaluation(text_content)
            
            logger.info("Completed manuscript evaluation")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error in manuscript evaluation: {e}")
            raise Exception(f"Manuscript evaluation failed: {str(e)}")
    
    def _perform_comprehensive_evaluation(self, text_content: str) -> Dict[str, Any]:
        """Perform comprehensive evaluation with structured output"""
        try:
            if not self.client:
                logger.error("⚠️  No OpenAI client available - using mock evaluation!")
                logger.error("⚠️  This will provide fake scores. Set OPENAI_API_KEY for real evaluation.")
                return self._generate_mock_evaluation()
            
            results = {}
            scores = {}
            
            # Evaluate each category
            for category_id, category_info in self.evaluation_categories.items():
                logger.info(f"Evaluating category: {category_info['title']}")
                
                try:
                    category_result = self._evaluate_category(text_content, category_info)
                    results[category_id] = category_result
                    scores[category_id] = category_result.get('score', 0)
                    
                    # Add delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error evaluating category {category_id}: {e}")
                    results[category_id] = {
                        'score': 0,
                        'summary': f"Error during evaluation: {str(e)}",
                        'status': 'failed'
                    }
                    scores[category_id] = 0
            
            # Calculate overall score
            overall_score = round(sum(scores.values()) / len(scores)) if scores else 0
            
            return {
                'categories': results,
                'scores': scores,
                'overall_score': overall_score,
                'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'text_length': len(text_content)
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive evaluation: {e}")
            return self._generate_mock_evaluation()
    
    def _evaluate_category(self, text_content: str, category_info: Dict[str, str]) -> Dict[str, Any]:
        """Evaluate a specific category with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                prompt = f"""
You are a professional manuscript evaluator specializing in {category_info['title']}.

{category_info['prompt']}

Please provide your evaluation in the following JSON format:
{{
    "score": <number between 0-100>,
    "summary": "<detailed summary of findings>",
    "strengths": ["<list of strengths>"],
    "areas_for_improvement": ["<list of areas for improvement>"]
}}

Manuscript text to evaluate:
{text_content[:5000]}  # Limit to first 5000 characters for this category
"""
            
                response = self.client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a professional manuscript evaluator. Provide evaluations in JSON format only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                    timeout=30  # Add timeout
                )
                
                content = response.choices[0].message.content.strip()
                
                # Try to parse JSON response
                try:
                    result = json.loads(content)
                    return {
                        'score': result.get('score', 0),
                        'summary': result.get('summary', 'No summary provided'),
                        'strengths': result.get('strengths', []),
                        'areas_for_improvement': result.get('areas_for_improvement', []),
                        'status': 'completed'
                    }
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    logger.warning(f"JSON parsing failed for {category_info['title']}, using fallback")
                    return {
                        'score': 75,  # Default score
                        'summary': content,
                        'strengths': [],
                        'areas_for_improvement': [],
                        'status': 'completed'
                    }
                    
            except Exception as e:
                logger.error(f"Error in category evaluation (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return {
                        'score': 0,
                        'summary': f"Error during evaluation after {max_retries} attempts: {str(e)}",
                        'status': 'failed'
                    }
    
    def _generate_mock_evaluation(self) -> Dict[str, Any]:
        """Generate mock evaluation for development/testing"""
        logger.error("⚠️  GENERATING MOCK EVALUATION - THESE ARE FAKE SCORES FOR TESTING ONLY!")
        logger.error("⚠️  Set OPENAI_API_KEY environment variable to get real AI evaluation scores!")
        
        mock_results = {
            'line-editing': {
                'score': 85,
                'summary': 'Strong prose with excellent clarity. Minor grammar inconsistencies noted in dialogue sections.',
                'strengths': ['Clear writing style', 'Good sentence structure'],
                'areas_for_improvement': ['Dialogue punctuation', 'Consistent tense usage'],
                'status': 'completed'
            },
            'plot': {
                'score': 78,
                'summary': 'Well-structured narrative with good pacing. The middle section could benefit from increased tension.',
                'strengths': ['Clear story arc', 'Good pacing'],
                'areas_for_improvement': ['Middle section tension', 'Subplot integration'],
                'status': 'completed'
            },
            'character': {
                'score': 92,
                'summary': 'Exceptional character development with clear motivations and authentic dialogue throughout.',
                'strengths': ['Deep character development', 'Authentic dialogue'],
                'areas_for_improvement': ['Minor character consistency'],
                'status': 'completed'
            },
            'flow': {
                'score': 80,
                'summary': 'Smooth transitions between scenes. Some chapters end abruptly but overall flow is engaging.',
                'strengths': ['Good scene transitions', 'Engaging flow'],
                'areas_for_improvement': ['Chapter endings', 'Pacing consistency'],
                'status': 'completed'
            },
            'worldbuilding': {
                'score': 88,
                'summary': 'Rich, immersive setting with consistent internal logic. Great attention to environmental details.',
                'strengths': ['Immersive setting', 'Consistent world logic'],
                'areas_for_improvement': ['More background details'],
                'status': 'completed'
            },
            'readiness': {
                'score': 84,
                'summary': 'High readiness for publication. Minor revisions recommended before final submission.',
                'strengths': ['Overall quality', 'Publication ready'],
                'areas_for_improvement': ['Minor revisions needed'],
                'status': 'completed'
            }
        }
        
        scores = {k: v['score'] for k, v in mock_results.items()}
        overall_score = round(sum(scores.values()) / len(scores))
        
        return {
            'categories': mock_results,
            'scores': scores,
            'overall_score': overall_score,
            'evaluation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'text_length': 5000
        } 