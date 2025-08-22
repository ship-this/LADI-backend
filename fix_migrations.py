#!/usr/bin/env python3
"""
Fix migrations and database setup script for LADI backend
This script helps resolve migration issues and ensures the database is properly configured.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {description} completed")
            return True
        else:
            print(f"[ERROR] {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} failed: {e}")
        return False

def check_database_status():
    """Check the current database migration status"""
    print("[INFO] Checking database migration status...")
    try:
        result = subprocess.run("flask db current", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            current = result.stdout.strip()
            print(f"[INFO] Current migration: {current}")
            return current
        else:
            print("[INFO] No database found or not initialized")
            return None
    except Exception as e:
        print(f"[ERROR] Could not check database status: {e}")
        return None

def main():
    """Main function to fix migrations and setup database"""
    print("=" * 60)
    print("LADI Backend - Migration Fix Script")
    print("=" * 60)
    
    # Check if we're in the backend directory
    if not os.path.exists("app"):
        print("[ERROR] Please run this script from the backend directory")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[WARNING] Virtual environment not detected. Please activate it first.")
        print("Run: source venv/bin/activate (Unix/Linux/macOS) or venv\\Scripts\\activate (Windows)")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Check if migrations directory exists
    migrations_dir = Path("migrations")
    if migrations_dir.exists():
        print("[INFO] Migrations directory found")
        
        # Check database status
        current_migration = check_database_status()
        
        if current_migration is None:
            # Database not initialized, try to upgrade
            print("[INFO] Attempting to initialize database...")
            if run_command("flask db upgrade", "Applying migrations"):
                print("[SUCCESS] Database initialized successfully")
            else:
                print("[ERROR] Failed to initialize database")
                sys.exit(1)
        else:
            print("[INFO] Database is already initialized")
            
            # Check if we're at the latest migration
            if run_command("flask db upgrade", "Upgrading to latest migration"):
                print("[SUCCESS] Database is up to date")
            else:
                print("[ERROR] Failed to upgrade database")
                sys.exit(1)
    else:
        print("[INFO] Migrations directory not found, initializing...")
        if run_command("flask db init", "Initializing migrations"):
            if run_command("flask db migrate -m 'Initial migration'", "Creating initial migration"):
                if run_command("flask db upgrade", "Applying initial migration"):
                    print("[SUCCESS] Database initialized successfully")
                else:
                    print("[ERROR] Failed to apply initial migration")
                    sys.exit(1)
            else:
                print("[ERROR] Failed to create initial migration")
                sys.exit(1)
        else:
            print("[ERROR] Failed to initialize migrations")
            sys.exit(1)
    
    # Create database tables
    print("[INFO] Creating database tables...")
    try:
        from app import create_app, db
        from app.models import User, Evaluation, EvaluationTemplate
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("[SUCCESS] Database tables created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create database tables: {e}")
        sys.exit(1)
    
    # Create upload directories
    print("[INFO] Creating upload directories...")
    upload_dirs = ["uploads", "uploads/reports", "uploads/templates"]
    for dir_path in upload_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("[SUCCESS] Upload directories created")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Database setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the backend server: python run.py")
    print("2. The API will be available at http://localhost:5000")
    print("3. You can now run the frontend setup")

if __name__ == "__main__":
    main()
