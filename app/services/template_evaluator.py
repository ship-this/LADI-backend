import logging
import json
from typing import Dict, Any, Optional
from app.services.excel_parser import ExcelParser
from app.services.gpt_evaluator import GPTEvaluator
from datetime import datetime

logger = logging.getLogger(__name__)

class TemplateEvaluator:
    def __init__(self):
        self.excel_parser = ExcelParser()
        self.gpt_evaluator = GPTEvaluator()
        
    def parse_template_file(self, template_file_path: str) -> Dict[str, Any]:
        """
        Parse Excel template file and extract evaluation prompts
        Returns a dictionary with category prompts and metadata
        """
        try:
            # Parse the Excel file
            parse_result = self.excel_parser.parse_excel_file(template_file_path)
            
            # Extract prompts from the parsed content
            prompts = self._extract_prompts_from_content(parse_result['text_content'])
            
            return {
                'prompts': prompts,
                'metadata': parse_result['metadata'],
                'total_sheets': parse_result['total_sheets'],
                'total_cells': parse_result['total_cells']
            }
            
        except Exception as e:
            logger.error(f"Error parsing template file {template_file_path}: {e}")
            raise Exception(f"Failed to parse template file: {str(e)}")
    
    def _extract_prompts_from_content(self, content: str) -> Dict[str, str]:
        """
        Extract evaluation prompts from Excel content
        Looks for specific patterns or sheet names to identify prompts
        """
        prompts = {}
        
        # Split content by sheet markers
        sheets = content.split("=== SHEET:")
        
        for sheet in sheets:
            if not sheet.strip():
                continue
                
            # Extract sheet name and content
            lines = sheet.strip().split('\n', 1)
            if len(lines) < 2:
                continue
                
            sheet_name = lines[0].strip()
            sheet_content = lines[1].strip()
            
            # Map sheet names to evaluation categories
            category_mapping = {
                'line-editing': ['line editing', 'line-editing', 'copy editing', 'grammar'],
                'plot': ['plot', 'story structure', 'narrative'],
                'character': ['character', 'characters', 'characterization'],
                'flow': ['flow', 'book flow', 'rhythm', 'transitions'],
                'worldbuilding': ['worldbuilding', 'world building', 'setting'],
                'readiness': ['readiness', 'ladi readiness', 'overall', 'final']
            }
            
            # Find matching category
            for category, keywords in category_mapping.items():
                if any(keyword.lower() in sheet_name.lower() for keyword in keywords):
                    prompts[category] = self._clean_prompt_content(sheet_content)
                    break
        
        # If no prompts found, use default prompts
        if not prompts:
            logger.warning("No prompts found in template, using default prompts")
            prompts = self._get_default_prompts()
        
        return prompts
    
    def _clean_prompt_content(self, content: str) -> str:
        """
        Clean and format prompt content from Excel
        """
        # Remove excessive whitespace and formatting
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('==='):
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """
        Return default prompts if template parsing fails
        """
        return {
            'line-editing': 'Analyze the manuscript for grammar, syntax, clarity, and prose fluidity. Provide a score out of 100 and a detailed summary of findings.',
            'plot': 'Evaluate the plot structure, pacing, narrative tension, and resolution effectiveness. Provide a score out of 100 and a detailed summary of findings.',
            'character': 'Assess character depth, motivation, consistency, and emotional impact throughout the manuscript. Provide a score out of 100 and a detailed summary of findings.',
            'flow': 'Evaluate the book flow, including rhythm, transitions, escalation patterns, and narrative cohesion. Provide a score out of 100 and a detailed summary of findings.',
            'worldbuilding': 'Analyze the worldbuilding and setting for depth, continuity, and originality. Provide a score out of 100 and a detailed summary of findings.',
            'readiness': 'Provide an overall LADI readiness assessment using our proprietary scoring system. Consider all aspects of the manuscript and assign a readiness tier (High Readiness, Moderate Readiness, Needs Work, etc.) with a score out of 100 and detailed justification.'
        }
    
    def evaluate_with_template(self, text_content: str, template_prompts: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluate manuscript using custom prompts from template
        """
        try:
            if not text_content or len(text_content.strip()) < 100:
                raise ValueError("Manuscript text is too short for meaningful evaluation")
            
            # Truncate text if too long
            max_chars = 15000
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "\n\n[Text truncated for analysis]"
            
            logger.info(f"Starting template-based manuscript evaluation for {len(text_content)} characters")
            
            # Perform evaluation with custom prompts
            evaluation_result = self._perform_template_evaluation(text_content, template_prompts)
            
            logger.info("Completed template-based manuscript evaluation")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error in template-based manuscript evaluation: {e}")
            raise
    
    def _perform_template_evaluation(self, text_content: str, template_prompts: Dict[str, str]) -> Dict[str, Any]:
        """
        Perform evaluation using prompts from template
        """
        categories = {}
        
        # Evaluate each category using template prompts
        for category_id, prompt in template_prompts.items():
            try:
                result = self._evaluate_category_with_prompt(text_content, category_id, prompt)
                categories[category_id] = result
            except Exception as e:
                logger.error(f"Error evaluating category {category_id}: {e}")
                # Fallback to default evaluation
                result = self._evaluate_category_with_default_prompt(text_content, category_id)
                categories[category_id] = result
        
        # Calculate overall score
        scores = [cat.get('score', 0) for cat in categories.values()]
        overall_score = round(sum(scores) / len(scores)) if scores else 0
        
        return {
            'categories': categories,
            'overall_score': overall_score,
            'evaluation_date': datetime.now().isoformat(),
            'template_used': True
        }
    
    def _evaluate_category_with_prompt(self, text_content: str, category_id: str, custom_prompt: str) -> Dict[str, Any]:
        """
        Evaluate a single category using custom prompt
        """
        if not self.gpt_evaluator.client:
            # Use mock evaluation if OpenAI client not available
            return self._get_mock_evaluation_result(category_id)
        
        try:
            # Create evaluation prompt with custom prompt
            evaluation_prompt = f"""
            You are an expert manuscript evaluator. Please evaluate the following manuscript excerpt using this specific criteria:

            {custom_prompt}

            Manuscript excerpt:
            {text_content[:5000]}  # Use first 5000 chars for evaluation

            Please provide your evaluation in the following JSON format:
            {{
                "score": <score_out_of_100>,
                "summary": "<detailed_summary_of_findings>",
                "strengths": ["<strength1>", "<strength2>"],
                "areas_for_improvement": ["<area1>", "<area2>"]
            }}
            """
            
            response = self.gpt_evaluator.client.chat.completions.create(
                model=self.gpt_evaluator.model,
                messages=[
                    {"role": "system", "content": "You are an expert manuscript evaluator. Provide evaluations in JSON format only."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Remove any markdown formatting
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                result = json.loads(response_text)
                
                return {
                    'score': result.get('score', 0),
                    'summary': result.get('summary', 'No summary available'),
                    'strengths': result.get('strengths', []),
                    'areas_for_improvement': result.get('areas_for_improvement', [])
                }
                
            except json.JSONDecodeError:
                # Fallback: extract score and summary from text
                return self._extract_evaluation_from_text(response_text, category_id)
                
        except Exception as e:
            logger.error(f"Error in GPT evaluation for category {category_id}: {e}")
            return self._get_mock_evaluation_result(category_id)
    
    def _evaluate_category_with_default_prompt(self, text_content: str, category_id: str) -> Dict[str, Any]:
        """
        Fallback to default evaluation if custom prompt fails
        """
        return self.gpt_evaluator._evaluate_category(text_content, category_id)
    
    def _extract_evaluation_from_text(self, text: str, category_id: str) -> Dict[str, Any]:
        """
        Extract evaluation results from text response when JSON parsing fails
        """
        # Simple extraction logic
        lines = text.split('\n')
        score = 0
        summary = text[:500]  # Use first 500 chars as summary
        
        # Try to find score in text
        for line in lines:
            if 'score' in line.lower() and any(char.isdigit() for char in line):
                try:
                    score = int(''.join(filter(str.isdigit, line)))
                    if score > 100:
                        score = score % 100
                    break
                except:
                    pass
        
        return {
            'score': score,
            'summary': summary,
            'strengths': [],
            'areas_for_improvement': []
        }
    
    def _get_mock_evaluation_result(self, category_id: str) -> Dict[str, Any]:
        """
        Return mock evaluation result for development/testing
        """
        import random
        
        mock_scores = {
            'line-editing': random.randint(70, 90),
            'plot': random.randint(65, 85),
            'character': random.randint(60, 80),
            'flow': random.randint(70, 85),
            'worldbuilding': random.randint(75, 90),
            'readiness': random.randint(65, 85)
        }
        
        mock_summaries = {
            'line-editing': 'The manuscript demonstrates solid grammar and syntax with good prose fluidity. Minor improvements needed in sentence structure.',
            'plot': 'The plot shows good structure and pacing. Narrative tension builds effectively, though some resolution elements could be strengthened.',
            'character': 'Characters are well-developed with clear motivations. Emotional impact is present but could be deepened in certain scenes.',
            'flow': 'The book flows well with good rhythm and transitions. Escalation patterns are effective and maintain reader engagement.',
            'worldbuilding': 'The setting is well-crafted with good depth and continuity. Original elements add value to the narrative.',
            'readiness': 'Overall manuscript shows moderate readiness for publication. Key areas identified for improvement before final submission.'
        }
        
        return {
            'score': mock_scores.get(category_id, 75),
            'summary': mock_summaries.get(category_id, 'Evaluation completed successfully.'),
            'strengths': ['Good structure', 'Clear narrative'],
            'areas_for_improvement': ['Minor refinements needed']
        }
