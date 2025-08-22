# LADI Manuscript Evaluation System - Backend

A Flask-based backend system for AI-powered manuscript evaluation using OpenAI GPT-4 API.

## Features

- **Document Upload & Processing**: Support for PDF and DOCX files
- **AI-Powered Evaluation**: 6 comprehensive evaluation categories using GPT-4
- **PostgreSQL Database**: Robust data storage with proper relationships
- **JWT Authentication**: Secure user authentication and authorization
- **PDF Report Generation**: Professional evaluation reports
- **S3 Integration**: Cloud storage for files and reports
- **RESTful API**: Clean API endpoints for frontend integration

## Evaluation Categories

The system evaluates manuscripts across 6 key dimensions:

1. **Line & Copy Editing**: Grammar, syntax, clarity, and prose fluidity
2. **Plot Evaluation**: Story structure, pacing, narrative tension, and resolution
3. **Character Evaluation**: Character depth, motivation, consistency, and emotional impact
4. **Book Flow Evaluation**: Rhythm, transitions, escalation patterns, and narrative cohesion
5. **Worldbuilding & Setting**: Setting depth, continuity, and originality
6. **LADI Readiness Score**: Overall readiness assessment with proprietary scoring

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key
- AWS S3 (optional, for cloud storage)

## Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/ladi_db
   
   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key
   
   # AWS Configuration (optional)
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_S3_BUCKET=your-s3-bucket-name
   
   # Flask Configuration
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb ladi_db
   
   # Run database setup
   python setup_database.py
   ```

## Database Setup

The system uses PostgreSQL for production and SQLite for development. To set up PostgreSQL:

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create database and user**
   ```sql
   CREATE DATABASE ladi_db;
   CREATE USER ladi_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE ladi_db TO ladi_user;
   ```

3. **Run migrations**
   ```bash
   python setup_database.py
   ```

## Running the Application

1. **Development mode**
   ```bash
   python run.py
   ```

2. **Production mode**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

The API will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

### Document Evaluation
- `POST /api/upload/evaluate` - Upload and evaluate document
- `GET /api/upload/evaluation/<id>` - Get evaluation results
- `GET /api/upload/evaluation/<id>/download` - Download evaluation report
- `GET /api/upload/evaluations` - Get user's evaluation history

### User Management
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/evaluations` - Get user evaluations

### Admin (if admin role)
- `GET /api/admin/users` - Get all users
- `GET /api/admin/evaluations` - Get all evaluations
- `PUT /api/admin/user/<id>` - Update user status

## File Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── config/              # Configuration settings
│   ├── models/              # Database models
│   ├── routes/              # API routes
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── migrations/              # Database migrations
├── temp_uploads/            # Temporary file storage
├── requirements.txt         # Python dependencies
├── setup_database.py        # Database setup script
├── run.py                   # Application entry point
└── README.md               # This file
```

## Services

### GPT Evaluator
- Handles AI-powered manuscript evaluation
- Supports 6 evaluation categories
- Fallback to mock evaluation for development

### PDF Generator
- Creates professional evaluation reports
- Includes executive summary and detailed analysis
- Supports custom styling and branding

### File Parsers
- PDF Parser: Extracts text from PDF files
- DOCX Parser: Extracts text from Word documents
- Excel Parser: Parses evaluation criteria from Excel files

### S3 Service
- Cloud storage integration
- File upload and download
- Presigned URL generation

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Code Style
```bash
# Format code
black app/

# Lint code
flake8 app/
```

## Deployment

### Docker
```bash
# Build image
docker build -t ladi-backend .

# Run container
docker run -p 5000:5000 ladi-backend
```

### Environment Variables for Production
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/ladi_db
OPENAI_API_KEY=your-production-openai-key
AWS_S3_BUCKET=your-production-s3-bucket
SECRET_KEY=your-production-secret-key
```

## Security Considerations

- JWT tokens for authentication
- Password hashing with bcrypt
- CORS configuration
- File upload validation
- SQL injection prevention with SQLAlchemy
- Environment variable management

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure database and user exist
- Check firewall settings

### OpenAI API Issues
- Verify API key is valid
- Check API quota and limits
- Ensure proper network connectivity

### File Upload Issues
- Check file size limits
- Verify file format support
- Ensure temp_uploads directory exists
- Check disk space

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `ladi_app.log`
3. Verify environment configuration
4. Test with the provided test files

## License

This project is proprietary software for LADI Manuscript Evaluation System. 