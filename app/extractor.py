import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .config import settings
from .models import ExtractionConfig, extraction_status
from .services.youtube_service import YouTubeAPIService
from .services.bigquery_service import BigQueryService
from .services.gcs_service import GCSService
from .services.content_analysis_service import ContentAnalysisService
from .services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Main YouTube video data extractor with modular service architecture."""
    
    def __init__(self):
        # Initialize services
        self.youtube_service = YouTubeAPIService()
        self.bigquery_service = BigQueryService()
        self.gcs_service = GCSService()
        self.content_analysis_service = ContentAnalysisService()
        self.database_service = DatabaseService()
        
        # Search strategies for Sri Lankan content
        self.search_strategies = self._initialize_search_strategies()
        
        # Extraction state
        self.current_session_id = None
        self.is_running = False
        
        logger.info("YouTube Extractor initialized with modular services")
    
    def _initialize_search_strategies(self) -> List[Dict[str, Any]]:
        """Initialize comprehensive search strategies for Sri Lankan content."""
        return [
            # Location-based searches
            {"query": "Sri Lanka", "category": "general", "priority": 1},
            {"query": "Colombo", "category": "location", "priority": 2},
            {"query": "Kandy Sri Lanka", "category": "location", "priority": 2},
            {"query": "Galle Sri Lanka", "category": "location", "priority": 2},
            {"query": "Jaffna Sri Lanka", "category": "location", "priority": 3},
            
            # Cultural and traditional content
            {"query": "Sinhala", "category": "culture", "priority": 2},
            {"query": "Tamil Sri Lanka", "category": "culture", "priority": 2},
            {"query": "Vesak Sri Lanka", "category": "culture", "priority": 3},
            {"query": "Avurudu Sri Lanka", "category": "culture", "priority": 3},
            {"query": "Sri Lankan food", "category": "culture", "priority": 2},
            
            # Entertainment and media
            {"query": "Sri Lankan music", "category": "entertainment", "priority": 2},
            {"query": "Sri Lankan movies", "category": "entertainment", "priority": 3},
            {"query": "Sri Lankan news", "category": "news", "priority": 1},
            {"query": "Sri Lankan cricket", "category": "sports", "priority": 2},
            
            # Tourism and travel
            {"query": "Sri Lanka tourism", "category": "travel", "priority": 2},
            {"query": "Visit Sri Lanka", "category": "travel", "priority": 3},
            {"query": "Sri Lanka beaches", "category": "travel", "priority": 3},
            {"query": "Sigiriya", "category": "travel", "priority": 3},
            
            # Current events and trending
            {"query": "Sri Lanka today", "category": "current", "priority": 1},
            {"query": "Sri Lanka update", "category": "current", "priority": 2},
            {"query": "Ceylon", "category": "historical", "priority": 3},
        ]
    
    async def run_extraction_cycle(self, config: ExtractionConfig) -> Dict[str, Any]:
        """Run a single extraction cycle with the given configuration."""
        if self.is_running:
            raise ValueError("Extraction already running")
        
        self.is_running = True
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        
        try:
            # Start extraction session
            session_config = config.dict()
            self.database_service.start_extraction_session(session_id, session_config)
            
            # Update global status
            extraction_status.update({
                "is_running": True,
                "current_session_id": session_id,
                "current_message": f"Starting extraction for: {config.query}",
                "start_time": datetime.now(),
                "videos_processed": 0
            })
            
            logger.info(f"Starting extraction cycle for query: {config.query}")
            
            # Search for videos
            videos = await self.youtube_service.search_videos(
                query=config.query,
                max_results=config.max_results,
                published_after=config.published_after,
                published_before=config.published_before,
                order=config.order,
                region_code=config.region_code
            )
            
            if not videos:
                logger.warning(f"No videos found for query: {config.query}")
                return {"videos_processed": 0, "sri_lankan_videos": 0}
            
            # Get detailed video information
            video_ids = [video['video_id'] for video in videos]
            detailed_videos = await self.youtube_service.get_video_details(video_ids)
            
            # Process and analyze videos
            processed_videos = []
            sri_lankan_count = 0
            
            for video in detailed_videos:
                # Skip if already processed recently
                if self.database_service.is_video_processed(video['video_id']):
                    continue
                
                # Analyze content
                analysis_result = self.content_analysis_service.analyze_content(video)
                
                # Merge analysis with video data
                video.update(analysis_result)
                video['search_query'] = config.query
                video['extraction_date'] = datetime.now().isoformat()
                video['video_url'] = f"https://www.youtube.com/watch?v={video['video_id']}"
                
                # Calculate engagement rate
                if video.get('view_count', 0) > 0:
                    video['engagement_rate'] = (video.get('like_count', 0) + 
                                               video.get('comment_count', 0) * 2) / video['view_count']
                else:
                    video['engagement_rate'] = 0.0
                
                processed_videos.append(video)
                
                if video.get('is_sri_lankan_content', False):
                    sri_lankan_count += 1
            
            # Save to cache
            saved_count = self.database_service.save_videos_batch(processed_videos)
            
            # Save to external services
            await self._save_to_external_services(processed_videos, config.query)
            
            # Update session
            self.database_service.update_extraction_session(
                session_id,
                status='completed',
                videos_extracted=len(processed_videos),
                sri_lankan_videos=sri_lankan_count
            )
            
            # Update global status
            extraction_status.update({
                "videos_processed": len(processed_videos),
                "last_extraction": datetime.now().isoformat(),
                "current_message": f"Completed extraction: {len(processed_videos)} videos processed"
            })
            
            logger.info(f"Extraction completed: {len(processed_videos)} videos, {sri_lankan_count} Sri Lankan")
            
            return {
                "session_id": session_id,
                "videos_processed": len(processed_videos),
                "sri_lankan_videos": sri_lankan_count,
                "saved_to_cache": saved_count,
                "extraction_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in extraction cycle: {e}")
            
            # Update session as failed
            if session_id:
                self.database_service.update_extraction_session(
                    session_id,
                    status='failed'
                )
            
            # Update global status
            extraction_status.update({
                "current_message": f"Extraction failed: {str(e)}"
            })
            
            raise
            
        finally:
            self.is_running = False
            extraction_status["is_running"] = False
            self.current_session_id = None
    
    async def run_comprehensive_scheduled_extraction(self) -> Dict[str, Any]:
        """Run comprehensive extraction using all search strategies."""
        if self.is_running:
            raise ValueError("Extraction already running")
        
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.is_running = True
        
        try:
            logger.info("Starting comprehensive scheduled extraction")
            
            # Initialize session
            session_config = {
                "type": "comprehensive",
                "strategies_count": len(self.search_strategies),
                "max_results_per_strategy": 50
            }
            
            self.database_service.start_extraction_session(session_id, session_config)
            
            # Update global status
            extraction_status.update({
                "is_running": True,
                "current_session_id": session_id,
                "current_message": "Starting comprehensive extraction",
                "start_time": datetime.now(),
                "videos_processed": 0,
                "total_strategies": len(self.search_strategies),
                "completed_strategies": 0
            })
            
            total_videos = 0
            total_sri_lankan = 0
            
            # Process each search strategy
            for i, strategy in enumerate(self.search_strategies):
                try:
                    extraction_status["current_message"] = f"Processing strategy {i+1}/{len(self.search_strategies)}: {strategy['query']}"
                    extraction_status["completed_strategies"] = i
                    
                    config = ExtractionConfig(
                        query=strategy['query'],
                        max_results=50,  # Reasonable limit per strategy
                        order='relevance'
                    )
                    
                    result = await self.run_single_strategy(config, session_id)
                    total_videos += result['videos_processed']
                    total_sri_lankan += result['sri_lankan_videos']
                    
                    # Small delay between strategies to avoid rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing strategy '{strategy['query']}': {e}")
                    continue
            
            # Update final session status
            self.database_service.update_extraction_session(
                session_id,
                status='completed',
                total_queries=len(self.search_strategies),
                completed_queries=len(self.search_strategies),
                videos_extracted=total_videos,
                sri_lankan_videos=total_sri_lankan
            )
            
            # Update global status
            extraction_status.update({
                "videos_processed": total_videos,
                "last_extraction": datetime.now().isoformat(),
                "current_message": f"Comprehensive extraction completed: {total_videos} videos processed",
                "completed_strategies": len(self.search_strategies)
            })
            
            logger.info(f"Comprehensive extraction completed: {total_videos} total videos, {total_sri_lankan} Sri Lankan")
            
            return {
                "session_id": session_id,
                "total_videos": total_videos,
                "sri_lankan_videos": total_sri_lankan,
                "strategies_processed": len(self.search_strategies),
                "completion_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive extraction: {e}")
            
            if session_id:
                self.database_service.update_extraction_session(
                    session_id,
                    status='failed'
                )
            
            extraction_status.update({
                "current_message": f"Comprehensive extraction failed: {str(e)}"
            })
            
            raise
            
        finally:
            self.is_running = False
            extraction_status["is_running"] = False
            self.current_session_id = None
    
    async def run_single_strategy(self, config: ExtractionConfig, parent_session_id: str = None) -> Dict[str, Any]:
        """Run extraction for a single strategy (used by comprehensive extraction)."""
        try:
            # Search for videos
            videos = await self.youtube_service.search_videos(
                query=config.query,
                max_results=config.max_results,
                order=config.order
            )
            
            if not videos:
                return {"videos_processed": 0, "sri_lankan_videos": 0}
            
            # Get detailed video information
            video_ids = [video['video_id'] for video in videos]
            detailed_videos = await self.youtube_service.get_video_details(video_ids)
            
            # Process and analyze videos
            processed_videos = []
            sri_lankan_count = 0
            
            for video in detailed_videos:
                # Skip if already processed recently
                if self.database_service.is_video_processed(video['video_id']):
                    continue
                
                # Analyze content
                analysis_result = self.content_analysis_service.analyze_content(video)
                
                # Merge analysis with video data
                video.update(analysis_result)
                video['search_query'] = config.query
                video['extraction_date'] = datetime.now().isoformat()
                video['video_url'] = f"https://www.youtube.com/watch?v={video['video_id']}"
                
                # Calculate engagement rate
                if video.get('view_count', 0) > 0:
                    video['engagement_rate'] = (video.get('like_count', 0) + 
                                               video.get('comment_count', 0) * 2) / video['view_count']
                else:
                    video['engagement_rate'] = 0.0
                
                processed_videos.append(video)
                
                if video.get('is_sri_lankan_content', False):
                    sri_lankan_count += 1
            
            # Save to cache
            self.database_service.save_videos_batch(processed_videos)
            
            # Save to external services (for Sri Lankan content only in comprehensive mode)
            sri_lankan_videos = [v for v in processed_videos if v.get('is_sri_lankan_content', False)]
            if sri_lankan_videos:
                await self._save_to_external_services(sri_lankan_videos, config.query)
            
            return {
                "videos_processed": len(processed_videos),
                "sri_lankan_videos": sri_lankan_count
            }
            
        except Exception as e:
            logger.error(f"Error in single strategy extraction: {e}")
            return {"videos_processed": 0, "sri_lankan_videos": 0}
    
    async def run_targeted_extraction(self, targets: List[str], max_results: int = 25) -> Dict[str, Any]:
        """Run targeted extraction for specific queries."""
        if self.is_running:
            raise ValueError("Extraction already running")
        
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.is_running = True
        
        try:
            logger.info(f"Starting targeted extraction for {len(targets)} targets")
            
            session_config = {
                "type": "targeted",
                "targets": targets,
                "max_results_per_target": max_results
            }
            
            self.database_service.start_extraction_session(session_id, session_config)
            
            extraction_status.update({
                "is_running": True,
                "current_session_id": session_id,
                "current_message": "Starting targeted extraction",
                "start_time": datetime.now(),
                "videos_processed": 0
            })
            
            total_videos = 0
            total_sri_lankan = 0
            
            for target in targets:
                try:
                    config = ExtractionConfig(
                        query=target,
                        max_results=max_results,
                        order='relevance'
                    )
                    
                    result = await self.run_single_strategy(config, session_id)
                    total_videos += result['videos_processed']
                    total_sri_lankan += result['sri_lankan_videos']
                    
                    # Update progress
                    extraction_status["videos_processed"] = total_videos
                    extraction_status["current_message"] = f"Processed target: {target}"
                    
                except Exception as e:
                    logger.error(f"Error processing target '{target}': {e}")
                    continue
            
            # Update session
            self.database_service.update_extraction_session(
                session_id,
                status='completed',
                videos_extracted=total_videos,
                sri_lankan_videos=total_sri_lankan
            )
            
            extraction_status.update({
                "videos_processed": total_videos,
                "last_extraction": datetime.now().isoformat(),
                "current_message": f"Targeted extraction completed: {total_videos} videos processed"
            })
            
            logger.info(f"Targeted extraction completed: {total_videos} videos, {total_sri_lankan} Sri Lankan")
            
            return {
                "session_id": session_id,
                "targets_processed": len(targets),
                "total_videos": total_videos,
                "sri_lankan_videos": total_sri_lankan,
                "completion_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in targeted extraction: {e}")
            
            if session_id:
                self.database_service.update_extraction_session(
                    session_id,
                    status='failed'
                )
            
            extraction_status.update({
                "current_message": f"Targeted extraction failed: {str(e)}"
            })
            
            raise
            
        finally:
            self.is_running = False
            extraction_status["is_running"] = False
            self.current_session_id = None
    
    async def _save_to_external_services(self, videos: List[Dict[str, Any]], query: str):
        """Save videos to external services (BigQuery and GCS)."""
        try:
            # Prepare filename for GCS
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"extraction_{timestamp}_{query.replace(' ', '_')}.json"
            
            # Save to GCS
            if self.gcs_service.is_available():
                try:
                    metadata = {
                        'extraction_date': datetime.now().isoformat(),
                        'record_count': str(len(videos)),
                        'extractor_version': settings.app_version,
                        'search_query': query,
                        'content_type': 'youtube_video_data'
                    }
                    
                    success = self.gcs_service.save_json(videos, filename, metadata)
                    if success:
                        logger.info(f"Saved {len(videos)} videos to GCS: {filename}")
                    else:
                        logger.warning("Failed to save to GCS")
                        
                except Exception as e:
                    logger.error(f"Error saving to GCS: {e}")
            
            # Save to BigQuery
            if self.bigquery_service.is_available():
                try:
                    errors = self.bigquery_service.insert_video_data(videos)
                    if not errors:
                        logger.info(f"Saved {len(videos)} videos to BigQuery")
                    else:
                        logger.error(f"BigQuery errors: {errors}")
                        
                except Exception as e:
                    logger.error(f"Error saving to BigQuery: {e}")
                    
        except Exception as e:
            logger.error(f"Error in external services save: {e}")
    
    def get_extraction_status(self) -> Dict[str, Any]:
        """Get current extraction status with detailed information."""
        base_status = extraction_status.copy()
        
        # Add service status
        base_status.update({
            "services": {
                "youtube_api": len(self.youtube_service.api_keys) > 0,
                "bigquery": self.bigquery_service.is_available(),
                "gcs": self.gcs_service.is_available(),
                "database": True  # Always available as it's SQLite
            },
            "api_key_status": self.youtube_service.get_api_key_status(),
            "cache_stats": self.database_service.get_cache_stats(),
            "current_time": datetime.now().isoformat()
        })
        
        # Add session information if available
        if self.current_session_id:
            session_data = self.database_service.get_extraction_session(self.current_session_id)
            if session_data:
                base_status["current_session"] = session_data
        
        return base_status
    
    def stop_extraction(self) -> bool:
        """Stop current extraction (graceful shutdown)."""
        if not self.is_running:
            return False
        
        logger.info("Stopping extraction...")
        
        # Update session status
        if self.current_session_id:
            self.database_service.update_extraction_session(
                self.current_session_id,
                status='stopped'
            )
        
        # Update global status
        extraction_status.update({
            "is_running": False,
            "current_message": "Extraction stopped by user request"
        })
        
        self.is_running = False
        return True


# Global extractor instance
extractor = YouTubeExtractor()