from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.evaluation import Evaluation
from app import db
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user's profile information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_active': user.is_active,
                'email_verified': user.email_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        
        if 'email' in data:
            email = data['email'].strip().lower()
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user_id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = email
        
        db.session.commit()
        
        logger.info(f"User {current_user_id} updated their profile")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_active': user.is_active,
                'email_verified': user.email_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate required fields
        if not current_password:
            return jsonify({'error': 'Current password is required'}), 400
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
        
        if not confirm_password:
            return jsonify({'error': 'Password confirmation is required'}), 400
        
        # Validate current password
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New password and confirmation do not match'}), 400
        
        # Check if new password is same as current
        if check_password_hash(user.password_hash, new_password):
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # Update password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        logger.info(f"User {current_user_id} changed their password")
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/delete-account', methods=['POST'])
@jwt_required()
def delete_account():
    """Delete user account"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        # Validate required fields
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if not confirmation:
            return jsonify({'error': 'Confirmation is required'}), 400
        
        if confirmation != 'DELETE':
            return jsonify({'error': 'Confirmation must be "DELETE"'}), 400
        
        # Validate password
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Password is incorrect'}), 400
        
        # Delete user account
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"User {current_user_id} deleted their account")
        
        return jsonify({
            'success': True,
            'message': 'Account deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/evaluations', methods=['GET'])
@jwt_required()
def get_user_evaluations():
    """Get all evaluations for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters for filtering and pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        
        # Build query
        query = Evaluation.query.filter_by(user_id=current_user_id)
        
        # Apply status filter
        if status:
            query = query.filter_by(status=status)
        
        # Apply search filter
        if search:
            query = query.filter(Evaluation.original_filename.ilike(f'%{search}%'))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        evaluations = query.order_by(Evaluation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'evaluations': [eval.to_dict() for eval in evaluations.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': evaluations.pages,
                'has_next': evaluations.has_next,
                'has_prev': evaluations.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user evaluations: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/evaluations/<int:evaluation_id>', methods=['DELETE'])
@jwt_required()
def delete_evaluation(evaluation_id):
    """Delete a specific evaluation for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Find the evaluation
        evaluation = Evaluation.query.filter_by(
            id=evaluation_id, 
            user_id=current_user_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        # Delete associated files from storage
        from app.services.s3_service import S3Service
        storage_service = S3Service()
        
        try:
            # Delete original file
            if evaluation.original_file_s3_key:
                storage_service.delete_file(evaluation.original_file_s3_key)
            
            # Delete report file
            if evaluation.report_file_s3_key:
                storage_service.delete_file(evaluation.report_file_s3_key)
                
        except Exception as e:
            logger.warning(f"Failed to delete files from storage: {e}")
            # Continue with database deletion even if file deletion fails
        
        # Delete from database
        db.session.delete(evaluation)
        db.session.commit()
        
        logger.info(f"User {current_user_id} deleted evaluation {evaluation_id}")
        
        return jsonify({
            'success': True,
            'message': 'Evaluation deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting evaluation: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/evaluations/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_evaluations():
    """Delete multiple evaluations for current user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'evaluation_ids' not in data:
            return jsonify({'error': 'No evaluation IDs provided'}), 400
        
        evaluation_ids = data['evaluation_ids']
        if not isinstance(evaluation_ids, list):
            return jsonify({'error': 'evaluation_ids must be a list'}), 400
        
        # Find evaluations that belong to the current user
        evaluations = Evaluation.query.filter(
            Evaluation.id.in_(evaluation_ids),
            Evaluation.user_id == current_user_id
        ).all()
        
        if not evaluations:
            return jsonify({'error': 'No evaluations found'}), 404
        
        # Delete associated files from storage
        from app.services.s3_service import S3Service
        storage_service = S3Service()
        deleted_files_count = 0
        
        for evaluation in evaluations:
            try:
                # Delete original file
                if evaluation.original_file_s3_key:
                    storage_service.delete_file(evaluation.original_file_s3_key)
                    deleted_files_count += 1
                
                # Delete report file
                if evaluation.report_file_s3_key:
                    storage_service.delete_file(evaluation.report_file_s3_key)
                    deleted_files_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to delete files for evaluation {evaluation.id}: {e}")
        
        # Delete from database
        deleted_ids = [eval.id for eval in evaluations]
        Evaluation.query.filter(Evaluation.id.in_(deleted_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        logger.info(f"User {current_user_id} bulk deleted {len(evaluations)} evaluations")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {len(evaluations)} evaluations',
            'deleted_count': len(evaluations),
            'deleted_files_count': deleted_files_count,
            'deleted_evaluation_ids': deleted_ids
        }), 200
        
    except Exception as e:
        logger.error(f"Error bulk deleting evaluations: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@user_bp.route('/evaluations/<int:evaluation_id>', methods=['PUT'])
@jwt_required()
def update_evaluation(evaluation_id):
    """Update a specific evaluation for current user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Find the evaluation
        evaluation = Evaluation.query.filter_by(
            id=evaluation_id, 
            user_id=current_user_id
        ).first()
        
        if not evaluation:
            return jsonify({'error': 'Evaluation not found'}), 404
        
        # Update allowed fields
        if 'original_filename' in data:
            evaluation.original_filename = data['original_filename'].strip()
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"User {current_user_id} updated evaluation {evaluation_id}")
        
        return jsonify({
            'success': True,
            'message': 'Evaluation updated successfully',
            'evaluation': evaluation.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating evaluation: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
