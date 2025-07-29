import logging
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import threading

from ..config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for SQLite database operations including caching and deduplication."""
    
    def __init__(self):
        self.db_path = settings.database_path
        self.lock = threading.Lock()
        self._ensure_directories()
        self._initialize_database()
    
    def _ensure_directories(self):
        """Ensure database directory exists."""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database tables."""
        try:
            with self.get_connection() as conn:
                # Create videos cache table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS videos (
                        video_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        channel_title TEXT NOT NULL,
                        published_at TEXT NOT NULL,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        duration TEXT,
                        tags TEXT,  -- JSON array
                        category_id TEXT,
                        language TEXT,
                        description TEXT,
                        thumbnail_url TEXT,
                        video_url TEXT,
                        search_query TEXT,
                        extraction_date TEXT NOT NULL,
                        is_sri_lankan_content BOOLEAN DEFAULT FALSE,
                        content_score REAL DEFAULT 0.0,
                        quality_score REAL DEFAULT 0.0,
                        engagement_rate REAL DEFAULT 0.0,
                        last_updated TEXT NOT NULL,
                        metadata TEXT  -- JSON for additional data
                    )
                ''')
                
                # Create API usage log table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS api_usage_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_key_hash TEXT NOT NULL,
                        request_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        quota_cost INTEGER DEFAULT 1,
                        error_message TEXT,
                        response_time REAL
                    )
                ''')
                
                # Create extraction sessions table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS extraction_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT NOT NULL,  -- running, completed, failed
                        total_queries INTEGER DEFAULT 0,
                        completed_queries INTEGER DEFAULT 0,
                        videos_extracted INTEGER DEFAULT 0,
                        sri_lankan_videos INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        configuration TEXT,  -- JSON
                        metadata TEXT  -- JSON
                    )
                ''')
                
                # Create search queries table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS search_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        category TEXT,
                        last_used TEXT,
                        usage_count INTEGER DEFAULT 1,
                        success_rate REAL DEFAULT 1.0,
                        avg_results INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_extraction_date ON videos(extraction_date)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_sri_lankan ON videos(is_sri_lankan_content)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage_log(timestamp)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON extraction_sessions(status)')
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                yield conn
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def is_video_processed(self, video_id: str, max_age_hours: int = 24) -> bool:
        """Check if video has been processed recently."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cutoff_str = cutoff_time.isoformat()
            
            with self.get_connection() as conn:
                result = conn.execute(
                    'SELECT 1 FROM videos WHERE video_id = ? AND last_updated > ?',
                    (video_id, cutoff_str)
                ).fetchone()
                
                return result is not None
                
        except Exception as e:
            logger.error(f"Error checking video processed status: {e}")
            return False
    
    def save_video(self, video_data: Dict[str, Any]) -> bool:
        """Save or update video data in cache."""
        try:
            with self.get_connection() as conn:
                # Prepare data
                now = datetime.now().isoformat()
                tags_json = json.dumps(video_data.get('tags', []))
                metadata_json = json.dumps(video_data.get('metadata', {}))
                
                # Insert or replace video
                conn.execute('''
                    INSERT OR REPLACE INTO videos (
                        video_id, title, channel_id, channel_title, published_at,
                        view_count, like_count, comment_count, duration, tags,
                        category_id, language, description, thumbnail_url, video_url,
                        search_query, extraction_date, is_sri_lankan_content,
                        content_score, quality_score, engagement_rate, last_updated, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data.get('video_id'),
                    video_data.get('title'),
                    video_data.get('channel_id'),
                    video_data.get('channel_title'),
                    video_data.get('published_at'),
                    video_data.get('view_count', 0),
                    video_data.get('like_count', 0),
                    video_data.get('comment_count', 0),
                    video_data.get('duration'),
                    tags_json,
                    video_data.get('category_id'),
                    video_data.get('language'),
                    video_data.get('description'),
                    video_data.get('thumbnail_url'),
                    video_data.get('video_url'),
                    video_data.get('search_query'),
                    video_data.get('extraction_date', now),
                    video_data.get('is_sri_lankan_content', False),
                    video_data.get('content_score', 0.0),
                    video_data.get('quality_score', 0.0),
                    video_data.get('engagement_rate', 0.0),
                    now,
                    metadata_json
                ))
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving video: {e}")
            return False
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video data from cache."""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM videos WHERE video_id = ?',
                    (video_id,)
                ).fetchone()
                
                if row:
                    video_data = dict(row)
                    # Parse JSON fields
                    video_data['tags'] = json.loads(video_data['tags']) if video_data['tags'] else []
                    video_data['metadata'] = json.loads(video_data['metadata']) if video_data['metadata'] else {}
                    return video_data
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting video: {e}")
            return None
    
    def save_videos_batch(self, videos: List[Dict[str, Any]]) -> int:
        """Save multiple videos in a batch operation."""
        saved_count = 0
        
        try:
            with self.get_connection() as conn:
                now = datetime.now().isoformat()
                
                for video_data in videos:
                    try:
                        tags_json = json.dumps(video_data.get('tags', []))
                        metadata_json = json.dumps(video_data.get('metadata', {}))
                        
                        conn.execute('''
                            INSERT OR REPLACE INTO videos (
                                video_id, title, channel_id, channel_title, published_at,
                                view_count, like_count, comment_count, duration, tags,
                                category_id, language, description, thumbnail_url, video_url,
                                search_query, extraction_date, is_sri_lankan_content,
                                content_score, quality_score, engagement_rate, last_updated, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            video_data.get('video_id'),
                            video_data.get('title'),
                            video_data.get('channel_id'),
                            video_data.get('channel_title'),
                            video_data.get('published_at'),
                            video_data.get('view_count', 0),
                            video_data.get('like_count', 0),
                            video_data.get('comment_count', 0),
                            video_data.get('duration'),
                            tags_json,
                            video_data.get('category_id'),
                            video_data.get('language'),
                            video_data.get('description'),
                            video_data.get('thumbnail_url'),
                            video_data.get('video_url'),
                            video_data.get('search_query'),
                            video_data.get('extraction_date', now),
                            video_data.get('is_sri_lankan_content', False),
                            video_data.get('content_score', 0.0),
                            video_data.get('quality_score', 0.0),
                            video_data.get('engagement_rate', 0.0),
                            now,
                            metadata_json
                        ))
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error saving individual video in batch: {e}")
                        continue
                
                logger.info(f"Saved {saved_count}/{len(videos)} videos to cache")
                return saved_count
                
        except Exception as e:
            logger.error(f"Error in batch save: {e}")
            return saved_count
    
    def log_api_usage(self, api_key: str, request_type: str, success: bool,
                     quota_cost: int = 1, error_message: str = None,
                     response_time: float = None) -> bool:
        """Log API usage for monitoring."""
        try:
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO api_usage_log 
                    (api_key_hash, request_type, timestamp, success, quota_cost, error_message, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    api_key_hash,
                    request_type,
                    datetime.now().isoformat(),
                    success,
                    quota_cost,
                    error_message,
                    response_time
                ))
                
                return True
                
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            return False
    
    def start_extraction_session(self, session_id: str, configuration: Dict[str, Any]) -> bool:
        """Start a new extraction session."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO extraction_sessions 
                    (session_id, start_time, status, configuration)
                    VALUES (?, ?, ?, ?)
                ''', (
                    session_id,
                    datetime.now().isoformat(),
                    'running',
                    json.dumps(configuration)
                ))
                
                return True
                
        except Exception as e:
            logger.error(f"Error starting extraction session: {e}")
            return False
    
    def update_extraction_session(self, session_id: str, **updates) -> bool:
        """Update extraction session progress."""
        try:
            with self.get_connection() as conn:
                # Build update query dynamically
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['status', 'total_queries', 'completed_queries', 
                              'videos_extracted', 'sri_lankan_videos', 'error_count']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if 'status' in updates and updates['status'] in ['completed', 'failed']:
                    set_clauses.append("end_time = ?")
                    values.append(datetime.now().isoformat())
                
                if set_clauses:
                    query = f"UPDATE extraction_sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
                    values.append(session_id)
                    
                    conn.execute(query, values)
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating extraction session: {e}")
            return False
    
    def get_extraction_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get extraction session data."""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM extraction_sessions WHERE session_id = ?',
                    (session_id,)
                ).fetchone()
                
                if row:
                    session_data = dict(row)
                    session_data['configuration'] = json.loads(session_data['configuration']) if session_data['configuration'] else {}
                    session_data['metadata'] = json.loads(session_data['metadata']) if session_data['metadata'] else {}
                    return session_data
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting extraction session: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with self.get_connection() as conn:
                # Video statistics
                video_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_videos,
                        SUM(CASE WHEN is_sri_lankan_content THEN 1 ELSE 0 END) as sri_lankan_videos,
                        AVG(content_score) as avg_content_score,
                        COUNT(DISTINCT channel_id) as unique_channels,
                        MIN(extraction_date) as oldest_video,
                        MAX(extraction_date) as newest_video
                    FROM videos
                ''').fetchone()
                
                # Recent activity (last 24 hours)
                cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
                recent_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as recent_videos,
                        SUM(CASE WHEN is_sri_lankan_content THEN 1 ELSE 0 END) as recent_sri_lankan
                    FROM videos
                    WHERE extraction_date > ?
                ''', (cutoff,)).fetchone()
                
                # API usage statistics
                api_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                        AVG(response_time) as avg_response_time
                    FROM api_usage_log
                    WHERE timestamp > ?
                ''', (cutoff,)).fetchone()
                
                # Database size
                db_size = conn.execute('PRAGMA page_count').fetchone()[0] * conn.execute('PRAGMA page_size').fetchone()[0]
                
                return {
                    'total_videos': video_stats['total_videos'],
                    'sri_lankan_videos': video_stats['sri_lankan_videos'],
                    'unique_channels': video_stats['unique_channels'],
                    'avg_content_score': round(video_stats['avg_content_score'] or 0, 3),
                    'oldest_video': video_stats['oldest_video'],
                    'newest_video': video_stats['newest_video'],
                    'recent_videos_24h': recent_stats['recent_videos'],
                    'recent_sri_lankan_24h': recent_stats['recent_sri_lankan'],
                    'api_requests_24h': api_stats['total_requests'],
                    'api_success_rate_24h': (api_stats['successful_requests'] / max(api_stats['total_requests'], 1)) * 100,
                    'avg_response_time_24h': round(api_stats['avg_response_time'] or 0, 3),
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2)
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old data from cache."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            cleanup_stats = {'videos': 0, 'api_logs': 0, 'sessions': 0}
            
            with self.get_connection() as conn:
                # Clean old videos
                result = conn.execute(
                    'DELETE FROM videos WHERE extraction_date < ?',
                    (cutoff_date,)
                )
                cleanup_stats['videos'] = result.rowcount
                
                # Clean old API logs
                result = conn.execute(
                    'DELETE FROM api_usage_log WHERE timestamp < ?',
                    (cutoff_date,)
                )
                cleanup_stats['api_logs'] = result.rowcount
                
                # Clean old completed sessions
                result = conn.execute(
                    'DELETE FROM extraction_sessions WHERE end_time < ? AND status IN ("completed", "failed")',
                    (cutoff_date,)
                )
                cleanup_stats['sessions'] = result.rowcount
                
                # Vacuum to reclaim space
                conn.execute('VACUUM')
                
                logger.info(f"Cleaned up old data: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'videos': 0, 'api_logs': 0, 'sessions': 0}
    
    def search_videos(self, query: str, limit: int = 50, sri_lankan_only: bool = False) -> List[Dict[str, Any]]:
        """Search videos in cache."""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT * FROM videos 
                    WHERE (title LIKE ? OR description LIKE ? OR channel_title LIKE ?)
                '''
                
                params = [f'%{query}%', f'%{query}%', f'%{query}%']
                
                if sri_lankan_only:
                    base_query += ' AND is_sri_lankan_content = 1'
                
                base_query += ' ORDER BY extraction_date DESC LIMIT ?'
                params.append(limit)
                
                rows = conn.execute(base_query, params).fetchall()
                
                videos = []
                for row in rows:
                    video_data = dict(row)
                    video_data['tags'] = json.loads(video_data['tags']) if video_data['tags'] else []
                    video_data['metadata'] = json.loads(video_data['metadata']) if video_data['metadata'] else {}
                    videos.append(video_data)
                
                return videos
                
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []
    
    def get_top_channels(self, limit: int = 20, sri_lankan_only: bool = False) -> List[Dict[str, Any]]:
        """Get top channels by video count and engagement."""
        try:
            with self.get_connection() as conn:
                base_query = '''
                    SELECT 
                        channel_id,
                        channel_title,
                        COUNT(*) as video_count,
                        SUM(view_count) as total_views,
                        SUM(like_count) as total_likes,
                        AVG(content_score) as avg_content_score,
                        AVG(engagement_rate) as avg_engagement_rate
                    FROM videos
                '''
                
                where_clause = ''
                if sri_lankan_only:
                    where_clause = ' WHERE is_sri_lankan_content = 1'
                
                full_query = f'''
                    {base_query} {where_clause}
                    GROUP BY channel_id, channel_title
                    HAVING video_count >= 2
                    ORDER BY total_views DESC, avg_engagement_rate DESC
                    LIMIT ?
                '''
                
                rows = conn.execute(full_query, (limit,)).fetchall()
                
                channels = []
                for row in rows:
                    channels.append({
                        'channel_id': row['channel_id'],
                        'channel_title': row['channel_title'],
                        'video_count': row['video_count'],
                        'total_views': row['total_views'],
                        'total_likes': row['total_likes'],
                        'avg_content_score': round(row['avg_content_score'] or 0, 3),
                        'avg_engagement_rate': round(row['avg_engagement_rate'] or 0, 3)
                    })
                
                return channels
                
        except Exception as e:
            logger.error(f"Error getting top channels: {e}")
            return []
