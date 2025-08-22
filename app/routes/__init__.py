# Import all blueprints
from .auth_routes import auth_bp
from .user_routes import user_bp
from .admin_routes import admin_bp
from .upload_routes import upload_bp
from .template_routes import template_bp

__all__ = ['auth_bp', 'user_bp', 'admin_bp', 'upload_bp', 'template_bp'] 