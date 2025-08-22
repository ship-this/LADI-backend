from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config import config
from app.models.user import db, bcrypt
from app.models import User, Evaluation, EvaluationStyle, UserSession, EvaluationTemplate
import logging

# Initialize Flask extensions
login_manager = LoginManager()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure request timeout for long-running operations
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Setup CORS
    CORS(app, supports_credentials=True)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Missing token'}, 401
    
    # Register blueprints
    from app.routes import auth_bp, user_bp, admin_bp, upload_bp, template_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(template_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        from app.models.user import UserRole
        admin_user = User.query.filter_by(email='admin@ladi.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@ladi.com',
                password='admin123',  # Change this in production
                first_name='Admin',
                last_name='User',
                role=UserRole.ADMIN
            )
            admin_user.email_verified = True
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created: admin@ladi.com / admin123")
        
        # Create default basic template if it doesn't exist
        basic_template = EvaluationTemplate.query.filter_by(is_default=True).first()
        if not basic_template:
            basic_template = EvaluationTemplate(
                name='Basic Evaluation',
                description='Default LADI evaluation template with standard criteria',
                file_s3_key='templates/default/basic_template.xlsx',
                original_filename='basic_template.xlsx',
                uploaded_by=admin_user.id,
                file_size=0,
                evaluation_criteria={},
                template_type='basic',
                is_default=True,
                is_active=True
            )
            db.session.add(basic_template)
            db.session.commit()
            print("Default basic template created")
    
    return app 