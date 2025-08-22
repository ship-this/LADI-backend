import PyPDF2
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PDFParser:
    """Service for parsing PDF files and extracting text content"""
    
    def __init__(self):
        self.supported_extensions = {'.pdf'}
    
    def parse_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PDF file and extract text content and metadata
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing text_content and metadata
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            
            # Open and read PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = ""
                total_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
                        logger.info(f"Extracted text from page {page_num + 1}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                
                # Get document metadata
                metadata = pdf_reader.metadata
                title = metadata.get('/Title', 'Unknown Title') if metadata else 'Unknown Title'
                author = metadata.get('/Author', 'Unknown Author') if metadata else 'Unknown Author'
                
                # Calculate text statistics
                word_count = len(text_content.split()) if text_content else 0
                char_count = len(text_content) if text_content else 0
                
                logger.info(f"PDF parsing completed: {total_pages} pages, {word_count} words, {char_count} characters")
                
                return {
                    'text_content': text_content.strip(),
                    'metadata': {
                        'file_size': file_size,
                        'total_pages': total_pages,
                        'word_count': word_count,
                        'char_count': char_count,
                        'title': title,
                        'author': author,
                        'file_type': 'pdf',
                        'original_filename': os.path.basename(file_path)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {e}")
            raise Exception(f"Failed to parse PDF file: {str(e)}")
    
    def validate_pdf_content(self, text_content: str, min_words: int = 100) -> bool:
        """
        Validate that the extracted text has sufficient content for evaluation
        
        Args:
            text_content: Extracted text from PDF
            min_words: Minimum number of words required
            
        Returns:
            True if content is sufficient, False otherwise
        """
        if not text_content or not text_content.strip():
            return False
        
        word_count = len(text_content.split())
        return word_count >= min_words
