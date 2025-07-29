import logging
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import backoff
from fastapi import HTTPException

from ..config import settings
from ..models import APIKeyMetrics

logger = logging.getLogger(__name__)


class YouTubeAPIService:
    """Service for interacting with YouTube Data API v3."""
    
    def __init__(self):
        self.api_keys = settings.youtube_api_keys
        self.current_key_index = 0
        self.api_key_metrics = {key: APIKeyMetrics() for key in self.api_keys}
        self.daily_limit_per_key = settings.daily_limit_per_key
        self.requests_per_hour_limit = settings.requests_per_hour_limit
        self.last_reset = datetime.now().date()
        
        if not self.api_keys:
            raise ValueError("No YouTube API keys configured. Please set YOUTUBE_API_KEY_1, etc.")
        
        logger.info(f"Initialized YouTube API service with {len(self.api_keys)} keys")
    
    def reset_daily_usage_if_needed(self):
        """Reset API key usage counters daily with proper metrics tracking."""
        current_date = datetime.now().date()
        if current_date > self.last_reset:
            # Reset counters for each key
            for key in self.api_keys:
                if key in self.api_key_metrics:
                    metrics = self.api_key_metrics[key]
                    metrics.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            self.last_reset = current_date
            logger.info(f"Daily API usage tracking reset for {len(self.api_keys)} keys")
    
    def is_key_available(self, api_key: str) -> bool:
        """Check if an API key is available for use."""
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
        """Enhanced API key rotation with availability checking."""
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
            self.current_key_index = original_index
            raise Exception("All API keys have reached their daily quota limit or are unavailable")
    
    def get_youtube_client(self):
        """Get YouTube API client with enhanced key rotation and error handling."""
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
    
    def log_api_usage(self, api_key: str, request_type: str, success: bool, 
                     quota_cost: int = 1, error_message: str = None):
        """Log API usage for monitoring and analytics."""
        try:
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
    
    @backoff.on_exception(
        backoff.expo,
        (HttpError, Exception),
        max_tries=3,
        max_time=300
    )
    async def search_videos(self, query: str, max_results: int = 50, 
                          published_after: str = None, published_before: str = None,
                          order: str = 'relevance', region_code: str = 'LK') -> List[Dict]:
        """Enhanced video search with better error handling and filtering."""
        try:
            youtube = self.get_youtube_client()
            current_key = self.api_keys[self.current_key_index]
            
            # Build search parameters
            search_params = {
                'q': query,
                'part': 'snippet',
                'maxResults': min(max_results, 50),  # YouTube API limit per request
                'type': 'video',
                'order': order,
                'regionCode': region_code,
                'relevanceLanguage': 'en'
            }
            
            # Add date filters if provided
            if published_after:
                search_params['publishedAfter'] = published_after
            if published_before:
                search_params['publishedBefore'] = published_before
            
            logger.info(f"Searching YouTube: query='{query}', max_results={max_results}, order={order}")
            
            # Execute search request
            request = youtube.search().list(**search_params)
            response = request.execute()
            
            # Log successful API usage
            self.log_api_usage(current_key, 'search', True, quota_cost=100)
            
            # Process results
            videos = []
            if 'items' in response:
                for item in response['items']:
                    try:
                        video_data = {
                            'video_id': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'description': item['snippet']['description'],
                            'published_at': item['snippet']['publishedAt'],
                            'channel_id': item['snippet']['channelId'],
                            'channel_title': item['snippet']['channelTitle'],
                            'thumbnails': item['snippet'].get('thumbnails', {}),
                            'tags': item['snippet'].get('tags', []),
                            'category_id': item['snippet'].get('categoryId', ''),
                            'default_language': item['snippet'].get('defaultLanguage', ''),
                            'default_audio_language': item['snippet'].get('defaultAudioLanguage', ''),
                            'live_broadcast_content': item['snippet'].get('liveBroadcastContent', 'none')
                        }
                        videos.append(video_data)
                    except KeyError as e:
                        logger.warning(f"Missing field in video data: {e}")
                        continue
            
            logger.info(f"Successfully retrieved {len(videos)} videos for query: {query}")
            return videos
            
        except HttpError as e:
            current_key = self.api_keys[self.current_key_index]
            error_msg = str(e)
            
            self.log_api_usage(current_key, 'search', False, error_message=error_msg)
            
            if e.resp.status == 403:
                if 'quota' in error_msg.lower():
                    logger.warning(f"API quota exceeded for key {self.current_key_index}, rotating...")
                    self.rotate_api_key()
                    # Retry with new key
                    return await self.search_videos(query, max_results, published_after, published_before, order, region_code)
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
            self.log_api_usage(current_key, 'search', False, error_message=str(e))
            logger.error(f"Unexpected error in video search: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")
    
    async def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information for a list of video IDs."""
        if not video_ids:
            return []
        
        try:
            youtube = self.get_youtube_client()
            current_key = self.api_keys[self.current_key_index]
            
            # Split video IDs into chunks of 50 (API limit)
            video_chunks = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
            all_videos = []
            
            for chunk in video_chunks:
                request = youtube.videos().list(
                    part='snippet,statistics,contentDetails,status',
                    id=','.join(chunk)
                )
                response = request.execute()
                
                self.log_api_usage(current_key, 'videos', True, quota_cost=1)
                
                if 'items' in response:
                    for item in response['items']:
                        try:
                            video_data = {
                                'video_id': item['id'],
                                'title': item['snippet']['title'],
                                'description': item['snippet']['description'],
                                'published_at': item['snippet']['publishedAt'],
                                'channel_id': item['snippet']['channelId'],
                                'channel_title': item['snippet']['channelTitle'],
                                'tags': item['snippet'].get('tags', []),
                                'category_id': item['snippet'].get('categoryId', ''),
                                'default_language': item['snippet'].get('defaultLanguage', ''),
                                'view_count': int(item['statistics'].get('viewCount', 0)),
                                'like_count': int(item['statistics'].get('likeCount', 0)),
                                'comment_count': int(item['statistics'].get('commentCount', 0)),
                                'duration': item['contentDetails'].get('duration', ''),
                                'definition': item['contentDetails'].get('definition', 'sd'),
                                'caption': item['contentDetails'].get('caption', 'false'),
                                'licensed_content': item['contentDetails'].get('licensedContent', False),
                                'privacy_status': item['status'].get('privacyStatus', 'public'),
                                'upload_status': item['status'].get('uploadStatus', 'processed'),
                                'embeddable': item['status'].get('embeddable', True)
                            }
                            all_videos.append(video_data)
                        except (KeyError, ValueError) as e:
                            logger.warning(f"Error processing video details: {e}")
                            continue
            
            logger.info(f"Retrieved details for {len(all_videos)} videos")
            return all_videos
            
        except HttpError as e:
            current_key = self.api_keys[self.current_key_index]
            self.log_api_usage(current_key, 'videos', False, error_message=str(e))
            logger.error(f"Error getting video details: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get video details: {e}")
    
    async def get_channel_details(self, channel_ids: List[str]) -> List[Dict]:
        """Get detailed information for a list of channel IDs."""
        if not channel_ids:
            return []
        
        try:
            youtube = self.get_youtube_client()
            current_key = self.api_keys[self.current_key_index]
            
            # Split channel IDs into chunks of 50 (API limit)
            channel_chunks = [channel_ids[i:i+50] for i in range(0, len(channel_ids), 50)]
            all_channels = []
            
            for chunk in channel_chunks:
                request = youtube.channels().list(
                    part='snippet,statistics,brandingSettings',
                    id=','.join(chunk)
                )
                response = request.execute()
                
                self.log_api_usage(current_key, 'channels', True, quota_cost=1)
                
                if 'items' in response:
                    for item in response['items']:
                        try:
                            channel_data = {
                                'channel_id': item['id'],
                                'title': item['snippet']['title'],
                                'description': item['snippet']['description'],
                                'published_at': item['snippet']['publishedAt'],
                                'country': item['snippet'].get('country', ''),
                                'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                                'video_count': int(item['statistics'].get('videoCount', 0)),
                                'view_count': int(item['statistics'].get('viewCount', 0)),
                                'keywords': item.get('brandingSettings', {}).get('channel', {}).get('keywords', ''),
                                'banner_image_url': item.get('brandingSettings', {}).get('image', {}).get('bannerExternalUrl', '')
                            }
                            all_channels.append(channel_data)
                        except (KeyError, ValueError) as e:
                            logger.warning(f"Error processing channel details: {e}")
                            continue
            
            logger.info(f"Retrieved details for {len(all_channels)} channels")
            return all_channels
            
        except HttpError as e:
            current_key = self.api_keys[self.current_key_index]
            self.log_api_usage(current_key, 'channels', False, error_message=str(e))
            logger.error(f"Error getting channel details: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get channel details: {e}")
    
    def get_api_key_status(self) -> Dict[str, Any]:
        """Get current status of all API keys."""
        status = {
            'total_keys': len(self.api_keys),
            'current_key_index': self.current_key_index,
            'keys': []
        }
        
        for i, key in enumerate(self.api_keys):
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
            metrics = self.api_key_metrics.get(key, APIKeyMetrics())
            
            key_status = {
                'index': i,
                'key_hash': key_hash,
                'is_current': i == self.current_key_index,
                'is_available': self.is_key_available(key),
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'quota_exceeded_count': metrics.quota_exceeded_count,
                'last_used': metrics.last_used.isoformat() if metrics.last_used else None,
                'quota_remaining': max(0, self.daily_limit_per_key - metrics.total_requests)
            }
            status['keys'].append(key_status)
        
        return status