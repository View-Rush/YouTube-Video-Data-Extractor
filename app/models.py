from datetime import datetime
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

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
    published_at: str
    channel_id: str
    channel_title: str
    view_count: int
    like_count: int
    comment_count: int
    duration: str
    tags: List[str]
    category_id: str
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