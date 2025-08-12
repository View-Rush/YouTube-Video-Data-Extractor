import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application Settings
    app_name: str = Field(default="YouTube Data Extractor", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    app_environment: str = Field(default="development", env="APP_ENVIRONMENT")
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Google Cloud Configuration
    google_cloud_project_id: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT_ID")
    gcs_bucket_name: str = Field(default="youtube-data-sri-lanka", env="GCS_BUCKET_NAME")
    bigquery_dataset_id: str = Field(default="youtube_analytics", env="BIGQUERY_DATASET_ID")
    bigquery_table_id: str = Field(default="video_data", env="BIGQUERY_TABLE_ID")
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # YouTube API Configuration
    youtube_api_keys: List[str] = Field(default_factory=list)
    daily_limit_per_key: int = Field(default=10000, env="DAILY_LIMIT_PER_KEY")
    requests_per_hour_limit: int = Field(default=100, env="REQUESTS_PER_HOUR_LIMIT")
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    batch_size: int = Field(default=50, env="BATCH_SIZE")
    cache_ttl_hours: int = Field(default=24, env="CACHE_TTL_HOURS")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    
    # Data Quality Settings
    min_sri_lanka_score: float = Field(default=0.3, env="MIN_SRI_LANKA_SCORE")
    min_quality_score: float = Field(default=0.2, env="MIN_QUALITY_SCORE")
    duplicate_check_enabled: bool = Field(default=True, env="DUPLICATE_CHECK_ENABLED")
    spam_filter_enabled: bool = Field(default=True, env="SPAM_FILTER_ENABLED")
    
    # Monitoring Settings
    health_check_interval: int = Field(default=300, env="HEALTH_CHECK_INTERVAL")
    log_rotation_size: str = Field(default="100MB", env="LOG_ROTATION_SIZE")
    metrics_retention_days: int = Field(default=30, env="METRICS_RETENTION_DAYS")
    
    # Security Settings
    api_rate_limit: int = Field(default=1000, env="API_RATE_LIMIT")
    allowed_origins: List[str] = Field(default=["localhost"], env="ALLOWED_ORIGINS")
    enable_api_authentication: bool = Field(default=False, env="ENABLE_API_AUTHENTICATION")
    
    # Database Settings
    database_path: str = Field(default="data/youtube_cache.db", env="DATABASE_PATH")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"
    
    def load_youtube_api_keys(self) -> List[str]:
        """Load YouTube API keys from environment variables."""
        keys = []
        
        # Load from environment variables (up to 20 keys)
        for i in range(1, 4):
            key = os.environ.get(f'YOUTUBE_API_KEY_{i}')
            if key and key.strip() and key not in ['your-api-key-here', 'YOUR_YOUTUBE_API_KEY_HERE']:
                keys.append(key.strip())
        
        # Remove duplicates while preserving order
        unique_keys = []
        for key in keys:
            if key not in unique_keys and self._validate_api_key_format(key):
                unique_keys.append(key)
        
        return unique_keys
    
    def _validate_api_key_format(self, key: str) -> bool:
        """Basic validation of API key format."""
        return bool(key and len(key) == 39 and key.startswith('AIza') and 
                   key.replace('-', '').replace('_', '').isalnum())
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_environment.lower() == "development"


# Global settings instance
settings = Settings()

# Load YouTube API keys on startup
settings.youtube_api_keys = settings.load_youtube_api_keys()