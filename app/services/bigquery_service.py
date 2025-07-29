import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound, Conflict

from ..config import settings

logger = logging.getLogger(__name__)


class BigQueryService:
    """Service for interacting with Google BigQuery."""
    
    def __init__(self):
        self.project_id = settings.google_cloud_project_id
        self.dataset_id = settings.bigquery_dataset_id
        self.table_id = settings.bigquery_table_id
        self.client = None
        
        if self.project_id:
            self._initialize_client()
            self._ensure_dataset_and_tables()
    
    def _initialize_client(self):
        """Initialize BigQuery client with proper authentication."""
        try:
            credentials_path = settings.google_application_credentials
            
            if credentials_path:
                logger.info(f"Using service account credentials: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = bigquery.Client(credentials=credentials, project=self.project_id)
            else:
                logger.info("Using default credentials")
                self.client = bigquery.Client(project=self.project_id)
            
            logger.info(f"BigQuery client initialized for project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            self.client = None
    
    def _ensure_dataset_and_tables(self):
        """Ensure dataset and tables exist."""
        if not self.client:
            return
        
        try:
            # Create dataset if it doesn't exist
            dataset_ref = self.client.dataset(self.dataset_id)
            try:
                self.client.get_dataset(dataset_ref)
                logger.info(f"Dataset {self.dataset_id} already exists")
            except NotFound:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                dataset.description = "YouTube video data analytics for Sri Lankan content"
                
                self.client.create_dataset(dataset)
                logger.info(f"Created dataset: {self.dataset_id}")
            
            # Create main video data table
            self._create_video_table(dataset_ref)
            
            # Create analytics tables
            self._create_analytics_tables(dataset_ref)
            
        except Exception as e:
            logger.error(f"Error ensuring BigQuery resources: {e}")
    
    def _create_video_table(self, dataset_ref):
        """Create the main videos table with partitioning and clustering."""
        table_ref = dataset_ref.table(self.table_id)
        
        try:
            self.client.get_table(table_ref)
            logger.info(f"Table {self.table_id} already exists")
            return
        except NotFound:
            pass
        
        # Define enhanced schema
        schema = [
            bigquery.SchemaField("video_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("published_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("view_count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("like_count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("comment_count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("duration", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
            bigquery.SchemaField("category_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("language", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("location", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("extraction_date", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("search_query", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("video_url", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("is_sri_lankan_content", "BOOLEAN", mode="REQUIRED"),
            bigquery.SchemaField("content_score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("quality_score", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("engagement_rate", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("definition", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("caption", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("licensed_content", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("privacy_status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("upload_status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("embeddable", "BOOLEAN", mode="NULLABLE")
        ]
        
        table = bigquery.Table(table_ref, schema=schema)
        
        # Configure partitioning and clustering
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="extraction_date"
        )
        
        table.clustering_fields = ["is_sri_lankan_content", "channel_id", "category_id"]
        
        # Set table description
        table.description = "YouTube video data with Sri Lankan content analysis"
        
        self.client.create_table(table)
        logger.info(f"Created partitioned and clustered table: {self.table_id}")
    
    def _create_analytics_tables(self, dataset_ref):
        """Create additional analytics tables."""
        # Channel analytics table
        channel_table_ref = dataset_ref.table("channel_analytics")
        
        try:
            self.client.get_table(channel_table_ref)
        except NotFound:
            channel_schema = [
                bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("total_videos", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("total_views", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("total_likes", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("avg_engagement_rate", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("sri_lankan_video_count", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED")
            ]
            
            channel_table = bigquery.Table(channel_table_ref, schema=channel_schema)
            channel_table.description = "Aggregated channel analytics"
            self.client.create_table(channel_table)
            logger.info("Created channel_analytics table")
        
        # Daily aggregation table
        daily_table_ref = dataset_ref.table("daily_aggregations")
        
        try:
            self.client.get_table(daily_table_ref)
        except NotFound:
            daily_schema = [
                bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("total_videos_extracted", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("sri_lankan_videos", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("total_views", "INTEGER", mode="REQUIRED"),
                bigquery.SchemaField("avg_content_score", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("top_categories", "STRING", mode="REPEATED"),
                bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED")
            ]
            
            daily_table = bigquery.Table(daily_table_ref, schema=daily_schema)
            daily_table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            )
            daily_table.description = "Daily aggregated statistics"
            self.client.create_table(daily_table)
            logger.info("Created daily_aggregations table")

    def insert_rows(self, rows):
        """Legacy method for backward compatibility."""
        return self.insert_video_data(rows)
    
    def insert_video_data(self, videos: List[Dict[str, Any]]) -> List[Dict]:
        """Insert video data into BigQuery."""
        if not self.client or not videos:
            return []
        
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            table = self.client.get_table(table_ref)
            
            # Prepare rows for insertion
            rows_to_insert = []
            for video in videos:
                row = self._prepare_video_row(video)
                if row:
                    rows_to_insert.append(row)
            
            if not rows_to_insert:
                logger.warning("No valid rows to insert")
                return []
            
            # Insert rows
            errors = self.client.insert_rows_json(table, rows_to_insert)
            
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                return errors
            else:
                logger.info(f"Successfully inserted {len(rows_to_insert)} rows into BigQuery")
                return []
                
        except Exception as e:
            logger.error(f"Error inserting video data to BigQuery: {e}")
            return [{"error": str(e)}]
    
    def _prepare_video_row(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare a video data row for BigQuery insertion."""
        try:
            return {
                "video_id": video.get("video_id", ""),
                "title": video.get("title", ""),
                "description": video.get("description", ""),
                "published_at": video.get("published_at", datetime.now().isoformat()),
                "channel_id": video.get("channel_id", ""),
                "channel_title": video.get("channel_title", ""),
                "view_count": video.get("view_count", 0),
                "like_count": video.get("like_count", 0),
                "comment_count": video.get("comment_count", 0),
                "duration": video.get("duration", ""),
                "tags": video.get("tags", []),
                "category_id": video.get("category_id", ""),
                "language": video.get("language", ""),
                "location": video.get("location", ""),
                "extraction_date": video.get("extraction_date", datetime.now().isoformat()),
                "search_query": video.get("search_query", ""),
                "video_url": video.get("video_url", ""),
                "is_sri_lankan_content": video.get("is_sri_lankan_content", False),
                "content_score": video.get("content_score", 0.0),
                "quality_score": video.get("quality_score", 0.0),
                "engagement_rate": video.get("engagement_rate", 0.0),
                "definition": video.get("definition", "sd"),
                "caption": video.get("caption", "false"),
                "licensed_content": video.get("licensed_content", False),
                "privacy_status": video.get("privacy_status", "public"),
                "upload_status": video.get("upload_status", "processed"),
                "embeddable": video.get("embeddable", True)
            }
        except Exception as e:
            logger.error(f"Error preparing video row: {e}")
            return None

    def video_exists(self, video_id: str) -> bool:
        """Check if a video already exists in the database."""
        if not self.client:
            return False
            
        try:
            query = f"""
            SELECT video_id FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE video_id = @video_id LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("video_id", "STRING", video_id)]
            )
            query_job = self.client.query(query, job_config=job_config)
            return len(list(query_job.result())) > 0
        except Exception as e:
            logger.error(f"Error checking video existence: {e}")
            return False
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary from BigQuery."""
        if not self.client:
            return {}
        
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_videos,
                SUM(CASE WHEN is_sri_lankan_content THEN 1 ELSE 0 END) as sri_lankan_videos,
                AVG(content_score) as avg_content_score,
                SUM(view_count) as total_views,
                SUM(like_count) as total_likes,
                COUNT(DISTINCT channel_id) as unique_channels,
                AVG(CASE WHEN view_count > 0 THEN like_count / view_count ELSE 0 END) as avg_engagement_rate
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE DATE(extraction_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            for row in results:
                return {
                    "total_videos": row.total_videos,
                    "sri_lankan_videos": row.sri_lankan_videos,
                    "avg_content_score": float(row.avg_content_score) if row.avg_content_score else 0.0,
                    "total_views": row.total_views,
                    "total_likes": row.total_likes,
                    "unique_channels": row.unique_channels,
                    "avg_engagement_rate": float(row.avg_engagement_rate) if row.avg_engagement_rate else 0.0
                }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {}
        
        return {}
    
    def is_available(self) -> bool:
        """Check if BigQuery service is available."""
        return self.client is not None