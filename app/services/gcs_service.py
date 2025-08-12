import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import storage
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound

from ..config import settings

logger = logging.getLogger(__name__)


class GCSService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self):
        self.project_id = settings.google_cloud_project_id
        self.bucket_name = settings.gcs_bucket_name
        self.client = None
        self.bucket = None
        
        if self.project_id:
            self._initialize_client()
            self._ensure_bucket_exists()
    
    def _initialize_client(self):
        """Initialize GCS client with proper authentication."""
        try:
            credentials_path = settings.google_application_credentials
            
            if credentials_path:
                logger.info(f"Using service account credentials: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = storage.Client(credentials=credentials, project=self.project_id)
            else:
                logger.info("Using default credentials")
                self.client = storage.Client(project=self.project_id)
            
            logger.info(f"GCS client initialized for project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None
    
    def _ensure_bucket_exists(self):
        """Ensure the GCS bucket exists."""
        if not self.client:
            return
        
        try:
            self.bucket = self.client.bucket(self.bucket_name)
            
            if not self.bucket.exists():
                logger.info(f"Creating bucket: {self.bucket_name}")
                self.bucket = self.client.create_bucket(self.bucket_name, location="US")
                
                # Set bucket configuration
                self.bucket.versioning_enabled = True
                self.bucket.update()
                
                # Set lifecycle rules
                lifecycle_rule = {
                    "action": {"type": "Delete"},
                    "condition": {
                        "age": 365,  # Delete after 1 year
                        "isLive": True
                    }
                }
                self.bucket.lifecycle_rules = [lifecycle_rule]
                self.bucket.update()
                
                logger.info(f"Created bucket with lifecycle rules: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            self.bucket = None
    
    def save_json(self, data: List[Dict[str, Any]], filename: str, 
                  metadata: Optional[Dict[str, str]] = None) -> bool:
        """Save JSON data to GCS with metadata."""
        if not self.bucket:
            logger.warning("GCS bucket not available")
            return False
        
        try:
            blob_name = f"extractions/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
            blob = self.bucket.blob(blob_name)
            
            # Prepare data for upload
            json_data = json.dumps(data, default=self._json_serializer, indent=2)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Set content type
            blob.content_type = 'application/json'
            
            # Upload data
            blob.upload_from_string(json_data)
            
            logger.info(f"Successfully saved {len(data)} records to GCS: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to GCS: {e}")
            return False
    
    def _json_serializer(self, obj):
        """JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], datetime):
            return [dt.isoformat() for dt in obj]
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def is_available(self) -> bool:
        """Check if GCS service is available."""
        return self.client is not None and self.bucket is not None


# Legacy class for backward compatibility
class CloudStorageService(GCSService):
    """Legacy class for backward compatibility."""
    
    def __init__(self, bucket_name=None, storage_client=None):
        # If called with old parameters, initialize with settings
        if bucket_name and storage_client:
            self.bucket_name = bucket_name
            self.client = storage_client
            self.bucket = storage_client.bucket(bucket_name)
        else:
            super().__init__()