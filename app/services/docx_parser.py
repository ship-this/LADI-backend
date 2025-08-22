import os
import logging
import mammoth
from typing import Dict, Any
from app.config import Config

logger = logging.getLogger(__name__)

class DOCXParser:
    def __init__(self):
        self.supported_extensions = ['.docx']
    
    def parse_docx_file(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX file and extract text content and metadata"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Starting DOCX parsing for file: {file_path}")
            
            # Extract text content
            with open(file_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                text_content = result.value
                
                # Get warnings if any
                if result.messages:
                    logger.warning(f"DOCX parsing warnings: {result.messages}")
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            
            # Estimate word count and page count
            word_count = len(text_content.split())
            estimated_pages = max(1, word_count // 250)  # Rough estimate: 250 words per page
            
            metadata = {
                'file_size': file_size,
                'word_count': word_count,
                'total_pages': estimated_pages,
                'file_type': 'docx',
                'parsing_warnings': result.messages if result.messages else []
            }
            
            logger.info(f"DOCX parsing completed. Extracted {len(text_content)} characters, {word_count} words")
            
            return {
                'text_content': text_content,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing DOCX file {file_path}: {e}")
            raise Exception(f"DOCX parsing failed: {str(e)}")
    
    def extract_text_with_formatting(self, file_path: str) -> Dict[str, Any]:
        """Extract text with HTML formatting preserved"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Starting DOCX parsing with formatting for file: {file_path}")
            
            # Extract text with HTML formatting
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
                
                # Get warnings if any
                if result.messages:
                    logger.warning(f"DOCX parsing warnings: {result.messages}")
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            
            # Extract plain text from HTML for word count
            import re
            plain_text = re.sub(r'<[^>]+>', '', html_content)
            word_count = len(plain_text.split())
            estimated_pages = max(1, word_count // 250)
            
            metadata = {
                'file_size': file_size,
                'word_count': word_count,
                'total_pages': estimated_pages,
                'file_type': 'docx',
                'parsing_warnings': result.messages if result.messages else []
            }
            
            logger.info(f"DOCX parsing with formatting completed. Extracted {len(html_content)} characters")
            
            return {
                'html_content': html_content,
                'text_content': plain_text,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing DOCX file with formatting {file_path}: {e}")
            raise Exception(f"DOCX parsing with formatting failed: {str(e)}")
    
    def extract_images(self, file_path: str, output_dir: str = None) -> Dict[str, Any]:
        """Extract images from DOCX file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logger.info(f"Starting image extraction from DOCX file: {file_path}")
            
            # Extract images
            with open(file_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                
                # Note: mammoth doesn't directly support image extraction
                # This would require additional libraries like python-docx
                # For now, we'll return a placeholder
                image_info = {
                    'images_found': 0,
                    'image_files': [],
                    'message': 'Image extraction not implemented in current version'
                }
            
            logger.info("DOCX image extraction completed")
            
            return image_info
            
        except Exception as e:
            logger.error(f"Error extracting images from DOCX file {file_path}: {e}")
            raise Exception(f"DOCX image extraction failed: {str(e)}")
    
    def validate_docx_file(self, file_path: str) -> bool:
        """Validate if file is a valid DOCX file"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Check file extension
            if not file_path.lower().endswith('.docx'):
                return False
            
            # Try to open and parse the file
            with open(file_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                
                # If we can extract text, the file is valid
                return len(result.value) > 0
                
        except Exception as e:
            logger.error(f"Error validating DOCX file {file_path}: {e}")
            return False
