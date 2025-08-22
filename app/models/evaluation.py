from .user import db
from datetime import datetime
import enum

class EvaluationStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EvaluationMethod(enum.Enum):
    BASIC = "basic"
    CUSTOM = "custom"
    TEMPLATE = "template"

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    original_file_s3_key = db.Column(db.String(500), nullable=False)
    report_file_s3_key = db.Column(db.String(500), nullable=True)
    download_url = db.Column(db.String(1000), nullable=True)
    status = db.Column(db.Enum(EvaluationStatus), default=EvaluationStatus.PENDING, nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    total_sheets = db.Column(db.Integer, nullable=True)
    total_cells = db.Column(db.Integer, nullable=True)
    text_length = db.Column(db.Integer, nullable=True)
    evaluation_results = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    evaluated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Evaluation methods used
    evaluation_methods = db.Column(db.JSON, nullable=True)  # List of method IDs used
    selected_templates = db.Column(db.JSON, nullable=True)  # List of template IDs used
    
    # Specific evaluation scores for the 6 categories
    line_editing_score = db.Column(db.Integer, nullable=True)
    plot_score = db.Column(db.Integer, nullable=True)
    character_score = db.Column(db.Integer, nullable=True)
    flow_score = db.Column(db.Integer, nullable=True)
    worldbuilding_score = db.Column(db.Integer, nullable=True)
    readiness_score = db.Column(db.Integer, nullable=True)
    
    # Overall score
    overall_score = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        """Convert evaluation to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'status': self.status.value,
            'file_size': self.file_size,
            'total_sheets': self.total_sheets,
            'total_cells': self.total_cells,
            'text_length': self.text_length,
            'download_url': self.download_url,
            'error_message': self.error_message,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'evaluation_methods': self.evaluation_methods,
            'selected_templates': self.selected_templates,
            'line_editing_score': self.line_editing_score,
            'plot_score': self.plot_score,
            'character_score': self.character_score,
            'flow_score': self.flow_score,
            'worldbuilding_score': self.worldbuilding_score,
            'readiness_score': self.readiness_score,
            'overall_score': self.overall_score,
            'evaluation_results': self.evaluation_results
        }
    
    def calculate_overall_score(self):
        """Calculate overall score from individual category scores"""
        scores = [
            self.line_editing_score,
            self.plot_score,
            self.character_score,
            self.flow_score,
            self.worldbuilding_score,
            self.readiness_score
        ]
        valid_scores = [score for score in scores if score is not None]
        if valid_scores:
            self.overall_score = round(sum(valid_scores) / len(valid_scores))
        return self.overall_score
    
    def __repr__(self):
        return f'<Evaluation {self.id} - {self.original_filename}>'

class EvaluationTemplate(db.Model):
    __tablename__ = 'evaluation_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_s3_key = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)  # Basic template
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    evaluation_criteria = db.Column(db.JSON, nullable=True)  # Parsed criteria from Excel
    template_type = db.Column(db.String(50), default='custom', nullable=False)  # basic, custom
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_templates')
    
    def to_dict(self):
        """Convert evaluation template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'original_filename': self.original_filename,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'uploaded_by': self.uploaded_by,
            'file_size': self.file_size,
            'evaluation_criteria': self.evaluation_criteria,
            'template_type': self.template_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<EvaluationTemplate {self.name}>'

class EvaluationStyle(db.Model):
    __tablename__ = 'evaluation_styles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_s3_key = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    evaluation_criteria = db.Column(db.JSON, nullable=True)  # Parsed criteria from Excel
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_styles')
    
    def to_dict(self):
        """Convert evaluation style to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'uploaded_by': self.uploaded_by,
            'file_size': self.file_size,
            'evaluation_criteria': self.evaluation_criteria,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<EvaluationStyle {self.name}>'
