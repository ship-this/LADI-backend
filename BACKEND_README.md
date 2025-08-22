# LADI Backend - Literary Analysis and Development Interface

## Overview

The LADI backend is a Flask-based REST API that provides manuscript evaluation and analysis services. It supports document parsing (PDF, DOCX, Excel), AI-powered evaluation, template management, and user authentication.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py              # Flask app factory and configuration
│   ├── config/                  # Configuration settings
│   │   └── __init__.py         # Environment-based config
│   ├── models/                  # Database models
│   │   ├── __init__.py         # Model imports
│   │   ├── user.py             # User and authentication models
│   │   ├── evaluation.py       # Evaluation and template models
│   │   └── user_session.py     # User session tracking
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py         # Blueprint registration
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── user_routes.py      # User management
│   │   ├── admin_routes.py     # Admin functionality
│   │   ├── upload_routes.py    # File upload and evaluation
│   │   └── template_routes.py  # Template management
│   ├── services/               # Business logic services
│   │   ├── docx_parser.py      # DOCX file parsing
│   │   ├── pdf_parser.py       # PDF file parsing
│   │   ├── excel_parser.py     # Excel file parsing
│   │   ├── gpt_evaluator.py    # AI evaluation service
│   │   ├── template_evaluator.py # Template-based evaluation
│   │   ├── pdf_generator.py    # Report generation
│   │   ├── email_service.py    # Email notifications
│   │   ├── s3_service.py       # AWS S3 integration
│   │   └── local_storage_service.py # Local file storage
│   └── utils/                  # Utility functions
├── migrations/                 # Database migrations
├── temp_uploads/              # Temporary file storage
├── uploads/                   # Permanent file storage
├── instance/                  # Instance-specific files (database)
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
├── setup_env.py              # Environment setup script
├── setup_external_db.py      # External database setup
├── fix_migrations.py         # Migration fixes
└── env.example               # Environment variables template
```

## Features

### Core Functionality
- **Document Parsing**: Support for PDF, DOCX, and Excel files
- **AI Evaluation**: GPT-powered manuscript analysis
- **Template System**: Customizable evaluation templates
- **User Management**: Authentication, authorization, and profiles
- **File Management**: Upload, storage, and retrieval
- **Report Generation**: PDF reports with evaluation results

### API Endpoints

#### Authentication (`/api/auth`)
- `POST /login` - User login
- `POST /register` - User registration
- `POST /logout` - User logout
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset

#### User Management (`/api/user`)
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile
- `GET /evaluations` - Get user evaluations
- `DELETE /account` - Delete user account

#### File Upload & Evaluation (`/api/upload`)
- `POST /upload` - Upload document for evaluation
- `POST /evaluate` - Start evaluation process
- `GET /status/<id>` - Get evaluation status
- `GET /download/<id>` - Download evaluation report
- `DELETE /evaluation/<id>` - Delete evaluation

#### Template Management (`/api/templates`)
- `GET /templates` - List available templates
- `POST /templates` - Upload new template
- `PUT /templates/<id>` - Update template
- `DELETE /templates/<id>` - Delete template

#### Admin Functions (`/api/admin`)
- `GET /users` - List all users
- `GET /evaluations` - List all evaluations
- `PUT /users/<id>/role` - Update user role
- `DELETE /users/<id>` - Delete user

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Quick Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup environment**
   ```bash
   python setup_env.py
   ```

6. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

### Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=true

# Database Configuration
# For SQLite (development):
DATABASE_URL=sqlite:///ladi_dev.db
# For PostgreSQL (production):
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ladi_db

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key

# File Upload Configuration
UPLOAD_FOLDER=temp_uploads
MAX_CONTENT_LENGTH=16777216

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1

# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Report Configuration
REPORT_EXPIRY_HOURS=24

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Frontend URL
FRONTEND_URL=http://localhost:8080

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Request Timeout Configuration
REQUEST_TIMEOUT=300
UPLOAD_TIMEOUT=600
```

## Database Models

### User Model
- Email, password, name, role
- Email verification status
- Account creation and update timestamps

### Evaluation Model
- Document metadata (filename, size, type)
- Evaluation results and scores
- Template used for evaluation
- User who requested evaluation

### EvaluationTemplate Model
- Template name and description
- File storage information
- Evaluation criteria configuration
- Default template flag

### UserSession Model
- Session tracking for analytics
- User activity logging

## Services

### Document Parsers
- **DOCX Parser**: Extracts text and formatting from Word documents
- **PDF Parser**: Extracts text from PDF files
- **Excel Parser**: Processes Excel templates and data

### AI Services
- **GPT Evaluator**: Uses OpenAI GPT models for manuscript analysis
- **Template Evaluator**: Applies custom evaluation templates

### Storage Services
- **Local Storage**: File storage on local filesystem
- **S3 Service**: AWS S3 integration for cloud storage

### Utility Services
- **PDF Generator**: Creates evaluation reports
- **Email Service**: Sends notifications and password resets

## Development

### Running in Development Mode
```bash
python run.py
```

The server will start on `http://localhost:5000`

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

### Testing
```bash
# Run tests (if available)
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

## Production Deployment

### Environment Variables
Set production environment variables:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `DATABASE_URL` (PostgreSQL recommended)
- `SECRET_KEY` (strong, unique key)
- `JWT_SECRET_KEY` (strong, unique key)

### WSGI Server
Use Gunicorn for production:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Database
- Use PostgreSQL for production
- Set up proper database backups
- Configure connection pooling

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check all dependencies are installed: `pip install -r requirements.txt`

2. **Database Errors**
   - Run migrations: `flask db upgrade`
   - Check database URL in `.env` file
   - Ensure database file permissions

3. **File Upload Issues**
   - Check upload directory permissions
   - Verify `MAX_CONTENT_LENGTH` setting
   - Ensure sufficient disk space

4. **CORS Errors**
   - Check `CORS_ORIGINS` in `.env`
   - Verify frontend URL is included

### Logs
Check the `ladi_app.log` file for detailed error information.

## API Documentation

The API follows RESTful conventions and returns JSON responses. All endpoints require authentication except for login and registration.

### Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Success message"
}
```

### Error Format
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages

## License

This project is part of the LADI (Literary Analysis and Development Interface) system.
