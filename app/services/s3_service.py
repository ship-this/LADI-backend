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
        self.s3_client = None
        self.bucket_name = Config.AWS_S3_BUCKET
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Initialize S3 client with credentials from environment"""
        try:
            # Check if AWS credentials are configured
            if not all([Config.AWS_ACCESS_KEY_ID, Config.AWS_SECRET_ACCESS_KEY, Config.AWS_S3_BUCKET]):
                logger.warning("AWS credentials not fully configured, falling back to local storage")
                self.s3_client = None
                return
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                region_name=Config.AWS_S3_REGION,
                config=BotoConfig(
                    retries={'max_attempts': 3},
                    connect_timeout=30,
                    read_timeout=60
                )
            )
            
            # Test the connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully initialized S3 client for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.warning("AWS credentials not found, falling back to local storage")
            self.s3_client = None
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                logger.error(f"S3 client initialization failed: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def upload_file(self, file_path, s3_key):
        """Upload a file to S3 or local storage as fallback"""
        try:
            if self.s3_client:
                # Upload to S3
                self.s3_client.upload_file(
                    file_path, 
                    self.bucket_name, 
                    s3_key,
                    ExtraArgs={'ContentType': self._get_content_type(file_path)}
                )
                logger.info(f"Successfully uploaded {file_path} to S3: {s3_key}")
                return True
            else:
                # Fallback to local storage
                local_dir = os.path.join(Config.UPLOAD_FOLDER, os.path.dirname(s3_key))
                os.makedirs(local_dir, exist_ok=True)
                
                local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
                shutil.copy2(file_path, local_file_path)
                
                logger.info(f"Successfully uploaded {file_path} to local storage: {local_file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise Exception(f"Upload failed: {e}")
    
    def _get_content_type(self, file_path):
        """Get content type based on file extension"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or 'application/octet-stream'
    
    def generate_presigned_url(self, s3_key, expiration_hours=24):
        """Generate a presigned URL for file download"""
        try:
            if self.s3_client:
                # Generate S3 presigned URL
                expiration_seconds = int(expiration_hours * 3600)
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration_seconds
                )
                logger.info(f"Generated S3 presigned URL for {s3_key}")
                return presigned_url
            else:
                # Fallback to local file URL
                local_url = f"/api/upload/public/download-file/{s3_key}"
                logger.info(f"Generated local file URL for {s3_key}: {local_url}")
                return local_url
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise Exception(f"Failed to generate download URL: {e}")
    
    def regenerate_presigned_url(self, s3_key, expiration_hours=24):
        """Regenerate a presigned URL for file download"""
        try:
            if self.s3_client:
                # Generate new S3 presigned URL
                expiration_seconds = int(expiration_hours * 3600)
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration_seconds
                )
                logger.info(f"Regenerated S3 presigned URL for {s3_key}")
                return presigned_url
            else:
                # Fallback to local file URL
                local_url = f"/api/upload/public/download-file/{s3_key}"
                logger.info(f"Regenerated local file URL for {s3_key}: {local_url}")
                return local_url
        except Exception as e:
            logger.error(f"Failed to regenerate download URL: {e}")
            raise Exception(f"Failed to regenerate download URL: {e}")
    
    def delete_file(self, s3_key):
        """Delete a file from S3 or local storage"""
        try:
            if self.s3_client:
                # Delete from S3
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Successfully deleted file from S3: {s3_key}")
                return True
            else:
                # Delete from local storage
                local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
                
                if os.path.exists(local_file_path):
                    os.remove(local_file_path)
                    logger.info(f"Successfully deleted local file: {local_file_path}")
                    return True
                else:
                    logger.warning(f"File does not exist in local storage: {local_file_path}")
                    return True  # Consider it "deleted" if it doesn't exist
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
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
        """Get file size from S3 or local storage"""
        try:
            if self.s3_client:
                # Get file size from S3
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return response['ContentLength']
            else:
                # Get file size from local storage
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
        """Check if a file exists in S3 or local storage"""
        try:
            if self.s3_client:
                # Check if file exists in S3
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
            else:
                # Check if file exists in local storage
                local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
                return os.path.exists(local_file_path)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking S3 file existence: {e}")
                return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
    
    def download_file(self, s3_key, local_path):
        """Download a file from S3 or local storage to another local path"""
        try:
            if self.s3_client:
                # Download from S3
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                self.s3_client.download_file(self.bucket_name, s3_key, local_path)
                logger.info(f"Successfully downloaded {s3_key} from S3 to {local_path}")
                return True
            else:
                # Download from local storage
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
            logger.error(f"Failed to download file: {e}")
            raise Exception(f"Download failed: {e}")
    
    def get_file_content(self, s3_key):
        """Get file content from S3 or local storage"""
        try:
            if self.s3_client:
                # Get file content from S3
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                content = response['Body'].read()
                logger.info(f"Successfully read file content from S3: {s3_key} ({len(content)} bytes)")
                return content
            else:
                # Get file content from local storage
                local_file_path = os.path.join(Config.UPLOAD_FOLDER, s3_key)
                
                if not os.path.exists(local_file_path):
                    raise Exception(f"File not found: {local_file_path}")
                
                with open(local_file_path, 'rb') as f:
                    content = f.read()
                
                logger.info(f"Successfully read file content from local storage: {local_file_path} ({len(content)} bytes)")
                return content
        except Exception as e:
            logger.error(f"Failed to get file content: {e}")
            raise Exception(f"Failed to read file content: {e}") 