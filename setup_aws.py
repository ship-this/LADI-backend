#!/usr/bin/env python3
"""
AWS S3 Setup Script for LADI Backend

This script helps you configure AWS S3 credentials for file storage.
"""

import os
import sys

def setup_aws_credentials():
    """Setup AWS S3 credentials"""
    print("=== AWS S3 Setup for LADI Backend ===\n")
    
    print("To use AWS S3 for file storage, you need to:")
    print("1. Create an AWS account (if you don't have one)")
    print("2. Create an S3 bucket")
    print("3. Create an IAM user with S3 permissions")
    print("4. Get the access key and secret key\n")
    
    print("=== Step-by-step instructions ===\n")
    
    print("1. Create S3 Bucket:")
    print("   - Go to AWS S3 Console")
    print("   - Click 'Create bucket'")
    print("   - Choose a unique bucket name (e.g., 'ladi-files-2024')")
    print("   - Select your preferred region")
    print("   - Keep default settings for now")
    print("   - Click 'Create bucket'\n")
    
    print("2. Create IAM User:")
    print("   - Go to AWS IAM Console")
    print("   - Click 'Users' → 'Add user'")
    print("   - Enter username (e.g., 'ladi-s3-user')")
    print("   - Select 'Programmatic access'")
    print("   - Click 'Next: Permissions'\n")
    
    print("3. Attach S3 Policy:")
    print("   - Click 'Attach existing policies directly'")
    print("   - Search for 'AmazonS3FullAccess'")
    print("   - Check the box and click 'Next'")
    print("   - Click 'Create user'\n")
    
    print("4. Get Credentials:")
    print("   - Click on your new user")
    print("   - Go to 'Security credentials' tab")
    print("   - Click 'Create access key'")
    print("   - Copy the Access Key ID and Secret Access Key\n")
    
    print("=== Environment Variables ===\n")
    
    # Get current values
    current_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
    current_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    current_bucket = os.environ.get('AWS_S3_BUCKET', '')
    current_region = os.environ.get('AWS_S3_REGION', 'us-east-1')
    
    print("Current AWS configuration:")
    print(f"AWS_ACCESS_KEY_ID: {'***' + current_access_key[-4:] if current_access_key else 'Not set'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'***' + current_secret_key[-4:] if current_secret_key else 'Not set'}")
    print(f"AWS_S3_BUCKET: {current_bucket or 'Not set'}")
    print(f"AWS_S3_REGION: {current_region}\n")
    
    # Ask for new values
    print("Enter your AWS credentials (press Enter to keep current values):")
    
    access_key = input(f"Access Key ID [{current_access_key}]: ").strip()
    if not access_key:
        access_key = current_access_key
    
    secret_key = input(f"Secret Access Key [{current_secret_key}]: ").strip()
    if not secret_key:
        secret_key = current_secret_key
    
    bucket = input(f"S3 Bucket Name [{current_bucket}]: ").strip()
    if not bucket:
        bucket = current_bucket
    
    region = input(f"S3 Region [{current_region}]: ").strip()
    if not region:
        region = current_region
    
    # Update .env file
    env_file = '.env'
    env_content = ""
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add AWS variables
    lines = env_content.split('\n')
    aws_vars = {
        'AWS_ACCESS_KEY_ID': access_key,
        'AWS_SECRET_ACCESS_KEY': secret_key,
        'AWS_S3_BUCKET': bucket,
        'AWS_S3_REGION': region
    }
    
    updated_lines = []
    aws_vars_found = set()
    
    for line in lines:
        if line.startswith('AWS_'):
            for var_name in aws_vars:
                if line.startswith(f'{var_name}='):
                    updated_lines.append(f'{var_name}={aws_vars[var_name]}')
                    aws_vars_found.add(var_name)
                    break
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add missing AWS variables
    for var_name, var_value in aws_vars.items():
        if var_name not in aws_vars_found:
            updated_lines.append(f'{var_name}={var_value}')
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"\n✅ AWS credentials updated in {env_file}")
    print("\n=== Next Steps ===")
    print("1. Restart your Flask application")
    print("2. Test file upload to verify S3 integration")
    print("3. Check logs for S3 connection messages")
    
    if not all([access_key, secret_key, bucket]):
        print("\n⚠️  Warning: Some AWS credentials are missing.")
        print("   The application will fall back to local storage.")
        print("   Set all AWS credentials to use S3 storage.")

def test_s3_connection():
    """Test S3 connection"""
    print("\n=== Testing S3 Connection ===")
    
    try:
        from app.services.s3_service import S3Service
        storage_service = S3Service()
        
        if storage_service.s3_client:
            print("✅ S3 client initialized successfully")
            print(f"✅ Connected to bucket: {storage_service.bucket_name}")
            return True
        else:
            print("❌ S3 client not initialized - falling back to local storage")
            print("   Check your AWS credentials in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error testing S3 connection: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_s3_connection()
    else:
        setup_aws_credentials()
