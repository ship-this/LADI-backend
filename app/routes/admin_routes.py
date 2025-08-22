from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User, UserRole, db
from app.models.evaluation import Evaluation, EvaluationStyle, EvaluationStatus
from app.models.user_session import UserSession
from app.services.s3_service import S3Service
from app.services.excel_parser import ExcelParser
from datetime import datetime, timedelta
import logging
import os
import uuid
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to check if user is admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# User Management
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role = request.args.get('role')
        search = request.args.get('search')
        is_active = request.args.get('is_active')
        
        # Build query
        query = User.query
        
        if role:
            try:
                role_enum = UserRole(role)
                query = query.filter_by(role=role_enum)
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter_by(is_active=is_active_bool)
        
        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users = [user.to_dict() for user in pagination.items]
        
        return jsonify({
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_details(user_id):
    """Get specific user details"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user statistics
        total_evaluations = Evaluation.query.filter_by(user_id=user_id).count()
        completed_evaluations = Evaluation.query.filter_by(
            user_id=user_id, 
            status=EvaluationStatus.COMPLETED
        ).count()
        
        user_data = user.to_dict()
        user_data['statistics'] = {
            'total_evaluations': total_evaluations,
            'completed_evaluations': completed_evaluations
        }
        
        return jsonify({
            'user': user_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get user details error: {e}")
        return jsonify({'error': 'Failed to get user details'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user information"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        if 'role' in data:
            try:
                user.role = UserRole(data['role'])
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        if 'email_verified' in data:
            user.email_verified = bool(data['email_verified'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {user_id} updated by admin")
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete user and all associated data"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_admin():
            return jsonify({'error': 'Cannot delete admin user'}), 400
        
        # Delete user's evaluations and files
        evaluations = Evaluation.query.filter_by(user_id=user_id).all()
        storage_service = S3Service()
        
        for evaluation in evaluations:
            try:
                if evaluation.original_file_s3_key:
                    storage_service.delete_file(evaluation.original_file_s3_key)
                if evaluation.report_file_s3_key:
                    storage_service.delete_file(evaluation.report_file_s3_key)
            except Exception as e:
                logger.warning(f"Failed to delete local files for evaluation {evaluation.id}: {e}")
        
        # Delete user (cascades to evaluations and sessions)
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"User {user_id} deleted by admin")
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

# Evaluation Style Management
@admin_bp.route('/evaluation-styles', methods=['GET'])
@jwt_required()
@admin_required
def get_evaluation_styles():
    """Get all evaluation styles"""
    try:
        styles = EvaluationStyle.query.order_by(EvaluationStyle.created_at.desc()).all()
        
        return jsonify({
            'styles': [style.to_dict() for style in styles]
        }), 200
        
    except Exception as e:
        logger.error(f"Get evaluation styles error: {e}")
        return jsonify({'error': 'Failed to get evaluation styles'}), 500

@admin_bp.route('/evaluation-styles', methods=['POST'])
@jwt_required()
@admin_required
def upload_evaluation_style():
    """Upload new evaluation style Excel file"""
    try:
        current_user_id = int(get_jwt_identity())
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.xls', '.xlsx')):
            return jsonify({'error': 'Only Excel files (.xls, .xlsx) are allowed'}), 400
        
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            return jsonify({'error': 'Style name is required'}), 400
        
        # Save file temporarily
        upload_folder = 'temp_uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        unique_filename = f"style_{uuid.uuid4().hex}_{filename}"
        temp_file_path = os.path.join(upload_folder, unique_filename)
        
        try:
            file.save(temp_file_path)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        try:
            # Parse Excel file to validate and extract criteria
            excel_parser = ExcelParser()
            parse_result = excel_parser.parse_excel_file(temp_file_path)
            
            # Upload to local storage
            storage_service = S3Service()
            file_key = f"evaluation_styles/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
            storage_service.upload_file(temp_file_path, file_key)
            
            # Create evaluation style record
            style = EvaluationStyle(
                name=name,
                description=description,
                file_s3_key=file_key,
                uploaded_by=current_user_id,
                file_size=os.path.getsize(temp_file_path),
                evaluation_criteria=parse_result.get('metadata', {})
            )
            
            db.session.add(style)
            db.session.commit()
            
            # Clean up temp file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            logger.info(f"Evaluation style uploaded: {name}")
            
            return jsonify({
                'message': 'Evaluation style uploaded successfully',
                'style': style.to_dict()
            }), 201
            
        except Exception as e:
            # Clean up temp file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            logger.error(f"Error processing evaluation style: {e}")
            return jsonify({'error': f'Failed to process file: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Upload evaluation style error: {e}")
        return jsonify({'error': 'Failed to upload evaluation style'}), 500

@admin_bp.route('/evaluation-styles/<int:style_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_evaluation_style(style_id):
    """Update evaluation style"""
    try:
        style = EvaluationStyle.query.get(style_id)
        
        if not style:
            return jsonify({'error': 'Evaluation style not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            style.name = data['name'].strip()
        if 'description' in data:
            style.description = data['description'].strip()
        if 'is_active' in data:
            style.is_active = bool(data['is_active'])
        
        style.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Evaluation style {style_id} updated")
        
        return jsonify({
            'message': 'Evaluation style updated successfully',
            'style': style.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Update evaluation style error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update evaluation style'}), 500

@admin_bp.route('/evaluation-styles/<int:style_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_evaluation_style(style_id):
    """Delete evaluation style"""
    try:
        style = EvaluationStyle.query.get(style_id)
        
        if not style:
            return jsonify({'error': 'Evaluation style not found'}), 404
        
        # Delete from local storage
        storage_service = S3Service()
        try:
            storage_service.delete_file(style.file_s3_key)
        except Exception as e:
            logger.warning(f"Failed to delete local file: {e}")
        
        # Delete from database
        db.session.delete(style)
        db.session.commit()
        
        logger.info(f"Evaluation style {style_id} deleted")
        
        return jsonify({'message': 'Evaluation style deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete evaluation style error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete evaluation style'}), 500

# System Statistics
@admin_bp.route('/statistics', methods=['GET'])
@jwt_required()
@admin_required
def get_system_statistics():
    """Get system-wide statistics"""
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(role=UserRole.ADMIN).count()
        
        # Evaluation statistics
        total_evaluations = Evaluation.query.count()
        completed_evaluations = Evaluation.query.filter_by(status=EvaluationStatus.COMPLETED).count()
        pending_evaluations = Evaluation.query.filter_by(status=EvaluationStatus.PENDING).count()
        failed_evaluations = Evaluation.query.filter_by(status=EvaluationStatus.FAILED).count()
        
        # Recent activity
        recent_evaluations = Evaluation.query.order_by(
            Evaluation.created_at.desc()
        ).limit(10).all()
        
        recent_users = User.query.order_by(
            User.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'statistics': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'admins': admin_users
                },
                'evaluations': {
                    'total': total_evaluations,
                    'completed': completed_evaluations,
                    'pending': pending_evaluations,
                    'failed': failed_evaluations
                }
            },
            'recent_activity': {
                'evaluations': [eval.to_dict() for eval in recent_evaluations],
                'users': [user.to_dict() for user in recent_users]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500
