import boto3
import os
import shutil
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config as BotoConfig
from app.config import Config
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = None  # Force local storage mode
        self.bucket_name = None
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Initialize S3 client with credentials from environment"""
        # Force local storage mode - always set s3_client to None
        logger.info("Using local file storage instead of AWS S3")
        self.s3_client = None
        return
    
    def upload_file(self, file_path, s3_key):
        """Upload a file to local storage (simulating S3 key structure)"""
        try:
            # Create the local directory structure based on S3 key
            local_dir = os.path.join(Config.UPLOAD_FOLDER, os.path.dirname(s3_key))
            os.makedirs(local_dir, exist_ok=True)
            
            # Copy file to local storage with S3 key as path
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            shutil.copy2(file_path, local_file_path)
            
            logger.info(f"Successfully uploaded {file_path} to local storage: {local_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            raise Exception(f"Local upload failed: {e}")
    
    def generate_presigned_url(self, s3_key, expiration_hours=24):
        """Generate a local file URL for file download"""
        try:
            # Return local file URL
            local_url = f"/api/upload/public/download-file/{s3_key}"
            logger.info(f"Generated local file URL for {s3_key}: {local_url}")
            return local_url
        except Exception as e:
            logger.error(f"Failed to generate local file URL: {e}")
            raise Exception(f"Failed to generate download URL: {e}")
    
    def regenerate_presigned_url(self, s3_key, expiration_hours=24):
        """Regenerate a local file URL"""
        try:
            # Return local file URL
            local_url = f"/api/upload/public/download-file/{s3_key}"
            logger.info(f"Regenerated local file URL for {s3_key}: {local_url}")
            return local_url
        except Exception as e:
            logger.error(f"Failed to regenerate local file URL: {e}")
            raise Exception(f"Failed to regenerate download URL: {e}")
    
    def delete_file(self, s3_key):
        """Delete a file from local storage"""
        try:
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
                logger.info(f"Successfully deleted local file: {local_file_path}")
                return True
            else:
                logger.warning(f"File does not exist in local storage: {local_file_path}")
                return True  # Consider it "deleted" if it doesn't exist
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
    
    def cleanup_expired_files(self, prefix, max_age_hours=24):
        """Clean up files older than specified hours from local storage"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            # Walk through the upload folder
            upload_folder = Config.UPLOAD_FOLDER
            if not os.path.exists(upload_folder):
                return 0
            
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    if file.startswith(prefix):
                        file_path = os.path.join(root, file)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_time:
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                logger.info(f"Cleaned up expired file: {file_path}")
                            except Exception as e:
                                logger.error(f"Failed to delete expired file {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} expired files from local storage")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired files: {e}")
            return 0
    
    def get_file_size(self, s3_key):
        """Get file size from local storage"""
        try:
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            
            if os.path.exists(local_file_path):
                return os.path.getsize(local_file_path)
            else:
                logger.warning(f"File not found in local storage: {local_file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            return None
    
    def file_exists(self, s3_key):
        """Check if a file exists in local storage"""
        try:
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            return os.path.exists(local_file_path)
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
    
    def download_file(self, s3_key, local_path):
        """Download a file from local storage to another local path"""
        try:
            source_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            
            if not os.path.exists(source_path):
                raise Exception(f"Source file not found: {source_path}")
            
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, local_path)
            logger.info(f"Successfully downloaded {source_path} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file from local storage: {e}")
            raise Exception(f"Local download failed: {e}")
    
    def get_file_content(self, s3_key):
        """Get file content from local storage"""
        try:
            local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
            
            if not os.path.exists(local_file_path):
                raise Exception(f"File not found: {local_file_path}")
            
            with open(local_file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Successfully read file content from local storage: {local_file_path} ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to get file content from local storage: {e}")
            raise Exception(f"Failed to read file content: {e}") 