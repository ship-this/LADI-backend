from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, decode_token, get_jwt
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, UserRole, db
from app.models.user_session import UserSession
from app.services.email_service import EmailService
from datetime import datetime, timedelta
import logging
import re
import secrets
import hashlib

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        user = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.USER
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Create JWT tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(session)
        db.session.commit()
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh JWT token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Verify the refresh token
        try:
            decoded_token = decode_token(refresh_token)
            current_user_id = int(decoded_token['sub'])
        except Exception as e:
            logger.error(f"Invalid refresh token: {e}")
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Create new access token
        new_access_token = create_access_token(identity=str(current_user_id))
        
        # Update session
        session = UserSession.query.filter_by(
            user_id=current_user_id,
            refresh_token=refresh_token
        ).first()
        
        if session:
            session.session_token = new_access_token
            session.update_last_used()
            db.session.commit()
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Deactivate current session
        session = UserSession.query.filter_by(
            user_id=current_user_id,
            session_token=get_jwt()['jti']
        ).first()
        
        if session:
            session.is_active = False
            db.session.commit()
        
        logger.info(f"User logged out: {current_user_id}")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if user exists or not
            return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Generate reset token with specific claims
        reset_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1),
            additional_claims={'type': 'password_reset'}
        )
        
        # Send email (implement email service)
        try:
            email_service = EmailService()
            email_service.send_password_reset_email(user.email, reset_token)
            logger.info(f"Password reset email sent to: {email}")
        except Exception as email_error:
            logger.error(f"Failed to send password reset email: {email_error}")
            # In development, we might want to return the token for testing
            if current_app.config.get('FLASK_ENV') == 'development':
                return jsonify({
                    'message': 'Password reset link generated (development mode)',
                    'reset_token': reset_token
                }), 200
        
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
@jwt_required()
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Verify this is a password reset token
        claims = get_jwt()
        if claims.get('type') != 'password_reset':
            return jsonify({'error': 'Invalid token type'}), 400
        
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Deactivate all user sessions
        UserSession.query.filter_by(user_id=current_user_id).update({'is_active': False})
        db.session.commit()
        
        logger.info(f"Password reset for user: {user.email}")
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Password reset failed'}), 500

@auth_bp.route('/verify-reset-token', methods=['POST'])
@jwt_required()
def verify_reset_token():
    """Verify password reset token is valid"""
    try:
        # Verify this is a password reset token
        claims = get_jwt()
        if claims.get('type') != 'password_reset':
            return jsonify({'error': 'Invalid token type'}), 400
        
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'message': 'Token is valid',
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Verify reset token error: {e}")
        return jsonify({'error': 'Token verification failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500
