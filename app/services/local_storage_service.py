import os
import shutil
import logging
from datetime import datetime, timedelta
from app.config import Config

logger = logging.getLogger(__name__)

class LocalStorageService:
    def __init__(self):
        self.base_path = Config.UPLOAD_FOLDER
        self._ensure_base_directory()
    
    def _ensure_base_directory(self):
        """Ensure the base upload directory exists"""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            logger.info(f"Local storage base directory ensured: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create base directory: {e}")
            raise
    
    def upload_file(self, source_path, file_key):
        """Upload a file to local storage using a key-based path structure"""
        try:
            # Create the local directory structure based on file key
            local_dir = os.path.join(self.base_path, os.path.dirname(file_key))
            os.makedirs(local_dir, exist_ok=True)
            
            # Copy file to local storage with file key as path
            local_file_path = os.path.join(self.base_path, file_key)
            shutil.copy2(source_path, local_file_path)
            
            logger.info(f"Successfully uploaded {source_path} to local storage: {local_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            raise Exception(f"Local upload failed: {e}")
    
    def generate_download_url(self, file_key, expiration_hours=24):
        """Generate a local file URL for file download"""
        try:
            # Return local file URL
            local_url = f"/api/upload/public/download-file/{file_key}"
            logger.info(f"Generated local file URL for {file_key}: {local_url}")
            return local_url
        except Exception as e:
            logger.error(f"Failed to generate local file URL: {e}")
            raise Exception(f"Failed to generate download URL: {e}")
    
    def regenerate_download_url(self, file_key, expiration_hours=24):
        """Regenerate a local file URL"""
        try:
            # Return local file URL
            local_url = f"/api/upload/public/download-file/{file_key}"
            logger.info(f"Regenerated local file URL for {file_key}: {local_url}")
            return local_url
        except Exception as e:
            logger.error(f"Failed to regenerate local file URL: {e}")
            raise Exception(f"Failed to regenerate download URL: {e}")
    
    def delete_file(self, file_key):
        """Delete a file from local storage"""
        try:
            local_file_path = os.path.join(self.base_path, file_key)
            
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
            if not os.path.exists(self.base_path):
                return 0
            
            for root, dirs, files in os.walk(self.base_path):
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
    
    def get_file_size(self, file_key):
        """Get file size from local storage"""
        try:
            local_file_path = os.path.join(self.base_path, file_key)
            
            if os.path.exists(local_file_path):
                return os.path.getsize(local_file_path)
            else:
                logger.warning(f"File not found in local storage: {local_file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            return None
    
    def file_exists(self, file_key):
        """Check if a file exists in local storage"""
        try:
            local_file_path = os.path.join(self.base_path, file_key)
            return os.path.exists(local_file_path)
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
    
    def download_file(self, file_key, destination_path):
        """Download a file from local storage to another local path"""
        try:
            source_path = os.path.join(self.base_path, file_key)
            
            if not os.path.exists(source_path):
                raise Exception(f"Source file not found: {source_path}")
            
            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, destination_path)
            logger.info(f"Successfully downloaded {source_path} to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file from local storage: {e}")
            raise Exception(f"Local download failed: {e}")
    
    def get_file_content(self, file_key):
        """Get file content from local storage"""
        try:
            local_file_path = os.path.join(self.base_path, file_key)
            
            if not os.path.exists(local_file_path):
                raise Exception(f"File not found: {local_file_path}")
            
            with open(local_file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Successfully read file content from local storage: {local_file_path} ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to get file content from local storage: {e}")
            raise Exception(f"Failed to read file content: {e}")
    
    def get_file_path(self, file_key):
        """Get the full local file path for a given file key"""
        return os.path.join(self.base_path, file_key)
    
    def list_files(self, prefix=None):
        """List files in local storage with optional prefix filter"""
        try:
            files = []
            if not os.path.exists(self.base_path):
                return files
            
            for root, dirs, filenames in os.walk(self.base_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, self.base_path)
                    
                    if prefix is None or relative_path.startswith(prefix):
                        files.append({
                            'key': relative_path,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                        })
            
            return files
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
