# LADI Backend

A Flask-based REST API backend for the Literary Analysis and Development Interface (LADI) platform. This backend provides comprehensive manuscript evaluation services using AI-powered analysis and custom evaluation templates.

## Features

### Core Functionality
- **User Authentication**: JWT-based authentication system
- **Document Processing**: Support for PDF, DOCX, XLS, and XLSX files
- **AI Evaluation**: GPT-powered manuscript analysis
- **Template System**: Custom evaluation templates with Excel-based criteria
- **Multi-Method Evaluation**: Combine basic and template-based evaluations
- **PDF Report Generation**: Detailed evaluation reports in PDF format
- **File Management**: Secure file upload and storage system

### User Management
- **Profile Management**: Update personal information
- **Password Management**: Secure password change functionality
- **Account Management**: Account deletion with confirmation

### Template Management
- **Template Upload**: Upload custom evaluation templates (Excel format)
- **Template CRUD**: Create, read, update, and delete templates
- **Template Parsing**: Automatic parsing of Excel-based evaluation criteria
- **Template Selection**: Choose templates for evaluation

## Technology Stack

- **Framework**: Flask 2.3.3
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy with Flask-Migrate
- **Authentication**: Flask-JWT-Extended
- **File Processing**: 
  - PyPDF2 for PDF files
  - python-docx for DOCX files
  - openpyxl for Excel files
- **Report Generation**: ReportLab for PDF reports
- **CORS**: Flask-CORS for cross-origin requests

## Project Structure

```
backend/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── config/                  # Configuration settings
│   │   └── __init__.py
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py              # User model
│   │   └── evaluation.py        # Evaluation and Template models
│   ├── routes/                  # API routes
│   │   ├── __init__.py
│   │   ├── auth_routes.py       # Authentication endpoints
│   │   ├── user_routes.py       # User management endpoints
│   │   ├── upload_routes.py     # File upload and evaluation
│   │   └── template_routes.py   # Template management
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── gpt_evaluator.py     # GPT-based evaluation
│   │   ├── template_evaluator.py # Template-based evaluation
│   │   ├── pdf_parser.py        # PDF text extraction
│   │   ├── docx_parser.py       # DOCX text extraction
│   │   ├── excel_parser.py      # Excel template parsing
│   │   ├── pdf_generator.py     # PDF report generation
│   │   └── local_storage_service.py # File storage
│   └── utils/                   # Utility functions
├── migrations/                  # Database migrations
├── uploads/                     # File upload directory
│   ├── reports/                 # Generated PDF reports
│   └── templates/               # Uploaded templates
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── env.example                  # Environment variables example
└── README.md                    # This file
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `POST /api/user/change-password` - Change password
- `POST /api/user/delete-account` - Delete account

### File Upload and Evaluation
- `POST /api/upload/evaluate` - Upload and evaluate document
- `GET /api/upload/download/<filename>` - Download evaluation report

### Template Management
- `GET /api/templates` - List all templates
- `POST /api/templates` - Upload new template
- `GET /api/templates/<id>` - Get template details
- `PUT /api/templates/<id>` - Update template
- `DELETE /api/templates/<id>` - Delete template
- `GET /api/templates/<id>/download` - Download template file

## Database Models

### User Model
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password
- `first_name`: User's first name
- `last_name`: User's last name
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

### Evaluation Model
- `id`: Primary key
- `user_id`: Foreign key to User
- `original_filename`: Original uploaded filename
- `file_s3_key`: Storage key for uploaded file
- `evaluation_results`: JSON evaluation results
- `pdf_report_path`: Path to generated PDF report
- `evaluation_methods`: JSON list of evaluation methods used
- `selected_templates`: JSON list of template IDs used
- `created_at`: Evaluation timestamp

### EvaluationTemplate Model
- `id`: Primary key
- `name`: Template name
- `description`: Template description
- `file_s3_key`: Storage key for template file
- `original_filename`: Original template filename
- `is_active`: Template availability flag
- `is_default`: Basic template flag
- `uploaded_by`: Foreign key to User
- `file_size`: Template file size
- `evaluation_criteria`: Parsed criteria from Excel
- `template_type`: Template type (basic/custom)
- `created_at`: Template creation timestamp
- `updated_at`: Template update timestamp

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Quick Setup
1. **Clone the repository** (if not already done)
2. **Run the setup script** from the project root:
   ```bash
   # Unix/Linux/macOS
   ./setup.sh
   
   # Windows
   setup.bat
   ```

### Manual Setup
1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Activate virtual environment**:
   ```bash
   # Unix/Linux/macOS
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Create upload directories**:
   ```bash
   mkdir -p uploads/reports uploads/templates
   ```

### Running the Application

#### Development Mode
```bash
python run.py
```

#### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

The API will be available at `http://localhost:5000`

## Configuration

### Environment Variables
Create a `.env` file in the backend directory with the following variables:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///instance/ladi.db

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=3600

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads

# API Configuration
REQUEST_TIMEOUT=300
UPLOAD_TIMEOUT=600
```

### Database Configuration
- **Development**: SQLite database (default)
- **Production**: PostgreSQL (update DATABASE_URL)

## Development

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Testing
- Write unit tests for all new features
- Test API endpoints with tools like Postman
- Verify file upload and processing functionality

### Database Migrations
When making model changes:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **JWT Authentication**: Stateless authentication with token refresh
- **Input Validation**: Comprehensive request validation
- **File Type Validation**: Secure file upload with type checking
- **CORS Protection**: Configured for frontend integration
- **SQL Injection Protection**: Using SQLAlchemy ORM

## Error Handling

The API provides consistent error responses:
```json
{
  "error": "Error message",
  "success": false
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## Performance Considerations

- **File Processing**: Asynchronous processing for large files
- **Database Queries**: Optimized queries with proper indexing
- **Memory Management**: Efficient file handling and cleanup
- **Timeout Handling**: Cross-platform timeout implementation

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Check DATABASE_URL in .env
   - Ensure database file permissions

2. **File Upload Issues**:
   - Verify upload directory exists
   - Check file size limits
   - Validate file types

3. **JWT Token Issues**:
   - Check JWT_SECRET_KEY configuration
   - Verify token expiration settings

4. **Import Errors**:
   - Ensure virtual environment is activated
   - Check all dependencies are installed

### Logs
Check application logs for detailed error information:
```bash
tail -f ladi_app.log
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Update documentation for new features
4. Test thoroughly before submitting changes

## License

This project is part of the LADI platform. See the main project README for license information. 