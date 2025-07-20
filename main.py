import os
import time
import json
import logging
import threading
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, jsonify
import requests
from google.cloud import bigquery
from google.cloud import storage
import uuid
from concurrent.futures import ThreadPoolExecutor
import schedule

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class APIKeyManager:
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_index = 0
        self.key_status = {}
        self.quota_reset_time = {}
        
        # Initialize status for all keys
        for key in self.api_keys:
            self.key_status[key] = {'active': True, 'requests_made': 0, 'last_error': None}
    
    def get_current_key(self):
        """Get the current active API key"""
        attempts = 0
        while attempts < len(self.api_keys):
            current_key = self.api_keys[self.current_index]
            
            # Check if key is active and not at quota limit
            if self.key_status[current_key]['active']:
                return current_key
            
            # Try next key
            self.rotate_key()
            attempts += 1
        
        # All keys exhausted, check if any can be reactivated
        self._check_quota_reset()
        return self.api_keys[self.current_index] if self.api_keys else None
    
    def rotate_key(self):
        """Rotate to the next API key"""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        logging.info(f"Rotated to API key index: {self.current_index}")
    
    def mark_key_exhausted(self, api_key, error_message=None):
        """Mark an API key as exhausted"""
        self.key_status[api_key]['active'] = False
        self.key_status[api_key]['last_error'] = error_message
        self.quota_reset_time[api_key] = datetime.now() + timedelta(hours=24)
        logging.warning(f"API key exhausted: {api_key[:10]}... Error: {error_message}")
        
        # Auto-rotate to next key
        self.rotate_key()
    
    def _check_quota_reset(self):
        """Check if any exhausted keys can be reactivated"""
        current_time = datetime.now()
        for key in self.api_keys:
            if not self.key_status[key]['active'] and key in self.quota_reset_time:
                if current_time >= self.quota_reset_time[key]:
                    self.key_status[key]['active'] = True
                    self.key_status[key]['requests_made'] = 0
                    logging.info(f"Reactivated API key: {key[:10]}...")
    
    def get_status_summary(self):
        """Get summary of all API key statuses"""
        summary = []
        for i, key in enumerate(self.api_keys):
            status = self.key_status[key]
            summary.append({
                'index': i,
                'key_preview': key[:10] + '...',
                'active': status['active'],
                'requests_made': status['requests_made'],
                'last_error': status['last_error'],
                'is_current': i == self.current_index
            })
        return summary

class ContinuousYouTubeExtractor:
    def __init__(self, api_keys, storage_manager):
        self.api_key_manager = APIKeyManager(api_keys)
        self.storage_manager = storage_manager
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.is_running = False
        self.extraction_stats = {
            'total_videos': 0,
            'total_requests': 0,
            'start_time': None,
            'last_extraction': None,
            'errors': 0
        }
        
        # Search configuration
        self.search_configs = [
            {'query': '', 'order': 'date'},  # Latest videos
            {'query': '', 'order': 'viewCount'},  # Most viewed
            {'query': 'sri lanka', 'order': 'relevance'},
            {'query': 'colombo', 'order': 'relevance'},
            {'query': 'sinhala', 'order': 'date'},
            {'query': 'tamil', 'order': 'date'},
            {'query': 'news sri lanka', 'order': 'date'},
            {'query': 'music sri lanka', 'order': 'viewCount'},
            {'query': 'travel sri lanka', 'order': 'relevance'},
            {'query': 'food sri lanka', 'order': 'relevance'},
        ]
        self.current_config_index = 0
        
    def make_api_request(self, endpoint, params, max_retries=3):
        """Make API request with automatic key rotation on quota exhaustion"""
        for attempt in range(max_retries):
            current_key = self.api_key_manager.get_current_key()
            if not current_key:
                return {'error': 'All API keys exhausted'}
            
            params['key'] = current_key
            
            try:
                response = requests.get(endpoint, params=params, timeout=30)
                
                # Check for quota exceeded
                if response.status_code == 403:
                    error_data = response.json().get('error', {})
                    error_reason = error_data.get('errors', [{}])[0].get('reason', '')
                    
                    if error_reason in ['quotaExceeded', 'dailyLimitExceeded']:
                        self.api_key_manager.mark_key_exhausted(current_key, f"Quota exceeded: {error_reason}")
                        continue  # Try with next key
                
                response.raise_for_status()
                self.api_key_manager.key_status[current_key]['requests_made'] += 1
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return {'error': f'API request failed after {max_retries} attempts: {str(e)}'}
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {'error': 'Max retries exceeded'}
    
    def search_videos(self, query="", region_code="LK", max_results=50, order="relevance"):
        """Search for videos with current API key"""
        endpoint = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'type': 'video',
            'regionCode': region_code,
            'maxResults': max_results,
            'order': order
        }
        
        if query:
            params['q'] = query
            
        return self.make_api_request(endpoint, params)
    
    def get_video_details(self, video_ids):
        """Get detailed video information"""
        if isinstance(video_ids, list):
            video_ids = ','.join(video_ids)
        
        endpoint = f"{self.base_url}/videos"
        params = {
            'part': 'snippet,statistics,contentDetails',
            'id': video_ids
        }
        
        return self.make_api_request(endpoint, params)
    
    def extract_and_store_batch(self, search_config):
        """Extract a batch of videos and store them"""
        try:
            # Search for videos
            search_results = self.search_videos(
                query=search_config['query'],
                order=search_config['order'],
                max_results=50  # Maximum per request
            )
            
            if 'error' in search_results:
                logging.error(f"Search failed: {search_results['error']}")
                self.extraction_stats['errors'] += 1
                return False
            
            video_ids = [item['id']['videoId'] for item in search_results.get('items', [])]
            if not video_ids:
                logging.info("No videos found in search results")
                return True
            
            # Get detailed video information
            video_details = self.get_video_details(video_ids)
            if 'error' in video_details:
                logging.error(f"Video details failed: {video_details['error']}")
                self.extraction_stats['errors'] += 1
                return False
            
            # Process videos
            processed_videos = []
            for video in video_details.get('items', []):
                video_data = {
                    'id': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'][:1000],  # Limit description length
                    'channel_title': video['snippet']['channelTitle'],
                    'channel_id': video['snippet']['channelId'],
                    'published_at': video['snippet']['publishedAt'],
                    'thumbnail': video['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'duration': video['contentDetails']['duration'],
                    'view_count': int(video['statistics'].get('viewCount', 0)),
                    'like_count': int(video['statistics'].get('likeCount', 0)),
                    'comment_count': int(video['statistics'].get('commentCount', 0)),
                    'url': f"https://www.youtube.com/watch?v={video['id']}"
                }
                processed_videos.append(video_data)
            
            # Store to database
            if processed_videos:
                extraction_id = str(uuid.uuid4())
                query_text = search_config['query'] if search_config['query'] else f"no_query_{search_config['order']}"
                
                # Store to BigQuery
                bigquery_result = self.storage_manager.store_to_bigquery(
                    processed_videos, query_text, extraction_id
                )
                
                # Store to Cloud Storage as backup
                storage_result = self.storage_manager.store_to_cloud_storage(
                    processed_videos, query_text, extraction_id
                )
                
                if bigquery_result.get('success'):
                    self.extraction_stats['total_videos'] += len(processed_videos)
                    self.extraction_stats['last_extraction'] = datetime.now()
                    logging.info(f"Stored {len(processed_videos)} videos for query: '{query_text}'")
                else:
                    logging.error(f"Storage failed: {bigquery_result.get('error')}")
                    self.extraction_stats['errors'] += 1
            
            self.extraction_stats['total_requests'] += 2  # Search + details requests
            return True
            
        except Exception as e:
            logging.error(f"Batch extraction failed: {str(e)}")
            self.extraction_stats['errors'] += 1
            return False
    
    def run_continuous_extraction(self):
        """Run continuous extraction until all API keys are exhausted"""
        self.is_running = True
        self.extraction_stats['start_time'] = datetime.now()
        
        logging.info("Starting continuous YouTube data extraction...")
        logging.info(f"Using {len(self.api_key_manager.api_keys)} API keys")
        
        while self.is_running:
            # Check if any API keys are available
            if not any(status['active'] for status in self.api_key_manager.key_status.values()):
                logging.info("All API keys exhausted. Waiting for quota reset...")
                time.sleep(3600)  # Wait 1 hour before checking again
                self.api_key_manager._check_quota_reset()
                continue
            
            # Get current search configuration
            search_config = self.search_configs[self.current_config_index]
            
            # Extract batch
            success = self.extract_and_store_batch(search_config)
            
            if success:
                # Move to next search configuration
                self.current_config_index = (self.current_config_index + 1) % len(self.search_configs)
                
                # Add delay to avoid hitting rate limits too quickly
                time.sleep(5)  # 5 seconds between batches
            else:
                # On failure, wait longer before retrying
                time.sleep(30)
        
        logging.info("Continuous extraction stopped")
    
    def stop_extraction(self):
        """Stop the continuous extraction"""
        self.is_running = False
    
    def get_status(self):
        """Get current extraction status"""
        return {
            'is_running': self.is_running,
            'stats': self.extraction_stats,
            'api_keys': self.api_key_manager.get_status_summary(),
            'current_search_config': self.search_configs[self.current_config_index]
        }

# Global extractor instance
continuous_extractor = None

def initialize_extractor():
    """Initialize the continuous extractor"""
    global continuous_extractor
    
    # Get API keys from environment
    api_keys_str = os.environ.get('YOUTUBE_API_KEYS', '')
    api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
    
    if not api_keys:
        logging.error("No API keys provided in YOUTUBE_API_KEYS environment variable")
        return None
    
    # Initialize storage manager
    from main import DataStorageManager  # Import from your main module
    storage_manager = DataStorageManager()
    
    continuous_extractor = ContinuousYouTubeExtractor(api_keys, storage_manager)
    return continuous_extractor

@app.route('/')
def index():
    return render_template('continuous_dashboard.html')

@app.route('/api/start-extraction', methods=['POST'])
def start_extraction():
    """Start continuous extraction in background thread"""
    global continuous_extractor
    
    if not continuous_extractor:
        continuous_extractor = initialize_extractor()
    
    if not continuous_extractor:
        return jsonify({'error': 'Failed to initialize extractor'}), 500
    
    if continuous_extractor.is_running:
        return jsonify({'message': 'Extraction already running'})
    
    # Start extraction in background thread
    extraction_thread = threading.Thread(
        target=continuous_extractor.run_continuous_extraction,
        daemon=True
    )
    extraction_thread.start()
    
    return jsonify({'message': 'Continuous extraction started'})

@app.route('/api/stop-extraction', methods=['POST'])
def stop_extraction():
    """Stop continuous extraction"""
    global continuous_extractor
    
    if continuous_extractor:
        continuous_extractor.stop_extraction()
        return jsonify({'message': 'Extraction stopped'})
    
    return jsonify({'message': 'No extraction running'})

@app.route('/api/extraction-status', methods=['GET'])
def get_extraction_status():
    """Get current extraction status"""
    global continuous_extractor
    
    if not continuous_extractor:
        return jsonify({
            'is_running': False,
            'error': 'Extractor not initialized'
        })
    
    return jsonify(continuous_extractor.get_status())

@app.route('/api/update-search-configs', methods=['POST'])
def update_search_configs():
    """Update search configurations"""
    global continuous_extractor
    
    if not continuous_extractor:
        return jsonify({'error': 'Extractor not initialized'}), 500
    
    data = request.get_json()
    new_configs = data.get('configs', [])
    
    if not new_configs:
        return jsonify({'error': 'No configurations provided'}), 400
    
    continuous_extractor.search_configs = new_configs
    continuous_extractor.current_config_index = 0
    
    return jsonify({'message': f'Updated {len(new_configs)} search configurations'})

# Auto-start extraction when app starts
@app.before_first_request
def auto_start_extraction():
    """Auto-start extraction if enabled"""
    auto_start = os.environ.get('AUTO_START_EXTRACTION', 'false').lower() == 'true'
    
    if auto_start:
        global continuous_extractor
        continuous_extractor = initialize_extractor()
        
        if continuous_extractor:
            extraction_thread = threading.Thread(
                target=continuous_extractor.run_continuous_extraction,
                daemon=True
            )
            extraction_thread.start()
            logging.info("Auto-started continuous extraction")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)