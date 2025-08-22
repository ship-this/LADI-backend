from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5,
            backColor=colors.lightgrey
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkblue
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Score style
        self.styles.add(ParagraphStyle(
            name='Score',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        ))
        
        # Category title style
        self.styles.add(ParagraphStyle(
            name='CategoryTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=16,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
    
    def generate_evaluation_report(self, evaluation_results: Dict[str, Any], 
                                 metadata: Dict[str, Any], output_path: str) -> str:
        """
        Generate a comprehensive PDF evaluation report
        Returns the path to the generated PDF file
        """
        try:
            logger.info(f"Generating PDF report with evaluation_results type: {type(evaluation_results)}")
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the story (content) for the PDF
            story = []
            
            # Add title page
            story.extend(self._create_title_page(metadata))
            story.append(PageBreak())
            
            # Add executive summary
            story.extend(self._create_executive_summary(evaluation_results))
            story.append(PageBreak())
            
            # Add detailed evaluation sections
            story.extend(self._create_detailed_evaluation(evaluation_results))
            
            # Build the PDF
            doc.build(story)
            
            logger.info(f"PDF report generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _create_title_page(self, metadata: Dict[str, Any]) -> List:
        """Create the title page"""
        story = []
        
        # Main title
        title = Paragraph("LADI Manuscript Evaluation Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 30))
        
        # Document information
        doc_info = [
            ["Document:", metadata.get('original_filename', 'Unknown')],
            ["File Type:", metadata.get('file_type', 'Unknown').upper()],
            ["Evaluation Date:", metadata.get('evaluation_date', 'Unknown')],
            ["Report ID:", metadata.get('evaluation_id', 'N/A')]
        ]
        
        doc_table = Table(doc_info, colWidths=[2*inch, 4*inch])
        doc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(doc_table)
        story.append(Spacer(1, 30))
        
        # Confidentiality notice
        notice = Paragraph(
            "This report contains confidential evaluation results. "
            "Please handle with appropriate discretion.",
            self.styles['CustomBodyText']
        )
        story.append(notice)
        
        return story
    
    def _create_executive_summary(self, evaluation_results: Dict[str, Any]) -> List:
        """Create the executive summary section"""
        story = []
        
        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Overall score
        overall_score = evaluation_results.get('overall_score', 0)
        score_text = f"Overall LADI Readiness Score: {overall_score}/100"
        score_para = Paragraph(score_text, self.styles['Score'])
        story.append(score_para)
        story.append(Spacer(1, 12))
        
        # Score interpretation
        if overall_score >= 80:
            readiness_level = "High Readiness"
            interpretation = "This manuscript demonstrates excellent quality and is well-positioned for publication consideration."
        elif overall_score >= 60:
            readiness_level = "Moderate Readiness"
            interpretation = "This manuscript shows good potential but requires some revisions before publication."
        else:
            readiness_level = "Needs Work"
            interpretation = "This manuscript requires significant revision and development before publication consideration."
        
        readiness_para = Paragraph(f"Readiness Level: {readiness_level}", self.styles['SubsectionHeader'])
        story.append(readiness_para)
        
        interpretation_para = Paragraph(interpretation, self.styles['CustomBodyText'])
        story.append(interpretation_para)
        story.append(Spacer(1, 12))
        
        # Category scores table
        categories = evaluation_results.get('categories', {})
        if categories:
            category_data = [["Category", "Score", "Status"]]
            
            category_names = {
                'line-editing': 'Line & Copy Editing',
                'plot': 'Plot Evaluation',
                'character': 'Character Evaluation',
                'flow': 'Book Flow Evaluation',
                'worldbuilding': 'Worldbuilding & Setting',
                'readiness': 'LADI Readiness Score'
            }
            
            for category_id, category_info in categories.items():
                score = category_info.get('score', 0)
                status = category_info.get('status', 'unknown')
                category_name = category_names.get(category_id, category_id.title())
                
                category_data.append([category_name, f"{score}/100", status.title()])
            
            category_table = Table(category_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(category_table)
        
        return story
    
    def _create_detailed_evaluation(self, evaluation_results: Dict[str, Any]) -> List:
        """Create detailed evaluation sections"""
        story = []
        
        # Section header
        header = Paragraph("Detailed Evaluation", self.styles['SectionHeader'])
        story.append(header)
        story.append(Spacer(1, 12))
        
        categories = evaluation_results.get('categories', {})
        category_names = {
            'line-editing': 'Line & Copy Editing',
            'plot': 'Plot Evaluation',
            'character': 'Character Evaluation',
            'flow': 'Book Flow Evaluation',
            'worldbuilding': 'Worldbuilding & Setting',
            'readiness': 'LADI Readiness Score'
        }
        
        for category_id, category_info in categories.items():
            category_name = category_names.get(category_id, category_id.title())
            
            # Category header
            cat_header = Paragraph(category_name, self.styles['CategoryTitle'])
            story.append(cat_header)
            
            # Score
            score = category_info.get('score', 0)
            score_text = f"Score: {score}/100"
            score_para = Paragraph(score_text, self.styles['Score'])
            story.append(score_para)
            
            # Summary
            summary = category_info.get('summary', 'No summary available.')
            summary_para = Paragraph(f"<b>Summary:</b> {summary}", self.styles['CustomBodyText'])
            story.append(summary_para)
            
            # Strengths
            strengths = category_info.get('strengths', [])
            if strengths:
                strengths_text = "<b>Strengths:</b><br/>" + "<br/>".join([f"• {s}" for s in strengths])
                strengths_para = Paragraph(strengths_text, self.styles['CustomBodyText'])
                story.append(strengths_para)
            
            # Areas for improvement
            improvements = category_info.get('areas_for_improvement', [])
            if improvements:
                improvements_text = "<b>Areas for Improvement:</b><br/>" + "<br/>".join([f"• {i}" for i in improvements])
                improvements_para = Paragraph(improvements_text, self.styles['CustomBodyText'])
                story.append(improvements_para)
            
            story.append(Spacer(1, 20))
        
        return story 