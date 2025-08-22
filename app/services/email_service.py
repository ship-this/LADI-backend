import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.smtp_username = Config.MAIL_USERNAME
        self.smtp_password = Config.MAIL_PASSWORD
        self.use_tls = Config.MAIL_USE_TLS
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("Email credentials not configured, skipping email send")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_password_reset_email(self, email, reset_token):
        """Send password reset email"""
        subject = "LADI - Password Reset Request"
        
        # Create reset URL (frontend URL)
        reset_url = f"{Config.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>LADI Password Reset</h2>
            <p>Hello,</p>
            <p>You have requested to reset your password for your LADI account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>Best regards,<br>LADI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        LADI Password Reset
        
        Hello,
        
        You have requested to reset your password for your LADI account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        LADI Team
        """
        
        return self.send_email(email, subject, html_content, text_content)
    
    def send_welcome_email(self, email, first_name):
        """Send welcome email to new users"""
        subject = "Welcome to LADI!"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to LADI!</h2>
            <p>Hello {first_name},</p>
            <p>Welcome to LADI (Literary Analysis and Development Index)!</p>
            <p>Your account has been successfully created. You can now:</p>
            <ul>
                <li>Upload your manuscripts for evaluation</li>
                <li>View detailed analysis reports</li>
                <li>Track your evaluation history</li>
                <li>Access professional manuscript insights</li>
            </ul>
            <p>Get started by uploading your first manuscript!</p>
            <p>Best regards,<br>LADI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to LADI!
        
        Hello {first_name},
        
        Welcome to LADI (Literary Analysis and Development Index)!
        
        Your account has been successfully created. You can now:
        - Upload your manuscripts for evaluation
        - View detailed analysis reports
        - Track your evaluation history
        - Access professional manuscript insights
        
        Get started by uploading your first manuscript!
        
        Best regards,
        LADI Team
        """
        
        return self.send_email(email, subject, html_content, text_content)
    
    def send_evaluation_completed_email(self, email, first_name, evaluation_id, filename):
        """Send notification when evaluation is completed"""
        subject = "LADI - Your Manuscript Evaluation is Ready!"
        
        # Create download URL (frontend URL)
        download_url = f"{Config.FRONTEND_URL}/evaluations/{evaluation_id}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Your Manuscript Evaluation is Ready!</h2>
            <p>Hello {first_name},</p>
            <p>Great news! Your manuscript evaluation for "{filename}" has been completed.</p>
            <p>You can now view and download your detailed evaluation report.</p>
            <p><a href="{download_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Report</a></p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p>{download_url}</p>
            <p>Your report includes comprehensive analysis across six key dimensions:</p>
            <ul>
                <li>Line and Copy Editing</li>
                <li>Plot Evaluation</li>
                <li>Character Evaluation</li>
                <li>Book Flow Evaluation</li>
                <li>Worldbuilding & Setting</li>
                <li>LADI Readiness Score</li>
            </ul>
            <p>Best regards,<br>LADI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Your Manuscript Evaluation is Ready!
        
        Hello {first_name},
        
        Great news! Your manuscript evaluation for "{filename}" has been completed.
        
        You can now view and download your detailed evaluation report at:
        {download_url}
        
        Your report includes comprehensive analysis across six key dimensions:
        - Line and Copy Editing
        - Plot Evaluation
        - Character Evaluation
        - Book Flow Evaluation
        - Worldbuilding & Setting
        - LADI Readiness Score
        
        Best regards,
        LADI Team
        """
        
        return self.send_email(email, subject, html_content, text_content)
