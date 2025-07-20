import os
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field
from google.cloud import storage, bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import aiohttp
import uvicorn
from contextlib import asynccontextmanager
import schedule
import threading
from queue import Queue
import random
import hashlib
from concurrent.futures import ThreadPoolExecutor
import re
from dataclasses import dataclass
import sqlite3
import backoff
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import psutil
import threading
from queue import Queue
import random
import hashlib
from concurrent.futures import ThreadPoolExecutor

# Configure logging with better formatting
os.makedirs('logs', exist_ok=True)

# Create handlers
file_handler = logging.FileHandler('logs/youtube_extractor.log')
error_handler = logging.FileHandler('logs/error.log')
error_handler.setLevel(logging.ERROR)  # Set level after creation
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        error_handler,
        console_handler
    ]
)
logger = logging.getLogger(__name__)

# Analytics and metrics tracking
@dataclass
class APIKeyMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    quota_exceeded_count: int = 0
    last_used: Optional[datetime] = None
    daily_reset_time: datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

@dataclass
class ExtractionMetrics:
    total_videos_extracted: int = 0
    total_extraction_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    start_time: datetime = datetime.now()
    last_successful_extraction: Optional[datetime] = None

# Enhanced Pydantic models
class ExtractionConfig(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=50, ge=1, le=500)
    region_code: str = Field(default="LK", description="Region code (LK for Sri Lanka)")
    published_after: Optional[str] = Field(None, description="Published after date (ISO format)")
    published_before: Optional[str] = Field(None, description="Published before date (ISO format)")
    order: str = Field(default="relevance", description="Order of results: relevance, date, rating, viewCount, title")
    duration: Optional[str] = Field(None, description="Duration filter: short, medium, long")
    video_definition: Optional[str] = Field(None, description="Video definition: high, standard")

class ExtractionStatus(BaseModel):
    status: str
    message: str
    videos_processed: int
    current_api_key_index: int
    api_key_usage: Dict[str, int]
    last_extraction: Optional[str]
    extraction_metrics: Dict[str, Any]
    current_search_config: Optional[Dict[str, Any]]
    api_keys: List[Dict[str, Any]]
    uptime: str
    stats: Dict[str, Any]

class VideoData(BaseModel):
    video_id: str
    title: str
    description: str
    published_at: str
    channel_id: str
    channel_title: str
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    tags: List[str]
    category_id: str
    thumbnail_url: str
    language: str
    location: Optional[str]
    extraction_date: str
    search_query: str
    video_url: str
    is_sri_lankan_content: bool
    content_score: float

class AnalyticsResponse(BaseModel):
    summary: List[Dict[str, Any]]
    trending_videos: List[Dict[str, Any]]
    channel_analytics: List[Dict[str, Any]]
    temporal_analytics: List[Dict[str, Any]]

# Enhanced Global variables
extraction_status = {
    "is_running": False,
    "videos_processed": 0,
    "last_extraction": None,
    "current_message": "Ready to start extraction",
    "start_time": datetime.now(),
    "current_search_config": None,
    "extraction_cycles": 0,
    "successful_cycles": 0,
    "failed_cycles": 0,
    "total_api_requests": 0,
    "total_errors": 0
}

class YouTubeExtractor:
    def __init__(self):
        # Configuration
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
        self.bucket_name = os.environ.get('GCS_BUCKET_NAME', 'youtube-data-sri-lanka')
        self.dataset_id = os.environ.get('BIGQUERY_DATASET_ID', 'youtube_analytics')
        self.table_id = os.environ.get('BIGQUERY_TABLE_ID', 'video_data')
        
        # Enhanced API key management
        self.api_keys = self.load_api_keys()
        self.current_key_index = 0
        self.api_key_metrics = {key: APIKeyMetrics() for key in self.api_keys}
        self.daily_limit_per_key = 10000  # YouTube API quota limit
        self.requests_per_hour_limit = 100  # Conservative rate limiting
        self.last_reset = datetime.now().date()
        
        # Initialize Google Cloud clients
        self.init_google_cloud_clients()
        
        # Initialize local database for caching and deduplication
        self.init_local_database()
        
        # Enhanced search terms and content detection
        self.sri_lanka_indicators = {
            'locations': [
                'Sri Lanka', 'Ceylon', 'Colombo', 'Kandy', 'Galle', 'Jaffna', 'Negombo', 
                'Anuradhapura', 'Polonnaruwa', 'Sigiriya', 'Ella', 'Nuwara Eliya', 
                'Trincomalee', 'Batticaloa', 'Matara', 'Ratnapura', 'Kurunegala',
                'Badulla', 'Monaragala', 'Hambantota', 'Kotte', 'Dehiwala', 'Moratuwa',
                'Kalutara', 'Puttalam', 'Chilaw', 'Kegalle', 'Balangoda', 'Bandarawela'
            ],
            'cultural_terms': [
                'සිංහල', 'sinhala', 'sinhalese', 'tamil', 'தமிழ்', 'buddhist', 'vesak',
                'poson', 'esala', 'kataragama', 'adam\'s peak', 'sri pada', 'tooth relic',
                'kandy perahera', 'ayurveda', 'curry', 'roti', 'hoppers', 'kottu'
            ],
            'categories': [
                'travel', 'culture', 'food', 'music', 'news', 'tourism', 'history', 
                'nature', 'festival', 'cricket', 'politics', 'education', 'technology',
                'dance', 'art', 'buddhism', 'temple', 'beach', 'wildlife', 'tea',
                'spices', 'gems', 'ayurveda', 'traditional', 'modern'
            ]
        }
        
        # Advanced search queries for comprehensive coverage
        self.search_strategies = [
            {'query': 'Sri Lanka', 'order': 'relevance', 'max_results': 50},
            {'query': 'Sri Lanka', 'order': 'date', 'max_results': 50},
            {'query': 'Sri Lanka', 'order': 'viewCount', 'max_results': 25},
            {'query': 'Ceylon', 'order': 'relevance', 'max_results': 25},
            {'query': 'Lanka', 'order': 'date', 'max_results': 25},
        ]
        
        # Content scoring keywords
        self.high_value_keywords = [
            'sri lanka', 'ceylon', 'colombo', 'kandy', 'sigiriya', 'ella',
            'galle', 'tourism', 'travel', 'culture', 'food', 'temple'
        ]
        
        # Processing metrics
        self.extraction_metrics = ExtractionMetrics()
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        logger.info("YouTubeExtractor initialized successfully")

    def load_api_keys(self) -> List[str]:
        """Load YouTube API keys from environment variables with fallback to config file"""
        keys = []
        
        # Load from environment variables (up to 20 keys)
        logger.info("Loading API keys from environment variables...")
        for i in range(1, 21):
            key = os.environ.get(f'YOUTUBE_API_KEY_{i}')
            if key and key.strip() and key not in ['your-api-key-here', 'YOUR_YOUTUBE_API_KEY_HERE']:
                keys.append(key.strip())
                logger.info(f"Loaded API key {i} from environment")
        
        # Fallback: Try to load from config file only if no env vars found
        if not keys:
            logger.info("No API keys found in environment, trying config file...")
            try:
                with open('api_keys.json', 'r') as f:
                    config = json.load(f)
                    file_keys = config.get('youtube_api_keys', [])
                    for key in file_keys:
                        if key and key.strip() and key not in ['YOUR_YOUTUBE_API_KEY_1', 'YOUR_YOUTUBE_API_KEY_2', 'YOUR_YOUTUBE_API_KEY_3']:
                            keys.append(key.strip())
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.info(f"Config file not available: {e}")
        
        # Remove duplicates while preserving order
        unique_keys = []
        for key in keys:
            if key not in unique_keys:
                unique_keys.append(key)
        
        if not unique_keys:
            logger.error("No valid YouTube API keys found!")
            logger.error("Please set environment variables YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, etc. in your .env file")
            logger.error("Example: YOUTUBE_API_KEY_1=AIzaSyYourActualAPIKeyHere")
            raise ValueError("No valid YouTube API keys found. Please set YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2, etc. in your .env file")
        
        # Validate API keys format
        validated_keys = []
        for key in unique_keys:
            if self.validate_api_key_format(key):
                validated_keys.append(key)
            else:
                logger.warning(f"Invalid API key format detected, skipping: {key[:10]}...")
        
        if not validated_keys:
            raise ValueError("No valid API keys found after validation")
        
        logger.info(f"Loaded and validated {len(validated_keys)} API keys")
        return validated_keys

    def validate_api_key_format(self, key: str) -> bool:
        """Basic validation of API key format"""
        # YouTube API keys are typically 39 characters long and start with "AIza"
        return bool(key and len(key) == 39 and key.startswith('AIza') and key.replace('-', '').replace('_', '').isalnum())

    def init_local_database(self):
        """Initialize SQLite database for local caching and deduplication"""
        try:
            os.makedirs('data', exist_ok=True)
            self.db_path = 'data/youtube_cache.db'
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS processed_videos (
                        video_id TEXT PRIMARY KEY,
                        title TEXT,
                        channel_id TEXT,
                        published_at TEXT,
                        processed_at TEXT,
                        search_query TEXT,
                        view_count INTEGER,
                        is_sri_lankan BOOLEAN
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS api_usage_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key_hash TEXT,
                        request_type TEXT,
                        timestamp TEXT,
                        success BOOLEAN,
                        quota_cost INTEGER,
                        error_message TEXT
                    )
                ''')
                
                # Create indexes separately (SQLite doesn't allow multiple statements in one execute)
                conn.execute('CREATE INDEX IF NOT EXISTS idx_video_id ON processed_videos(video_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_videos(processed_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_log(timestamp)')
                
            logger.info("Local database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize local database: {e}")
            raise

    def is_video_processed(self, video_id: str) -> bool:
        """Check if video has been processed recently"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT processed_at FROM processed_videos WHERE video_id = ?",
                    (video_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    processed_at = datetime.fromisoformat(result[0])
                    # Consider video fresh if processed within last 7 days
                    return (datetime.now() - processed_at).days < 7
                return False
        except Exception as e:
            logger.error(f"Error checking processed videos: {e}")
            return False

    def log_api_usage(self, api_key: str, request_type: str, success: bool, quota_cost: int = 1, error_message: str = None):
        """Log API usage for monitoring and analytics"""
        try:
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO api_usage_log 
                    (api_key_hash, request_type, timestamp, success, quota_cost, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (api_key_hash, request_type, datetime.now().isoformat(), success, quota_cost, error_message))
                
            # Update metrics
            if api_key in self.api_key_metrics:
                metrics = self.api_key_metrics[api_key]
                metrics.total_requests += 1
                metrics.last_used = datetime.now()
                
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    if 'quota' in (error_message or '').lower():
                        metrics.quota_exceeded_count += 1
                        
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")

    def init_google_cloud_clients(self):
        """Initialize Google Cloud Storage and BigQuery clients with enhanced error handling"""
        try:
            # Initialize with service account or default credentials
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            
            if credentials_path and os.path.exists(credentials_path):
                logger.info(f"Using service account credentials from: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.storage_client = storage.Client(credentials=credentials, project=self.project_id)
                self.bigquery_client = bigquery.Client(credentials=credentials, project=self.project_id)
            else:
                if credentials_path:
                    logger.warning(f"Service account file not found at: {credentials_path}")
                logger.info("Attempting to use default credentials or environment-based authentication")
                
                # Try to initialize without explicit credentials (will use default/environment auth)
                try:
                    self.storage_client = storage.Client(project=self.project_id) if self.project_id else None
                    self.bigquery_client = bigquery.Client(project=self.project_id) if self.project_id else None
                    logger.info("Successfully initialized with default credentials")
                except Exception as auth_error:
                    logger.warning(f"Could not initialize with default credentials: {auth_error}")
                    logger.warning("Google Cloud features will be disabled. Set up service account or default credentials to enable.")
                    self.storage_client = None
                    self.bigquery_client = None
                    return
            
            # Test the connections if clients were created
            if self.bigquery_client:
                try:
                    # Test BigQuery connection
                    datasets = list(self.bigquery_client.list_datasets(max_results=1))
                    logger.info("BigQuery connection successful")
                except Exception as e:
                    logger.warning(f"BigQuery connection test failed: {e}")
                    logger.warning("BigQuery features will be limited")
            
            if self.storage_client:
                try:
                    # Test GCS connection
                    buckets = list(self.storage_client.list_buckets(max_results=1))
                    logger.info("Google Cloud Storage connection successful")
                except Exception as e:
                    logger.warning(f"GCS connection test failed: {e}")
                    logger.warning("Cloud storage features will be limited")
            
            # Create resources if they don't exist and clients are available
            if self.storage_client:
                self.create_bucket_if_not_exists()
            if self.bigquery_client:
                self.create_enhanced_bigquery_resources()
            
            if self.storage_client or self.bigquery_client:
                logger.info("Google Cloud clients initialized successfully")
            else:
                logger.warning("No Google Cloud clients initialized - running in local-only mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud clients: {e}")
            logger.warning("Google Cloud features will be disabled")
            # Don't raise here, allow the application to continue with limited functionality
            self.storage_client = None
            self.bigquery_client = None

    def create_bucket_if_not_exists(self):
        """Create GCS bucket if it doesn't exist with enhanced configuration"""
        if not self.storage_client:
            logger.warning("Storage client not available, skipping bucket creation")
            return
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                # Create bucket with lifecycle management
                bucket = self.storage_client.create_bucket(
                    self.bucket_name,
                    location="US"  # Multi-region for better availability
                )
                
                # Set lifecycle rules to manage storage costs
                lifecycle_rule = {
                    "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
                    "condition": {"age": 90}  # Move to coldline after 90 days
                }
                bucket.lifecycle_rules = [lifecycle_rule]
                bucket.patch()
                
                logger.info(f"Created bucket with lifecycle rules: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")

    def create_enhanced_bigquery_resources(self):
        """Create BigQuery dataset and table with enhanced schema and partitioning"""
        if not self.bigquery_client:
            logger.warning("BigQuery client not available, skipping resource creation")
            return
            
        try:
            # Create dataset with enhanced configuration
            dataset_ref = self.bigquery_client.dataset(self.dataset_id)
            try:
                dataset = self.bigquery_client.get_dataset(dataset_ref)
                logger.info(f"Dataset already exists: {self.dataset_id}")
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                dataset.description = "YouTube video data for Sri Lankan content analysis"
                
                # Set default table expiration (optional)
                # dataset.default_table_expiration_ms = 1000 * 60 * 60 * 24 * 365 * 2  # 2 years
                
                dataset = self.bigquery_client.create_dataset(dataset, exists_ok=True)
                logger.info(f"Created dataset: {self.dataset_id}")

            # Create main video table with enhanced schema
            self.create_videos_table(dataset_ref)
            
            # Create analytics tables
            self.create_analytics_tables(dataset_ref)
            
        except Exception as e:
            logger.error(f"Error creating BigQuery resources: {e}")

    def create_videos_table(self, dataset_ref):
        """Create the main videos table with partitioning and clustering"""
        table_ref = dataset_ref.table(self.table_id)
        
        try:
            table = self.bigquery_client.get_table(table_ref)
            logger.info(f"Table already exists: {self.table_id}")
            return
        except Exception:
            pass
        
        # Enhanced schema with more fields
        schema = [
            bigquery.SchemaField("video_id", "STRING", mode="REQUIRED", description="YouTube video ID"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED", description="Video title"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE", description="Video description (truncated)"),
            bigquery.SchemaField("published_at", "TIMESTAMP", mode="REQUIRED", description="Video publication timestamp"),
            bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED", description="YouTube channel ID"),
            bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED", description="Channel name"),
            bigquery.SchemaField("view_count", "INTEGER", mode="NULLABLE", description="View count at extraction time"),
            bigquery.SchemaField("like_count", "INTEGER", mode="NULLABLE", description="Like count at extraction time"),
            bigquery.SchemaField("comment_count", "INTEGER", mode="NULLABLE", description="Comment count at extraction time"),
            bigquery.SchemaField("duration", "STRING", mode="NULLABLE", description="Video duration in ISO 8601 format"),
            bigquery.SchemaField("duration_seconds", "INTEGER", mode="NULLABLE", description="Video duration in seconds"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED", description="Video tags"),
            bigquery.SchemaField("category_id", "STRING", mode="NULLABLE", description="YouTube category ID"),
            bigquery.SchemaField("category_name", "STRING", mode="NULLABLE", description="YouTube category name"),
            bigquery.SchemaField("thumbnail_url", "STRING", mode="NULLABLE", description="High quality thumbnail URL"),
            bigquery.SchemaField("language", "STRING", mode="NULLABLE", description="Video language"),
            bigquery.SchemaField("detected_location", "STRING", mode="NULLABLE", description="Detected Sri Lankan location"),
            bigquery.SchemaField("extraction_date", "TIMESTAMP", mode="REQUIRED", description="When the data was extracted"),
            bigquery.SchemaField("search_query", "STRING", mode="REQUIRED", description="Search query used to find the video"),
            bigquery.SchemaField("video_url", "STRING", mode="REQUIRED", description="Full YouTube URL"),
            bigquery.SchemaField("is_sri_lankan_content", "BOOLEAN", mode="REQUIRED", description="Whether content is Sri Lankan"),
            bigquery.SchemaField("content_score", "FLOAT", mode="NULLABLE", description="Sri Lankan content relevance score"),
            bigquery.SchemaField("thumbnail_downloaded", "BOOLEAN", mode="NULLABLE", description="Whether thumbnail was saved to GCS"),
            bigquery.SchemaField("last_updated", "TIMESTAMP", mode="NULLABLE", description="Last time stats were updated"),
            
            # Additional analytics fields
            bigquery.SchemaField("engagement_rate", "FLOAT", mode="NULLABLE", description="Calculated engagement rate"),
            bigquery.SchemaField("views_per_day", "FLOAT", mode="NULLABLE", description="Average views per day since publication"),
            bigquery.SchemaField("subscriber_count", "INTEGER", mode="NULLABLE", description="Channel subscriber count at extraction"),
            bigquery.SchemaField("video_count", "INTEGER", mode="NULLABLE", description="Total videos in channel"),
        ]
        
        # Create table with partitioning and clustering
        table = bigquery.Table(table_ref, schema=schema)
        
        # Partition by extraction date for better query performance
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="extraction_date",
            expiration_ms=None  # No automatic expiration
        )
        
        # Cluster by commonly queried fields
        table.clustering_fields = ["is_sri_lankan_content", "channel_id", "category_id"]
        
        table.description = "Main table for YouTube video data with Sri Lankan content focus"
        
        table = self.bigquery_client.create_table(table, exists_ok=True)
        logger.info(f"Created partitioned and clustered table: {self.table_id}")

    def create_analytics_tables(self, dataset_ref):
        """Create additional analytics tables"""
        try:
            # Channel analytics table
            channel_table_ref = dataset_ref.table("channel_analytics")
            try:
                self.bigquery_client.get_table(channel_table_ref)
            except Exception:
                channel_schema = [
                    bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("total_videos", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("total_views", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("total_likes", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("avg_engagement_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("subscriber_count", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("created_date", "TIMESTAMP", mode="NULLABLE"),
                    bigquery.SchemaField("last_video_date", "TIMESTAMP", mode="NULLABLE"),
                    bigquery.SchemaField("is_sri_lankan_channel", "BOOLEAN", mode="NULLABLE"),
                    bigquery.SchemaField("content_categories", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("analysis_date", "TIMESTAMP", mode="REQUIRED"),
                ]
                
                channel_table = bigquery.Table(channel_table_ref, schema=channel_schema)
                channel_table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="analysis_date"
                )
                self.bigquery_client.create_table(channel_table, exists_ok=True)
                logger.info("Created channel analytics table")
            
            # Daily summary table
            summary_table_ref = dataset_ref.table("daily_summary")
            try:
                self.bigquery_client.get_table(summary_table_ref)
            except Exception:
                summary_schema = [
                    bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                    bigquery.SchemaField("total_videos_extracted", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("unique_channels", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("total_views", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("avg_engagement_rate", "FLOAT", mode="NULLABLE"),
                    bigquery.SchemaField("top_categories", "STRING", mode="REPEATED"),
                    bigquery.SchemaField("api_requests_made", "INTEGER", mode="NULLABLE"),
                    bigquery.SchemaField("extraction_cycles", "INTEGER", mode="NULLABLE"),
                ]
                
                summary_table = bigquery.Table(summary_table_ref, schema=summary_schema)
                self.bigquery_client.create_table(summary_table, exists_ok=True)
                logger.info("Created daily summary table")
                
        except Exception as e:
            logger.error(f"Error creating analytics tables: {e}")

    def reset_daily_usage_if_needed(self):
        """Reset API key usage counters daily with proper metrics tracking"""
        current_date = datetime.now().date()
        if current_date > self.last_reset:
            # Reset counters for each key
            for key in self.api_keys:
                if key in self.api_key_metrics:
                    metrics = self.api_key_metrics[key]
                    metrics.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    # Keep cumulative totals, just reset daily tracking if needed
            
            self.last_reset = current_date
            logger.info(f"Daily API usage tracking reset for {len(self.api_keys)} keys")

    def get_youtube_client(self):
        """Get YouTube API client with enhanced key rotation and error handling"""
        self.reset_daily_usage_if_needed()
        
        max_attempts = len(self.api_keys)
        attempts = 0
        
        while attempts < max_attempts:
            current_key = self.api_keys[self.current_key_index]
            metrics = self.api_key_metrics[current_key]
            
            # Check if current key is still viable
            if self.is_key_available(current_key):
                try:
                    # Test the key with a simple request
                    youtube = build('youtube', 'v3', developerKey=current_key)
                    # Record that we're using this key
                    metrics.last_used = datetime.now()
                    return youtube
                except Exception as e:
                    logger.warning(f"Failed to create client with key {self.current_key_index}: {e}")
                    metrics.failed_requests += 1
                    self.rotate_api_key()
                    attempts += 1
            else:
                logger.info(f"Key {self.current_key_index} not available, rotating")
                self.rotate_api_key()
                attempts += 1
        
        raise Exception("All API keys are unavailable or have exceeded their quota")

    def is_key_available(self, api_key: str) -> bool:
        """Check if an API key is available for use"""
        if api_key not in self.api_key_metrics:
            return True
            
        metrics = self.api_key_metrics[api_key]
        
        # Check daily quota
        if metrics.total_requests >= self.daily_limit_per_key:
            return False
        
        # Check if key had too many recent failures
        if metrics.failed_requests > 0 and metrics.total_requests > 0:
            failure_rate = metrics.failed_requests / metrics.total_requests
            if failure_rate > 0.5:  # More than 50% failure rate
                return False
        
        # Check quota exceeded count
        if metrics.quota_exceeded_count > 3:  # Too many quota violations
            return False
        
        return True

    def rotate_api_key(self):
        """Enhanced API key rotation with availability checking"""
        original_index = self.current_key_index
        rotated = False
        
        for _ in range(len(self.api_keys)):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            current_key = self.api_keys[self.current_key_index]
            
            if self.is_key_available(current_key):
                logger.info(f"Rotated to API key index: {self.current_key_index}")
                rotated = True
                break
        
        if not rotated:
            logger.error("No available API keys found after rotation")
            # Reset to original and try to continue with warnings
            self.current_key_index = original_index
            raise Exception("All API keys have reached their daily quota limit or are unavailable")

    @backoff.on_exception(
        backoff.expo,
        (HttpError, Exception),
        max_tries=3,
        max_time=300
    )
    async def search_videos(self, query: str, max_results: int = 50, 
                          published_after: str = None, published_before: str = None,
                          order: str = 'relevance') -> List[Dict]:
        """Enhanced video search with better error handling and filtering"""
        try:
            youtube = self.get_youtube_client()
            current_key = self.api_keys[self.current_key_index]
            
            # Enhanced search parameters
            search_params = {
                'q': self.optimize_search_query(query),
                'part': 'snippet',
                'type': 'video',
                'maxResults': min(max_results, 50),
                'regionCode': 'LK',
                'relevanceLanguage': 'en',
                'order': order,
                'videoEmbeddable': 'true',  # Only embeddable videos
                'videoSyndicated': 'true',  # Only syndicated videos
                'safeSearch': 'moderate'
            }
            
            # Add date filters if provided
            if published_after:
                try:
                    search_params['publishedAfter'] = datetime.fromisoformat(published_after.replace('Z', '+00:00')).isoformat() + 'Z'
                except ValueError:
                    search_params['publishedAfter'] = published_after
            
            if published_before:
                try:
                    search_params['publishedBefore'] = datetime.fromisoformat(published_before.replace('Z', '+00:00')).isoformat() + 'Z'
                except ValueError:
                    search_params['publishedBefore'] = published_before
            
            logger.info(f"Searching videos with query: {search_params['q']}, max_results: {max_results}")
            
            # Execute search
            search_response = youtube.search().list(**search_params).execute()
            
            # Log API usage
            self.log_api_usage(current_key, 'search', True, 100)  # Search costs 100 quota units
            
            if not search_response.get('items'):
                logger.info(f"No videos found for query: {query}")
                return []
            
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Filter out already processed videos
            new_video_ids = [vid for vid in video_ids if not self.is_video_processed(vid)]
            
            if not new_video_ids:
                logger.info("All found videos have been processed recently")
                return []
            
            logger.info(f"Found {len(video_ids)} videos, {len(new_video_ids)} are new")
            
            # Get detailed video information in batches
            videos = []
            batch_size = 50
            
            for i in range(0, len(new_video_ids), batch_size):
                batch_ids = new_video_ids[i:i + batch_size]
                
                videos_response = youtube.videos().list(
                    part='snippet,statistics,contentDetails,status,localizations',
                    id=','.join(batch_ids)
                ).execute()
                
                # Log API usage for videos call
                self.log_api_usage(current_key, 'videos', True, 1)  # Videos.list costs 1 quota unit per call
                
                # Get channel information for better analysis
                channel_ids = list(set([item['snippet']['channelId'] for item in videos_response['items']]))
                channels_data = {}
                
                if channel_ids:
                    try:
                        channels_response = youtube.channels().list(
                            part='snippet,statistics,brandingSettings',
                            id=','.join(channel_ids[:50])  # API limit
                        ).execute()
                        
                        self.log_api_usage(current_key, 'channels', True, 1)
                        
                        channels_data = {
                            channel['id']: channel 
                            for channel in channels_response.get('items', [])
                        }
                    except Exception as e:
                        logger.warning(f"Failed to get channel data: {e}")
                
                # Process videos
                for item in videos_response['items']:
                    try:
                        channel_data = channels_data.get(item['snippet']['channelId'], {})
                        video_data = self.extract_enhanced_video_data(item, query, channel_data)
                        
                        # Only include videos that meet our criteria
                        if self.is_relevant_sri_lankan_content(video_data):
                            videos.append(video_data)
                            
                            # Mark as processed
                            self.mark_video_processed(video_data)
                            
                    except Exception as e:
                        logger.error(f"Error extracting video data for {item.get('id', 'unknown')}: {e}")
                        continue
            
            logger.info(f"Successfully extracted {len(videos)} relevant videos for query: {query}")
            return videos
            
        except HttpError as e:
            current_key = self.api_keys[self.current_key_index]
            error_message = str(e)
            
            # Log API error
            self.log_api_usage(current_key, 'search', False, 0, error_message)
            
            if e.resp.status == 403:
                if 'quota' in error_message.lower():
                    logger.warning(f"API key {self.current_key_index} quota exceeded, rotating")
                    self.api_key_metrics[current_key].quota_exceeded_count += 1
                    self.rotate_api_key()
                    # Retry with new key
                    return await self.search_videos(query, max_results, published_after, published_before, order)
                else:
                    logger.error(f"API access denied: {e}")
                    raise HTTPException(status_code=403, detail=f"YouTube API access denied: {e}")
            elif e.resp.status == 400:
                logger.error(f"Bad request to YouTube API: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid request parameters: {e}")
            else:
                logger.error(f"YouTube API error: {e}")
                raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
                
        except Exception as e:
            current_key = self.api_keys[self.current_key_index]
            self.log_api_usage(current_key, 'search', False, 0, str(e))
            logger.error(f"Unexpected error searching videos: {e}")
            raise HTTPException(status_code=500, detail=f"Error searching videos: {e}")

    def optimize_search_query(self, query: str) -> str:
        """Optimize search query for better Sri Lankan content discovery"""
        # If query doesn't contain Sri Lankan indicators, add them
        sri_lankan_terms = ['sri lanka', 'ceylon', 'lk', 'lanka']
        
        query_lower = query.lower()
        has_sri_lankan_term = any(term in query_lower for term in sri_lankan_terms)
        
        if not has_sri_lankan_term:
            # Add Sri Lanka to the query for better targeting
            optimized_query = f"{query} Sri Lanka"
        else:
            optimized_query = query
        
        # Remove common spam terms
        spam_terms = ['fake', 'scam', 'clickbait', '18+', 'xxx']
        for term in spam_terms:
            optimized_query = optimized_query.replace(term, '')
        
        return optimized_query.strip()

    def is_relevant_sri_lankan_content(self, video_data: Dict) -> bool:
        """Determine if video content is relevant to Sri Lanka"""
        content_score = video_data.get('content_score', 0)
        
        # Basic threshold
        if content_score < 0.3:
            return False
        
        # Additional quality checks
        title = video_data.get('title', '').lower()
        description = video_data.get('description', '').lower()
        
        # Check for spam indicators
        spam_indicators = ['free money', 'get rich quick', '100% guaranteed', 'click here', 'subscribe for money']
        if any(spam in title or spam in description for spam in spam_indicators):
            return False
        
        # Check minimum engagement
        view_count = video_data.get('view_count', 0)
        like_count = video_data.get('like_count', 0)
        
        if view_count < 10:  # Very low view count might indicate poor quality
            return False
        
        return True

    def mark_video_processed(self, video_data: Dict):
        """Mark video as processed in local database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO processed_videos 
                    (video_id, title, channel_id, published_at, processed_at, search_query, view_count, is_sri_lankan)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data['video_id'],
                    video_data['title'][:200],  # Truncate long titles
                    video_data['channel_id'],
                    video_data['published_at'],
                    datetime.now().isoformat(),
                    video_data['search_query'],
                    video_data['view_count'],
                    video_data['is_sri_lankan_content']
                ))
        except Exception as e:
            logger.error(f"Error marking video as processed: {e}")

    def extract_enhanced_video_data(self, item: Dict, search_query: str, channel_data: Dict = None) -> Dict:
        """Extract comprehensive data from YouTube video item with enhanced analysis"""
        snippet = item['snippet']
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})
        status = item.get('status', {})
        
        # Basic video information
        video_id = item['id']
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        
        # Parse duration
        duration_iso = content_details.get('duration', '')
        duration_seconds = self.parse_duration_to_seconds(duration_iso)
        
        # Detect Sri Lankan content and calculate relevance score
        content_analysis = self.analyze_sri_lankan_content(title, description, snippet.get('tags', []))
        
        # Extract numeric statistics with fallbacks
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        # Calculate engagement metrics
        engagement_rate = self.calculate_engagement_rate(view_count, like_count, comment_count)
        
        # Get channel information
        channel_info = self.extract_channel_info(snippet, channel_data)
        
        # Calculate content quality score
        quality_score = self.calculate_content_quality_score(
            view_count, like_count, comment_count, len(title), len(description), duration_seconds
        )
        
        # Determine publication date and calculate age
        published_at = snippet.get('publishedAt', '')
        video_age_days = self.calculate_video_age_days(published_at)
        views_per_day = view_count / max(video_age_days, 1) if video_age_days > 0 else 0
        
        return {
            # Basic video information
            'video_id': video_id,
            'title': title,
            'description': description[:2000],  # Truncate for storage efficiency
            'published_at': published_at,
            'video_url': f"https://www.youtube.com/watch?v={video_id}",
            
            # Channel information
            'channel_id': snippet.get('channelId', ''),
            'channel_title': snippet.get('channelTitle', ''),
            'subscriber_count': channel_info.get('subscriber_count', 0),
            'video_count': channel_info.get('video_count', 0),
            
            # Statistics
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'engagement_rate': engagement_rate,
            'views_per_day': views_per_day,
            
            # Content details
            'duration': duration_iso,
            'duration_seconds': duration_seconds,
            'tags': snippet.get('tags', [])[:20],  # Limit tags to prevent storage bloat
            'category_id': snippet.get('categoryId', ''),
            'category_name': self.get_category_name(snippet.get('categoryId', '')),
            
            # Media and technical details
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'language': snippet.get('defaultLanguage', snippet.get('defaultAudioLanguage', '')),
            'caption_available': content_details.get('caption', 'false') == 'true',
            'definition': content_details.get('definition', 'sd'),
            
            # Sri Lankan content analysis
            'detected_location': content_analysis['detected_location'],
            'is_sri_lankan_content': content_analysis['is_sri_lankan'],
            'content_score': content_analysis['relevance_score'],
            'sri_lankan_indicators': content_analysis['indicators'],
            
            # Quality and metadata
            'quality_score': quality_score,
            'video_age_days': video_age_days,
            'is_live': status.get('uploadStatus') == 'live',
            'is_embeddable': status.get('embeddable', True),
            'license': status.get('license', 'youtube'),
            
            # Extraction metadata
            'extraction_date': datetime.now().isoformat(),
            'search_query': search_query,
            'last_updated': datetime.now().isoformat(),
            'thumbnail_downloaded': False  # Will be updated if thumbnail is saved
        }

    def parse_duration_to_seconds(self, duration_iso: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        if not duration_iso:
            return 0
        
        try:
            # Simple regex for PT1H2M3S format
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_iso)
            
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            logger.warning(f"Failed to parse duration {duration_iso}: {e}")
        
        return 0

    def analyze_sri_lankan_content(self, title: str, description: str, tags: List[str]) -> Dict:
        """Comprehensive analysis of Sri Lankan content relevance"""
        text_content = f"{title} {description} {' '.join(tags)}".lower()
        
        found_indicators = []
        location_score = 0
        cultural_score = 0
        category_score = 0
        
        # Check location indicators
        for location in self.sri_lanka_indicators['locations']:
            if location.lower() in text_content:
                found_indicators.append(('location', location))
                location_score += 1
        
        # Check cultural terms
        for term in self.sri_lanka_indicators['cultural_terms']:
            if term.lower() in text_content:
                found_indicators.append(('cultural', term))
                cultural_score += 1
        
        # Check category relevance
        for category in self.sri_lanka_indicators['categories']:
            if category.lower() in text_content:
                found_indicators.append(('category', category))
                category_score += 0.5
        
        # Calculate overall relevance score
        relevance_score = min(1.0, (location_score * 0.4 + cultural_score * 0.4 + category_score * 0.2) / 3)
        
        # Detect primary location
        detected_location = None
        for location in self.sri_lanka_indicators['locations']:
            if location.lower() in text_content:
                detected_location = location
                break
        
        # Determine if content is Sri Lankan
        is_sri_lankan = relevance_score > 0.2 or location_score > 0
        
        return {
            'is_sri_lankan': is_sri_lankan,
            'relevance_score': relevance_score,
            'detected_location': detected_location,
            'indicators': found_indicators,
            'location_score': location_score,
            'cultural_score': cultural_score,
            'category_score': category_score
        }

    def calculate_engagement_rate(self, views: int, likes: int, comments: int) -> float:
        """Calculate engagement rate as a percentage"""
        if views == 0:
            return 0.0
        
        total_engagement = likes + comments
        return round((total_engagement / views) * 100, 4)

    def extract_channel_info(self, snippet: Dict, channel_data: Dict = None) -> Dict:
        """Extract relevant channel information"""
        channel_info = {
            'subscriber_count': 0,
            'video_count': 0,
            'country': None
        }
        
        if channel_data:
            statistics = channel_data.get('statistics', {})
            snippet_data = channel_data.get('snippet', {})
            
            channel_info.update({
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'country': snippet_data.get('country', None)
            })
        
        return channel_info

    def calculate_content_quality_score(self, views: int, likes: int, comments: int, 
                                      title_length: int, description_length: int, duration: int) -> float:
        """Calculate a quality score for the content"""
        score = 0.0
        
        # View count factor (normalized)
        if views > 1000:
            score += 0.2
        elif views > 100:
            score += 0.1
        
        # Engagement factor
        if views > 0:
            like_ratio = likes / views
            comment_ratio = comments / views
            
            if like_ratio > 0.01:  # > 1% like rate
                score += 0.2
            elif like_ratio > 0.005:  # > 0.5% like rate
                score += 0.1
            
            if comment_ratio > 0.001:  # > 0.1% comment rate
                score += 0.1
        
        # Content completeness
        if title_length > 20:
            score += 0.1
        if description_length > 100:
            score += 0.1
        
        # Duration factor (prefer videos between 1-20 minutes)
        if 60 <= duration <= 1200:  # 1-20 minutes
            score += 0.2
        elif 30 <= duration <= 3600:  # 30s-1hour
            score += 0.1
        
        return min(1.0, score)

    def calculate_video_age_days(self, published_at: str) -> int:
        """Calculate video age in days"""
        if not published_at:
            return 0
        
        try:
            published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            age = datetime.now(published_date.tzinfo) - published_date
            return max(1, age.days)  # Minimum 1 day
        except Exception as e:
            logger.warning(f"Failed to calculate video age for {published_at}: {e}")
            return 1

    def get_category_name(self, category_id: str) -> str:
        """Map YouTube category ID to name"""
        category_mapping = {
            '1': 'Film & Animation', '2': 'Autos & Vehicles', '10': 'Music',
            '15': 'Pets & Animals', '17': 'Sports', '19': 'Travel & Events',
            '20': 'Gaming', '22': 'People & Blogs', '23': 'Comedy',
            '24': 'Entertainment', '25': 'News & Politics', '26': 'Howto & Style',
            '27': 'Education', '28': 'Science & Technology', '29': 'Nonprofits & Activism'
        }
        return category_mapping.get(category_id, 'Unknown')

    # Keep the old method for backward compatibility
    def extract_video_data(self, item: Dict, search_query: str) -> Dict:
        """Legacy method - use extract_enhanced_video_data instead"""
        return self.extract_enhanced_video_data(item, search_query)

    def detect_sri_lankan_location(self, text: str) -> Optional[str]:
        """Legacy method - detect Sri Lankan locations in text"""
        text_lower = text.lower()
        for location in self.sri_lanka_indicators['locations']:
            if location.lower() in text_lower:
                return location
        return None

    async def save_to_gcs(self, data: List[Dict], filename: str):
        """Enhanced GCS saving with error handling and metadata"""
        if not self.storage_client:
            logger.warning("Storage client not available, skipping GCS save")
            return
            
        try:
            bucket = self.storage_client.bucket(self.bucket_name)
            
            # Organize files by date and type
            current_date = datetime.now().strftime("%Y/%m/%d")
            blob_path = f"raw_data/{current_date}/{filename}"
            blob = bucket.blob(blob_path)
            
            # Add metadata
            metadata = {
                'extraction_date': datetime.now().isoformat(),
                'record_count': str(len(data)),
                'extractor_version': '2.0.0',
                'content_type': 'youtube_video_data'
            }
            blob.metadata = metadata
            
            # Compress and save JSON data
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            blob.upload_from_string(
                json_data, 
                content_type='application/json',
                timeout=300  # 5 minute timeout
            )
            
            logger.info(f"Saved {len(data)} records to GCS: {blob_path}")
            
            # Also save a backup copy if this is a large dataset
            if len(data) > 100:
                backup_path = f"backups/{current_date}/{filename}"
                backup_blob = bucket.blob(backup_path)
                backup_blob.upload_from_string(json_data, content_type='application/json')
                logger.info(f"Created backup copy at: {backup_path}")
                
        except Exception as e:
            logger.error(f"Error saving to GCS: {e}")
            # Don't raise - continue with local processing
            try:
                # Save locally as fallback
                local_path = f"data/gcs_fallback_{filename}"
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved fallback copy locally: {local_path}")
            except Exception as local_e:
                logger.error(f"Failed to save local fallback: {local_e}")

    async def save_to_bigquery(self, data: List[Dict]):
        """Enhanced BigQuery saving with deduplication and error handling"""
        if not self.bigquery_client:
            logger.warning("BigQuery client not available, skipping BigQuery save")
            return
            
        try:
            if not data:
                logger.info("No data to save to BigQuery")
                return
            
            table_ref = self.bigquery_client.dataset(self.dataset_id).table(self.table_id)
            table = self.bigquery_client.get_table(table_ref)
            
            # Remove duplicates and convert to BigQuery format
            seen_video_ids = set()
            rows_to_insert = []
            
            for item in data:
                video_id = item.get('video_id')
                if video_id in seen_video_ids:
                    continue
                seen_video_ids.add(video_id)
                
                # Check if video already exists in BigQuery
                if self.video_exists_in_bigquery(video_id):
                    logger.debug(f"Video {video_id} already exists in BigQuery, skipping")
                    continue
                
                row = self.prepare_bigquery_row(item)
                rows_to_insert.append(row)
            
            if not rows_to_insert:
                logger.info("No new records to insert into BigQuery")
                return
            
            # Insert in batches to avoid quota limits
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(rows_to_insert), batch_size):
                batch = rows_to_insert[i:i + batch_size]
                
                try:
                    errors = self.bigquery_client.insert_rows_json(
                        table, 
                        batch, 
                        retry=bigquery.DEFAULT_RETRY.with_deadline(300)
                    )
                    
                    if errors:
                        logger.error(f"BigQuery batch insert errors: {errors}")
                        # Try to insert successful rows individually
                        successful_count = self.insert_rows_individually(table, batch)
                        total_inserted += successful_count
                    else:
                        total_inserted += len(batch)
                        logger.info(f"Successfully inserted batch of {len(batch)} rows")
                        
                except Exception as batch_error:
                    logger.error(f"Error inserting batch: {batch_error}")
                    # Try individual insertion as fallback
                    successful_count = self.insert_rows_individually(table, batch)
                    total_inserted += successful_count
            
            logger.info(f"Total inserted into BigQuery: {total_inserted} out of {len(rows_to_insert)} rows")
            
            # Update daily summary
            await self.update_daily_summary(len(rows_to_insert))
            
        except Exception as e:
            logger.error(f"Error saving to BigQuery: {e}")
            # Save to local backup for later retry
            try:
                backup_file = f"data/bigquery_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved BigQuery backup to: {backup_file}")
            except Exception as backup_error:
                logger.error(f"Failed to create BigQuery backup: {backup_error}")

    def prepare_bigquery_row(self, item: Dict) -> Dict:
        """Prepare a single row for BigQuery insertion"""
        try:
            # Parse published_at timestamp
            published_at = item.get('published_at', '')
            if published_at:
                try:
                    published_timestamp = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except ValueError:
                    published_timestamp = datetime.now()
            else:
                published_timestamp = datetime.now()
            
            return {
                'video_id': item.get('video_id', ''),
                'title': item.get('title', '')[:500],  # Truncate titles
                'description': item.get('description', '')[:2000],  # Truncate descriptions
                'published_at': published_timestamp,
                'channel_id': item.get('channel_id', ''),
                'channel_title': item.get('channel_title', '')[:100],
                'view_count': item.get('view_count', 0),
                'like_count': item.get('like_count', 0),
                'comment_count': item.get('comment_count', 0),
                'duration': item.get('duration', ''),
                'duration_seconds': item.get('duration_seconds', 0),
                'tags': item.get('tags', [])[:20],  # Limit tags
                'category_id': item.get('category_id', ''),
                'category_name': item.get('category_name', ''),
                'thumbnail_url': item.get('thumbnail_url', ''),
                'language': item.get('language', ''),
                'detected_location': item.get('detected_location', ''),
                'extraction_date': datetime.now(),
                'search_query': item.get('search_query', ''),
                'video_url': item.get('video_url', ''),
                'is_sri_lankan_content': item.get('is_sri_lankan_content', False),
                'content_score': item.get('content_score', 0.0),
                'thumbnail_downloaded': item.get('thumbnail_downloaded', False),
                'last_updated': datetime.now(),
                'engagement_rate': item.get('engagement_rate', 0.0),
                'views_per_day': item.get('views_per_day', 0.0),
                'subscriber_count': item.get('subscriber_count', 0),
                'video_count': item.get('video_count', 0)
            }
        except Exception as e:
            logger.error(f"Error preparing BigQuery row: {e}")
            # Return minimal valid row
            return {
                'video_id': item.get('video_id', ''),
                'title': item.get('title', 'Error processing title'),
                'extraction_date': datetime.now(),
                'search_query': item.get('search_query', ''),
                'is_sri_lankan_content': False,
                'content_score': 0.0
            }

    def video_exists_in_bigquery(self, video_id: str) -> bool:
        """Check if video already exists in BigQuery"""
        try:
            query = f"""
            SELECT video_id 
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}` 
            WHERE video_id = @video_id 
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("video_id", "STRING", video_id)
                ]
            )
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            return len(results) > 0
            
        except Exception as e:
            logger.warning(f"Error checking video existence in BigQuery: {e}")
            return False  # Assume doesn't exist if we can't check

    def insert_rows_individually(self, table, rows: List[Dict]) -> int:
        """Insert rows one by one as fallback"""
        successful_count = 0
        
        for row in rows:
            try:
                errors = self.bigquery_client.insert_rows_json(table, [row])
                if not errors:
                    successful_count += 1
                else:
                    logger.warning(f"Failed to insert row for video {row.get('video_id', 'unknown')}: {errors}")
            except Exception as e:
                logger.warning(f"Error inserting individual row: {e}")
        
        return successful_count

    async def update_daily_summary(self, videos_processed: int):
        """Update the daily summary table"""
        if not self.bigquery_client:
            return
            
        try:
            today = datetime.now().date()
            
            # Insert or update daily summary
            summary_query = f"""
            MERGE `{self.project_id}.{self.dataset_id}.daily_summary` AS target
            USING (
                SELECT 
                    @date as date,
                    @videos_processed as videos_processed,
                    @api_requests as api_requests,
                    @extraction_cycles as extraction_cycles
            ) AS source
            ON target.date = source.date
            WHEN MATCHED THEN
                UPDATE SET
                    total_videos_extracted = target.total_videos_extracted + source.videos_processed,
                    api_requests_made = target.api_requests_made + source.api_requests,
                    extraction_cycles = target.extraction_cycles + source.extraction_cycles
            WHEN NOT MATCHED THEN
                INSERT (date, total_videos_extracted, api_requests_made, extraction_cycles)
                VALUES (source.date, source.videos_processed, source.api_requests, source.extraction_cycles)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("date", "DATE", today),
                    bigquery.ScalarQueryParameter("videos_processed", "INT64", videos_processed),
                    bigquery.ScalarQueryParameter("api_requests", "INT64", 1),
                    bigquery.ScalarQueryParameter("extraction_cycles", "INT64", 1)
                ]
            )
            
            query_job = self.bigquery_client.query(summary_query, job_config=job_config)
            query_job.result()  # Wait for completion
            
            logger.debug("Updated daily summary table")
            
        except Exception as e:
            logger.warning(f"Error updating daily summary: {e}")

    async def run_extraction_cycle(self, config: ExtractionConfig):
        """Enhanced extraction cycle with comprehensive error handling and metrics"""
        global extraction_status
        
        cycle_start_time = datetime.now()
        videos_found = 0
        
        try:
            extraction_status.update({
                "is_running": True,
                "current_message": f"Starting extraction for query: {config.query}",
                "current_search_config": {
                    "query": config.query,
                    "max_results": config.max_results,
                    "order": getattr(config, 'order', 'relevance'),
                    "published_after": config.published_after,
                    "published_before": config.published_before
                },
                "extraction_cycles": extraction_status.get("extraction_cycles", 0) + 1
            })
            
            logger.info(f"Starting extraction cycle for query: {config.query}")
            
            # Update extraction metrics
            self.extraction_metrics.total_extraction_cycles += 1
            
            # Search for videos with enhanced parameters
            videos = await self.search_videos(
                config.query, 
                config.max_results,
                config.published_after,
                config.published_before,
                getattr(config, 'order', 'relevance')
            )
            
            videos_found = len(videos)
            
            if videos:
                extraction_status["current_message"] = f"Processing {len(videos)} videos..."
                
                # Save to storage systems
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_query = re.sub(r'[^a-zA-Z0-9_-]', '_', config.query)
                filename = f"youtube_data_{safe_query}_{timestamp}.json"
                
                # Save to GCS (non-blocking)
                try:
                    await self.save_to_gcs(videos, filename)
                    extraction_status["current_message"] = f"Saved {len(videos)} videos to Cloud Storage"
                except Exception as gcs_error:
                    logger.error(f"GCS save failed: {gcs_error}")
                    extraction_status["current_message"] = f"GCS save failed, continuing with BigQuery"
                
                # Save to BigQuery (critical)
                try:
                    await self.save_to_bigquery(videos)
                    extraction_status["current_message"] = f"Successfully processed {len(videos)} videos"
                except Exception as bq_error:
                    logger.error(f"BigQuery save failed: {bq_error}")
                    extraction_status["current_message"] = f"BigQuery save failed: {str(bq_error)}"
                    raise bq_error
                
                # Update metrics
                extraction_status["videos_processed"] += len(videos)
                extraction_status["last_extraction"] = datetime.now().isoformat()
                self.extraction_metrics.total_videos_extracted += len(videos)
                self.extraction_metrics.successful_cycles += 1
                self.extraction_metrics.last_successful_extraction = datetime.now()
                
                logger.info(f"Successfully completed extraction cycle: {len(videos)} videos processed")
                
            else:
                extraction_status["current_message"] = "No new videos found for the given query"
                logger.info(f"No videos found for query: {config.query}")
                
                # Still count as successful cycle
                self.extraction_metrics.successful_cycles += 1
                
        except Exception as e:
            error_message = f"Error during extraction: {str(e)}"
            extraction_status["current_message"] = error_message
            extraction_status["failed_cycles"] = extraction_status.get("failed_cycles", 0) + 1
            extraction_status["total_errors"] = extraction_status.get("total_errors", 0) + 1
            
            self.extraction_metrics.failed_cycles += 1
            
            logger.error(f"Extraction cycle failed for query '{config.query}': {e}")
            
            # Don't re-raise the exception to allow the application to continue
            # raise
            
        finally:
            extraction_status["is_running"] = False
            
            # Calculate cycle time
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            logger.info(f"Extraction cycle completed in {cycle_duration:.2f} seconds, {videos_found} videos found")

    async def run_comprehensive_scheduled_extraction(self):
        """Enhanced scheduled extraction with strategic query selection"""
        global extraction_status
        
        try:
            extraction_status["is_running"] = True
            extraction_status["current_message"] = "Starting comprehensive scheduled extraction"
            
            logger.info("Starting comprehensive scheduled extraction")
            
            total_videos = 0
            successful_queries = 0
            failed_queries = 0
            
            # Primary queries for current content
            primary_strategies = [
                {'query': 'Sri Lanka', 'order': 'date', 'max_results': 50, 'days_back': 3},
                {'query': 'Sri Lanka tourism', 'order': 'relevance', 'max_results': 25, 'days_back': 7},
                {'query': 'Sri Lanka news', 'order': 'date', 'max_results': 30, 'days_back': 1},
                {'query': 'Ceylon', 'order': 'relevance', 'max_results': 20, 'days_back': 7},
                {'query': 'Colombo', 'order': 'viewCount', 'max_results': 25, 'days_back': 7},
            ]
            
            # Location-specific queries
            for location in self.sri_lanka_indicators['locations'][:10]:  # Top 10 locations
                primary_strategies.append({
                    'query': f"{location}",
                    'order': 'date',
                    'max_results': 15,
                    'days_back': 14
                })
            
            # Category combinations
            for category in self.sri_lanka_indicators['categories'][:8]:  # Top 8 categories
                primary_strategies.append({
                    'query': f"Sri Lanka {category}",
                    'order': 'relevance',
                    'max_results': 20,
                    'days_back': 14
                })
            
            # Execute all strategies
            for i, strategy in enumerate(primary_strategies):
                try:
                    extraction_status["current_message"] = f"Processing strategy {i+1}/{len(primary_strategies)}: {strategy['query']}"
                    
                    # Calculate date range
                    published_after = (datetime.now() - timedelta(days=strategy['days_back'])).isoformat()
                    
                    config = ExtractionConfig(
                        query=strategy['query'],
                        max_results=strategy['max_results'],
                        order=strategy['order'],
                        published_after=published_after
                    )
                    
                    await self.run_extraction_cycle(config)
                    successful_queries += 1
                    
                    # Add delay to respect API limits
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Failed strategy {strategy['query']}: {e}")
                    failed_queries += 1
                    continue
            
            extraction_status["current_message"] = f"Completed scheduled extraction: {successful_queries} successful, {failed_queries} failed"
            logger.info(f"Comprehensive extraction completed: {successful_queries} successful queries, {failed_queries} failed")
            
        except Exception as e:
            extraction_status["current_message"] = f"Scheduled extraction failed: {str(e)}"
            logger.error(f"Comprehensive scheduled extraction failed: {e}")
        finally:
            extraction_status["is_running"] = False

    async def run_targeted_extraction(self, targets: List[str], max_results_per_target: int = 25):
        """Run extraction for specific targets"""
        results = []
        
        for target in targets:
            try:
                config = ExtractionConfig(
                    query=target,
                    max_results=max_results_per_target,
                    order='relevance'
                )
                
                await self.run_extraction_cycle(config)
                results.append({"target": target, "status": "success"})
                
                # Small delay between targets
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed targeted extraction for {target}: {e}")
                results.append({"target": target, "status": "failed", "error": str(e)})
        
        return results

    def get_extraction_metrics(self) -> Dict[str, Any]:
        """Get comprehensive extraction metrics"""
        uptime = datetime.now() - self.extraction_metrics.start_time
        
        # Calculate API key metrics
        total_requests = sum(metrics.total_requests for metrics in self.api_key_metrics.values())
        successful_requests = sum(metrics.successful_requests for metrics in self.api_key_metrics.values())
        failed_requests = sum(metrics.failed_requests for metrics in self.api_key_metrics.values())
        
        return {
            # Extraction metrics
            "total_videos_extracted": self.extraction_metrics.total_videos_extracted,
            "total_extraction_cycles": self.extraction_metrics.total_extraction_cycles,
            "successful_cycles": self.extraction_metrics.successful_cycles,
            "failed_cycles": self.extraction_metrics.failed_cycles,
            "success_rate": round((self.extraction_metrics.successful_cycles / max(self.extraction_metrics.total_extraction_cycles, 1)) * 100, 2),
            
            # API metrics
            "total_api_requests": total_requests,
            "successful_api_requests": successful_requests,
            "failed_api_requests": failed_requests,
            "api_success_rate": round((successful_requests / max(total_requests, 1)) * 100, 2),
            
            # Timing metrics
            "uptime": str(uptime).split('.')[0],  # Remove microseconds
            "start_time": self.extraction_metrics.start_time.isoformat(),
            "last_successful_extraction": self.extraction_metrics.last_successful_extraction.isoformat() if self.extraction_metrics.last_successful_extraction else None,
            
            # Performance metrics
            "videos_per_hour": round(self.extraction_metrics.total_videos_extracted / max(uptime.total_seconds() / 3600, 1), 2),
            "cycles_per_hour": round(self.extraction_metrics.total_extraction_cycles / max(uptime.total_seconds() / 3600, 1), 2),
            
            # API key details
            "api_keys_count": len(self.api_keys),
            "active_api_keys": len([k for k in self.api_keys if self.is_key_available(k)]),
        }

    # Keep the old method for backward compatibility
    async def run_scheduled_extraction(self):
        """Legacy method - use run_comprehensive_scheduled_extraction instead"""
        return await self.run_comprehensive_scheduled_extraction()

# Initialize the extractor
extractor = YouTubeExtractor()

# Enhanced FastAPI app setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Enhanced YouTube Data Extractor FastAPI application")
    
    # Start background scheduler for automatic extractions
    def run_scheduler():
        # Schedule comprehensive extraction every 6 hours
        schedule.every(6).hours.do(lambda: asyncio.create_task(extractor.run_comprehensive_scheduled_extraction()))
        
        # Schedule quick updates every hour
        schedule.every(1).hour.do(lambda: asyncio.create_task(extractor.run_targeted_extraction(['Sri Lanka news', 'Sri Lanka'], 25)))
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced YouTube Data Extractor")

app = FastAPI(
    title="Enhanced YouTube Data Extractor for Sri Lanka",
    description="Comprehensive YouTube video data collection and analysis platform for Sri Lankan content",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files and templates (create directories if they don't exist)
import os
os.makedirs("static", exist_ok=True)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

templates = Jinja2Templates(directory="templates")

# Enhanced API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Enhanced main dashboard"""
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "title": "Enhanced YouTube Data Extractor - Sri Lanka"
        })
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        # Return simple HTML if template fails
        return HTMLResponse("""
        <!DOCTYPE html>
        <html><head><title>YouTube Data Extractor</title></head>
        <body>
        <h1>🇱🇰 YouTube Data Extractor for Sri Lanka</h1>
        <p>Dashboard template not found. Please check the templates directory.</p>
        <p><a href="/docs">View API Documentation</a></p>
        </body></html>
        """)

@app.get("/api/status")
async def get_enhanced_status():
    """Get comprehensive extraction status with detailed metrics"""
    try:
        # Get system metrics
        memory_usage = f"{psutil.virtual_memory().percent}%"
        cpu_usage = f"{psutil.cpu_percent(interval=1)}%"
        
        # Calculate uptime
        uptime = datetime.now() - extraction_status["start_time"]
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Get API key information
        api_keys_info = []
        for i, key in enumerate(extractor.api_keys):
            metrics = extractor.api_key_metrics.get(key, APIKeyMetrics())
            api_keys_info.append({
                "index": i,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "quota_exceeded_count": metrics.quota_exceeded_count,
                "last_used": metrics.last_used.isoformat() if metrics.last_used else None,
                "is_available": extractor.is_key_available(key)
            })
        
        # Get extraction metrics
        extraction_metrics = extractor.get_extraction_metrics()
        
        return {
            "status": "running" if extraction_status["is_running"] else "idle",
            "message": extraction_status["current_message"],
            "videos_processed": extraction_status["videos_processed"],
            "current_api_key_index": extractor.current_key_index,
            "last_extraction": extraction_status["last_extraction"],
            "uptime": uptime_str,
            "current_search_config": extraction_status.get("current_search_config"),
            "api_keys": api_keys_info,
            "extraction_metrics": extraction_metrics,
            "stats": {
                "total_api_requests": extraction_metrics["total_api_requests"],
                "successful_cycles": extraction_metrics["successful_cycles"],
                "failed_cycles": extraction_metrics["failed_cycles"],
                "extraction_cycles": extraction_metrics["total_extraction_cycles"],
                "start_time": extraction_status["start_time"].isoformat(),
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "api_success_rate": extraction_metrics["api_success_rate"],
                "videos_per_hour": extraction_metrics["videos_per_hour"],
                "active_api_keys": extraction_metrics["active_api_keys"],
                "errors": extraction_status.get("total_errors", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "error",
            "message": f"Error retrieving status: {str(e)}",
            "videos_processed": 0,
            "current_api_key_index": 0,
            "last_extraction": None,
            "uptime": "unknown",
            "api_keys": [],
            "stats": {}
        }

@app.post("/api/extract")
async def start_enhanced_extraction(config: ExtractionConfig, background_tasks: BackgroundTasks):
    """Start enhanced video extraction for a specific query"""
    if extraction_status["is_running"]:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    # Validate configuration
    if not config.query or not config.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if config.max_results > 500:
        raise HTTPException(status_code=400, detail="Max results cannot exceed 500")
    
    background_tasks.add_task(extractor.run_extraction_cycle, config)
    
    return {
        "message": "Enhanced extraction started",
        "config": config.dict(),
        "estimated_duration": "2-10 minutes",
        "started_at": datetime.now().isoformat()
    }

@app.post("/api/extract/scheduled")
async def start_comprehensive_scheduled_extraction(background_tasks: BackgroundTasks):
    """Start comprehensive scheduled extraction for all Sri Lankan content"""
    if extraction_status["is_running"]:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    background_tasks.add_task(extractor.run_comprehensive_scheduled_extraction)
    
    return {
        "message": "Comprehensive scheduled extraction started",
        "estimated_duration": "30-60 minutes",
        "strategies_count": len(extractor.sri_lanka_indicators['locations']) + len(extractor.sri_lanka_indicators['categories']) + 5,
        "started_at": datetime.now().isoformat()
    }

@app.post("/api/extract/targeted")
async def start_targeted_extraction(targets: List[str], max_results: int = 25, background_tasks: BackgroundTasks = None):
    """Start targeted extraction for specific queries"""
    if extraction_status["is_running"]:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    if not targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if len(targets) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 targets allowed")
    
    if background_tasks:
        background_tasks.add_task(extractor.run_targeted_extraction, targets, max_results)
        return {
            "message": f"Targeted extraction started for {len(targets)} targets",
            "targets": targets,
            "max_results_per_target": max_results,
            "started_at": datetime.now().isoformat()
        }
    else:
        # Synchronous execution for immediate results
        results = await extractor.run_targeted_extraction(targets, max_results)
        return {
            "message": "Targeted extraction completed",
            "results": results,
            "completed_at": datetime.now().isoformat()
        }

@app.get("/api/queries")
async def get_predefined_queries():
    """Get predefined Sri Lankan queries and categories"""
    return {
        "locations": extractor.sri_lanka_indicators['locations'],
        "cultural_terms": extractor.sri_lanka_indicators['cultural_terms'][:20],  # Limit for UI
        "categories": extractor.sri_lanka_indicators['categories'],
        "quick_queries": [
            "Sri Lanka tourism",
            "Sri Lanka food",
            "Sri Lanka culture",
            "Sri Lanka news",
            "Ceylon tea",
            "Colombo",
            "Kandy",
            "Sigiriya",
            "Sri Lankan music",
            "Lankan cricket"
        ]
    }

@app.get("/api/analytics/summary")
async def get_enhanced_analytics_summary():
    """Get comprehensive analytics summary from BigQuery"""
    if not extractor.bigquery_client:
        raise HTTPException(status_code=503, detail="BigQuery client not available")
        
    try:
        query = f"""
        SELECT 
            search_query,
            COUNT(*) as total_videos,
            COUNT(DISTINCT channel_id) as unique_channels,
            AVG(view_count) as avg_views,
            AVG(engagement_rate) as avg_engagement,
            AVG(content_score) as avg_content_score,
            MAX(published_at) as latest_video,
            SUM(CASE WHEN is_sri_lankan_content THEN 1 ELSE 0 END) as sri_lankan_videos,
            AVG(duration_seconds) as avg_duration_seconds
        FROM `{extractor.project_id}.{extractor.dataset_id}.{extractor.table_id}`
        WHERE extraction_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY search_query
        ORDER BY total_videos DESC
        LIMIT 20
        """
        
        query_job = extractor.bigquery_client.query(query)
        results = query_job.result()
        
        summary = []
        for row in results:
            summary.append({
                "search_query": row.search_query,
                "total_videos": row.total_videos,
                "unique_channels": row.unique_channels,
                "avg_views": round(float(row.avg_views) if row.avg_views else 0, 0),
                "avg_engagement": round(float(row.avg_engagement) if row.avg_engagement else 0, 4),
                "avg_content_score": round(float(row.avg_content_score) if row.avg_content_score else 0, 3),
                "latest_video": row.latest_video.isoformat() if row.latest_video else None,
                "sri_lankan_videos": row.sri_lankan_videos,
                "avg_duration_minutes": round(float(row.avg_duration_seconds or 0) / 60, 1),
                "sri_lankan_percentage": round((row.sri_lankan_videos / row.total_videos) * 100, 1) if row.total_videos > 0 else 0
            })
        
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics: {str(e)}")

@app.get("/api/analytics/trending")
async def get_enhanced_trending_videos():
    """Get trending videos with enhanced metrics"""
    if not extractor.bigquery_client:
        raise HTTPException(status_code=503, detail="BigQuery client not available")
        
    try:
        query = f"""
        SELECT 
            video_id,
            title,
            channel_title,
            view_count,
            like_count,
            comment_count,
            engagement_rate,
            content_score,
            published_at,
            thumbnail_url,
            duration_seconds,
            is_sri_lankan_content,
            detected_location,
            views_per_day
        FROM `{extractor.project_id}.{extractor.dataset_id}.{extractor.table_id}`
        WHERE published_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
          AND is_sri_lankan_content = true
        ORDER BY view_count DESC, engagement_rate DESC
        LIMIT 30
        """
        
        query_job = extractor.bigquery_client.query(query)
        results = query_job.result()
        
        trending = []
        for row in results:
            trending.append({
                "video_id": row.video_id,
                "title": row.title,
                "channel_title": row.channel_title,
                "view_count": row.view_count,
                "like_count": row.like_count,
                "comment_count": row.comment_count,
                "engagement_rate": round(float(row.engagement_rate or 0), 4),
                "content_score": round(float(row.content_score or 0), 3),
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "thumbnail_url": row.thumbnail_url,
                "duration_minutes": round(float(row.duration_seconds or 0) / 60, 1),
                "detected_location": row.detected_location,
                "views_per_day": round(float(row.views_per_day or 0), 1),
                "youtube_url": f"https://www.youtube.com/watch?v={row.video_id}"
            })
        
        return {"trending_videos": trending}
        
    except Exception as e:
        logger.error(f"Error getting trending videos: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving trending videos: {str(e)}")

@app.get("/api/analytics/channels")
async def get_top_channels():
    """Get top Sri Lankan channels by various metrics"""
    if not extractor.bigquery_client:
        raise HTTPException(status_code=503, detail="BigQuery client not available")
        
    try:
        query = f"""
        SELECT 
            channel_id,
            channel_title,
            COUNT(*) as video_count,
            SUM(view_count) as total_views,
            AVG(view_count) as avg_views,
            AVG(engagement_rate) as avg_engagement,
            MAX(published_at) as latest_video,
            AVG(content_score) as avg_content_score
        FROM `{extractor.project_id}.{extractor.dataset_id}.{extractor.table_id}`
        WHERE is_sri_lankan_content = true
          AND extraction_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY channel_id, channel_title
        HAVING video_count >= 3
        ORDER BY total_views DESC
        LIMIT 20
        """
        
        query_job = extractor.bigquery_client.query(query)
        results = query_job.result()
        
        channels = []
        for row in results:
            channels.append({
                "channel_id": row.channel_id,
                "channel_title": row.channel_title,
                "video_count": row.video_count,
                "total_views": row.total_views,
                "avg_views": round(float(row.avg_views or 0), 0),
                "avg_engagement": round(float(row.avg_engagement or 0), 4),
                "latest_video": row.latest_video.isoformat() if row.latest_video else None,
                "avg_content_score": round(float(row.avg_content_score or 0), 3),
                "channel_url": f"https://www.youtube.com/channel/{row.channel_id}"
            })
        
        return {"top_channels": channels}
        
    except Exception as e:
        logger.error(f"Error getting top channels: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving top channels: {str(e)}")

@app.get("/api/metrics")
async def get_system_metrics():
    """Get detailed system and extraction metrics"""
    try:
        metrics = extractor.get_extraction_metrics()
        
        # Add system information
        metrics.update({
            "system": {
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(interval=1),
                "disk_usage": psutil.disk_usage('/').percent if os.path.exists('/') else None
            },
            "api_keys": {
                "total": len(extractor.api_keys),
                "active": len([k for k in extractor.api_keys if extractor.is_key_available(k)]),
                "current_index": extractor.current_key_index
            }
        })
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

# Health check with detailed system information
@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check endpoint with system status"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "components": {
                "bigquery": "healthy" if extractor.bigquery_client else "unavailable",
                "gcs": "healthy" if extractor.storage_client else "unavailable",
                "api_keys": f"{len([k for k in extractor.api_keys if extractor.is_key_available(k)])}/{len(extractor.api_keys)} available",
                "extraction": "running" if extraction_status["is_running"] else "idle"
            },
            "metrics": {
                "total_videos": extraction_status["videos_processed"],
                "uptime": str(datetime.now() - extraction_status["start_time"]).split('.')[0]
            }
        }
        
        # Check if any critical components are down
        if not extractor.bigquery_client and not extractor.storage_client:
            health_status["status"] = "degraded"
            health_status["message"] = "No storage backends available"
        elif len([k for k in extractor.api_keys if extractor.is_key_available(k)]) == 0:
            health_status["status"] = "degraded"
            health_status["message"] = "No API keys available"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    # Configuration for production deployment
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        access_log=True,
        log_level="info"
    )