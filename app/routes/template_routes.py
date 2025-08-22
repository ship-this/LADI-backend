import os
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models.evaluation import EvaluationTemplate, db
from app.services.s3_service import S3Service
from app.services.excel_parser import ExcelParser
from app.config import Config
from datetime import datetime

logger = logging.getLogger(__name__)
template_bp = Blueprint('template', __name__)

@template_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all templates for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's templates
        templates = EvaluationTemplate.query.filter_by(
            uploaded_by=current_user_id,
            is_active=True
        ).order_by(EvaluationTemplate.created_at.desc()).all()
        
        # Also get the default basic template
        basic_template = EvaluationTemplate.query.filter_by(
            is_default=True,
            is_active=True
        ).first()
        
        template_list = [template.to_dict() for template in templates]
        
        # Add basic template if it exists
        if basic_template:
            template_list.insert(0, basic_template.to_dict())
        
        return jsonify({
            'templates': template_list,
            'total': len(template_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@template_bp.route('/templates', methods=['POST'])
@jwt_required()
def upload_template():
    """Upload a new evaluation template"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if file was uploaded
        if 'template' not in request.files:
            return jsonify({'error': 'No template file provided'}), 400
        
        file = request.files['template']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xls', '.xlsx')):
            return jsonify({'error': 'Only Excel files (.xls, .xlsx) are allowed'}), 400
        
        # Validate file size (16MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 16 * 1024 * 1024:  # 16MB
            return jsonify({'error': 'File size exceeds 16MB limit'}), 400
        
        # Get template metadata from form
        name = request.form.get('name', file.filename)
        description = request.form.get('description', '')
        template_type = request.form.get('template_type', 'custom')
        
        # Save file to local storage
        storage_service = S3Service()
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_key = f'templates/{current_user_id}/{timestamp}_{filename}'
        
        # Save file temporarily first
        temp_file_path = os.path.join(Config.UPLOAD_FOLDER, f'temp_{timestamp}_{filename}')
        file.save(temp_file_path)
        
        # Upload to local storage
        storage_service.upload_file(temp_file_path, file_key)
        
        # Read file content for parsing
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
        
        # Parse template to extract criteria
        excel_parser = ExcelParser()
        
        try:
            parse_result = excel_parser.parse_excel_file(temp_file_path)
            evaluation_criteria = parse_result.get('metadata', {})
            
        except Exception as parse_error:
            logger.warning(f"Failed to parse template file: {parse_error}")
            evaluation_criteria = {}
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        # Create template record
        template = EvaluationTemplate(
            name=name,
            description=description,
            file_s3_key=file_key,
            original_filename=filename,
            uploaded_by=current_user_id,
            file_size=file_size,
            evaluation_criteria=evaluation_criteria,
            template_type=template_type,
            is_default=False,
            is_active=True
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template uploaded successfully',
            'template': template.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@template_bp.route('/templates/<int:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a specific template by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        template = EvaluationTemplate.query.filter_by(
            id=template_id,
            uploaded_by=current_user_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({
            'template': template.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@template_bp.route('/templates/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update template metadata"""
    try:
        current_user_id = get_jwt_identity()
        
        template = EvaluationTemplate.query.filter_by(
            id=template_id,
            uploaded_by=current_user_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'is_active' in data:
            template.is_active = data['is_active']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template updated successfully',
            'template': template.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@template_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a template"""
    try:
        current_user_id = get_jwt_identity()
        
        template = EvaluationTemplate.query.filter_by(
            id=template_id,
            uploaded_by=current_user_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Don't allow deletion of default template
        if template.is_default:
            return jsonify({'error': 'Cannot delete default template'}), 400
        
        # Delete file from storage
        storage_service = S3Service()
        try:
            storage_service.delete_file(template.file_s3_key)
        except Exception as storage_error:
            logger.warning(f"Failed to delete template file: {storage_error}")
        
        # Delete from database
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@template_bp.route('/templates/<int:template_id>/download', methods=['GET'])
@jwt_required()
def download_template(template_id):
    """Download template file"""
    try:
        current_user_id = get_jwt_identity()
        
        template = EvaluationTemplate.query.filter_by(
            id=template_id,
            uploaded_by=current_user_id
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Generate download URL
        storage_service = S3Service()
        download_url = storage_service.regenerate_download_url(template.file_s3_key, expiration_hours=1)
        
        return jsonify({
            'download_url': download_url,
            'filename': template.original_filename,
            'expires_in': '1 hour'
        }), 200
        
    except Exception as e:
        logger.error(f"Error downloading template: {e}")
        return jsonify({'error': 'Internal server error'}), 500
