#!/usr/bin/env python3
"""
LADI Backend Environment Setup Script
This script creates a .env file from env.example if it doesn't exist
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Setup environment file and directories"""
    print("Setting up LADI backend environment...")
    
    # Get the backend directory
    backend_dir = Path(__file__).parent
    env_example = backend_dir / "env.example"
    env_file = backend_dir / ".env"
    
    # Create .env file from env.example if it doesn't exist
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from env.example...")
        shutil.copy(env_example, env_file)
        print("✓ .env file created successfully")
    elif env_file.exists():
        print("✓ .env file already exists")
    else:
        print("⚠ env.example not found, creating comprehensive .env file...")
        create_comprehensive_env(env_file)
    
    # Create necessary directories
    directories = [
        "temp_uploads",
        "temp_uploads/reports", 
        "temp_uploads/templates",
        "uploads",
        "uploads/reports",
        "uploads/templates"
    ]
    
    for directory in directories:
        dir_path = backend_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directory created/verified: {directory}")
    
    print("\nEnvironment setup completed!")
    print("Next steps:")
    print("1. Edit .env file if needed")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: flask db upgrade")
    print("4. Run: python run.py")

def create_comprehensive_env(env_file):
    """Create a comprehensive .env file with all required variables"""
    comprehensive_env_content = """# Flask Configuration
SECRET_KEY=ladi-secret-key-development-2024
FLASK_ENV=development
FLASK_DEBUG=true

# Database Configuration
# For SQLite (development):
DATABASE_URL=sqlite:///ladi_dev.db
# For PostgreSQL (production):
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ladi_db

# JWT Configuration
JWT_SECRET_KEY=ladi-jwt-secret-key-2024

# File Upload Configuration
UPLOAD_FOLDER=temp_uploads
MAX_CONTENT_LENGTH=16777216

# AWS S3 Configuration (optional for development)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET=

# OpenAI Configuration (optional for development)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4

# Report Configuration
REPORT_EXPIRY_HOURS=24

# Email Configuration (optional for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=

# Frontend URL
FRONTEND_URL=http://localhost:8080

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Request Timeout Configuration
REQUEST_TIMEOUT=300
UPLOAD_TIMEOUT=600
"""
    
    with open(env_file, 'w') as f:
        f.write(comprehensive_env_content)

if __name__ == "__main__":
    setup_environment()
