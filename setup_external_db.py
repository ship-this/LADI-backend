#!/usr/bin/env python3
"""
External Database Setup Script for LADI Backend
This script helps set up external PostgreSQL database for the LADI project.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def test_external_connection():
    """Test connection to the external PostgreSQL database"""
    try:
        # External database URL
        db_url = "postgresql://ladi_user:sFF4bMH7Denh8rXMkuWsL2pkrbEUr2hd@dpg-d2jrq1f5r7bs73e3f0qg-a.oregon-postgres.render.com/ladi"
        
        print("[INFO] Testing connection to external database...")
        conn = psycopg2.connect(db_url)
        
        # Test basic operations
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[SUCCESS] Connected to PostgreSQL: {version[0]}")
        
        # Check if database exists and is accessible
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()
        print(f"[SUCCESS] Connected to database: {db_name[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    except ImportError:
        print("[ERROR] psycopg2 is not installed")
        print("Please install: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def create_env_file():
    """Create .env file with external database configuration"""
    env_content = """# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration (External PostgreSQL - Render.com)
DATABASE_URL=postgresql://ladi_user:sFF4bMH7Denh8rXMkuWsL2pkrbEUr2hd@dpg-d2jrq1f5r7bs73e3f0qg-a.oregon-postgres.render.com/ladi

# JWT Configuration
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=3600

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads

# API Configuration
REQUEST_TIMEOUT=300
UPLOAD_TIMEOUT=600

# CORS Configuration
CORS_ORIGINS=http://localhost:8080,http://localhost:3000,http://localhost:5173
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("[SUCCESS] .env file created with external database configuration")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .env file: {e}")
        return False

def check_database_tables():
    """Check if database tables exist"""
    try:
        db_url = "postgresql://ladi_user:sFF4bMH7Denh8rXMkuWsL2pkrbEUr2hd@dpg-d2jrq1f5r7bs73e3f0qg-a.oregon-postgres.render.com/ladi"
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"[INFO] Found {len(tables)} existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("[INFO] No existing tables found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to check database tables: {e}")
        return False

def main():
    """Main function to set up external database"""
    print("=" * 60)
    print("LADI Backend - External Database Setup Script")
    print("=" * 60)
    
    print("[INFO] This script will configure the LADI project to use external PostgreSQL")
    print("[INFO] Database: Render.com PostgreSQL")
    print("[INFO] URL: dpg-d2jrq1f5r7bs73e3f0qg-a.oregon-postgres.render.com")
    print()
    
    # Check if we're in the backend directory
    if not os.path.exists("app"):
        print("[ERROR] Please run this script from the backend directory")
        sys.exit(1)
    
    # Test external database connection
    print("[INFO] Testing external database connection...")
    if not test_external_connection():
        print("\n[ERROR] External database connection failed")
        print("Please check:")
        print("1. Internet connection")
        print("2. Database URL is correct")
        print("3. Database credentials are valid")
        print("4. Database is accessible from your network")
        sys.exit(1)
    
    print("[SUCCESS] External database connection successful")
    
    # Check existing tables
    print("\n[INFO] Checking existing database tables...")
    check_database_tables()
    
    # Create .env file
    print("\n[INFO] Creating environment configuration...")
    if not create_env_file():
        print("\n[ERROR] Failed to create .env file")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] External database setup completed successfully!")
    print("=" * 60)
    print("\nDatabase Configuration:")
    print("- Host: dpg-d2jrq1f5r7bs73e3f0qg-a.oregon-postgres.render.com")
    print("- Database: ladi")
    print("- User: ladi_user")
    print("- Provider: Render.com")
    print("\nNext steps:")
    print("1. Run: flask db upgrade")
    print("2. Start the backend server: python run.py")
    print("3. The API will be available at http://localhost:5000")
    print("\nNote: This external database is shared and persistent.")
    print("Data will be preserved between application restarts.")

if __name__ == "__main__":
    main()
