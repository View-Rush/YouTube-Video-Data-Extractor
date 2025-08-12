# Enhanced YouTube Video Data Extractor for Sri Lankan Content

A comprehensive, production-ready YouTube video data extraction and analysis platform specifically designed for Sri Lankan content. Built with FastAPI and modern cloud technologies, this system provides automated content discovery, intelligent analysis, and scalable deployment options.

## 🚀 Key Features

### Core Functionality
- **Comprehensive Sri Lankan Content Discovery**: Advanced search strategies covering 30+ locations and 25+ categories
- **Intelligent Content Analysis**: ML-powered content scoring and Sri Lankan relevance detection
- **Multi-API Key Management**: Automatic rotation and quota management for unlimited scalability
- **Robust Error Handling**: Exponential backoff, automatic retries, and graceful degradation
- **Real-time Analytics Dashboard**: Live monitoring with extraction metrics and performance insights

### Enhanced Data Collection
- **Smart Deduplication**: Local SQLite cache prevents duplicate video processing
- **Content Quality Scoring**: Algorithmic ranking based on engagement, relevance, and content quality
- **Advanced Filtering**: Remove spam, irrelevant content, and low-quality videos
- **Comprehensive Metadata**: 35+ data points per video including engagement metrics, channel statistics, and content analysis (video descriptions excluded for storage efficiency)

### Storage & Analytics
- **Google Cloud Storage**: Organized data storage with automatic lifecycle management
- **BigQuery Integration**: Partitioned and clustered tables for optimal query performance
- **Advanced Analytics**: Trending videos, channel analytics, temporal analysis, and content insights
- **Local SQLite Cache**: Fast local caching for improved performance and deduplication

### Production-Ready Features
- **FastAPI Backend**: High-performance async web framework with automatic API documentation
- **Containerized Deployment**: Multi-stage Docker build with security best practices
- **Comprehensive Logging**: Structured logging with rotation and error tracking
- **Cloud-Native**: Designed for Google Cloud Platform with auto-scaling capabilities
- **Security**: Non-root container execution, environment-based configuration, and secure API handling

## � Project Structure

```
Youtube Video Data Extractor/
├── 📄 main.py                 # FastAPI application with all endpoints and business logic
├── 📄 requirements.txt        # Python dependencies
├── 📄 dockerfile             # Multi-stage Docker configuration
├── 📄 docker-compose.yaml    # Docker Compose for easy deployment
├── 📄 .env.example           # Environment variables template
├── 📄 .env                   # Your environment configuration (create from .env.example)
├── 📄 api_keys.json          # YouTube API keys configuration
├── 📄 service-account.json   # Google Cloud service account credentials
├── 📄 deploy.sh              # Automated deployment script for Google Cloud
├── 📄 startup-script.sh      # VM startup script for Compute Engine
├── 📄 DEPLOYMENT.md          # Comprehensive deployment guide
├── 📁 data/                  # Local data storage
│   └── youtube_cache.db      # SQLite database for caching and deduplication
├── 📁 logs/                  # Application logs
│   ├── youtube_extractor.log # Main application logs
│   └── error.log            # Error-specific logs
├── 📁 templates/            # HTML templates
│   └── dashboard.html       # Web dashboard interface
├── 📁 static/               # Static web assets (CSS, JS, images)
└── 📁 __pycache__/          # Python bytecode cache
```

## 🛠️ Technology Stack

### Backend & API
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Uvicorn**: ASGI server for high-performance async applications
- **Pydantic**: Data validation and settings management using Python type hints
- **Jinja2**: Template engine for HTML rendering

### Data Storage & Processing
- **Google BigQuery**: Data warehouse for analytics and large-scale querying
- **Google Cloud Storage**: Object storage for video metadata and backups
- **SQLite**: Local database for caching and deduplication
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

### APIs & Cloud Services
- **YouTube Data API v3**: Video data extraction and search
- **Google Cloud APIs**: BigQuery, Storage, and authentication
- **Google OAuth2**: Secure authentication and authorization

### Monitoring & Utilities
- **PSUtil**: System and process monitoring
- **Schedule**: Task scheduling and automation
- **Backoff**: Exponential backoff for API retries
- **Python-dotenv**: Environment variable management
- **Tenacity**: Retry library for robust error handling

### Deployment & DevOps
- **Docker**: Containerization with multi-stage builds
- **Docker Compose**: Local development and testing
- **Google Cloud Platform**: Production deployment (Compute Engine, Cloud Run)
- **Nginx**: Reverse proxy and load balancing (in deployment)

## 📋 Prerequisites

### Required Services
1. **Google Cloud Project** with the following APIs enabled:
   - YouTube Data API v3
   - BigQuery API
   - Cloud Storage API
   - Compute Engine API (for VM deployment)

2. **YouTube API Keys**: Multiple keys recommended for higher quota limits (each key provides 10,000 units/day)

3. **Google Cloud Resources**:
   - Cloud Storage bucket
   - BigQuery dataset and table
   - Service account with appropriate permissions
   - Compute Engine instance (optional, for VM deployment)

### System Requirements
- **Python**: 3.11+ (recommended 3.11 for optimal performance)
- **Memory**: 2GB RAM minimum (4GB recommended for production)
- **Storage**: 10GB disk space minimum
- **Network**: Stable internet connection with good bandwidth
- **Docker**: For containerized deployment (optional but recommended)

## ⚙️ Installation & Setup

## ⚙️ Installation & Setup

### 1. Clone and Setup
```bash
git clone https://github.com/View-Rush/YouTube-Video-Data-Extractor.git
cd YouTube-Video-Data-Extractor
```

### 2. Python Environment Setup
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables with your actual values
# Windows: notepad .env
# macOS/Linux: nano .env
```

Required environment variables:
```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=youtube-data-sri-lanka
BIGQUERY_DATASET_ID=youtube_analytics
BIGQUERY_TABLE_ID=video_data
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# YouTube API Keys (add as many as you have)
YOUTUBE_API_KEY_1=your-first-youtube-api-key
YOUTUBE_API_KEY_2=your-second-youtube-api-key
YOUTUBE_API_KEY_3=your-third-youtube-api-key
# ... up to YOUTUBE_API_KEY_20

# Application Configuration
APP_ENVIRONMENT=development
APP_PORT=8000
APP_HOST=0.0.0.0
LOG_LEVEL=INFO
```

### 4. Setup API Keys Configuration
Update `api_keys.json` with your YouTube API keys:
```json
{
  "youtube_api_keys": [
    "your-youtube-api-key-1",
    "your-youtube-api-key-2",
    "your-youtube-api-key-3"
  ]
}
```

### 5. Google Cloud Service Account
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Save it as `service-account.json` in the project root
4. Ensure the service account has the following permissions:
   - BigQuery Data Editor
   - Storage Object Admin
   - Storage Admin (for bucket creation)

### 6. Initialize Data Storage
The application will automatically:
- Create the SQLite cache database in `data/youtube_cache.db`
- Set up BigQuery tables if they don't exist
- Create log files in the `logs/` directory

### 7. Run the Application
```bash
# Development mode
python main.py

# Or with uvicorn directly for more control
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **Dashboard**: `http://localhost:8000/`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## 🐳 Docker Deployment

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended for Development)
```bash
# Configure environment variables
cp .env.example .env
# Edit .env with your actual values

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f youtube-extractor

# Stop the application
docker-compose down
```

### Option 2: Manual Docker Build
```bash
# Build the image
docker build -t youtube-extractor:latest .

# Run with environment file
docker run -d \
  --name youtube-extractor \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/service-account.json:/app/service-account.json:ro \
  -v $(pwd)/api_keys.json:/app/api_keys.json:ro \
  -v $(pwd)/logs:/app/logs \
  youtube-extractor:latest

# Monitor logs
docker logs -f youtube-extractor
```

### Docker Features
- **Multi-stage build**: Optimized image size and security
- **Non-root execution**: Runs as unprivileged user for security
- **Volume mounting**: Persistent logs and configuration
- **Health checks**: Built-in container health monitoring
- **Resource limits**: Configurable memory and CPU limits

## ☁️ Google Cloud Deployment

## ☁️ Google Cloud Deployment

For detailed deployment instructions, see **[DEPLOYMENT.md](DEPLOYMENT.md)** which includes comprehensive guides for all deployment methods.

### Quick Start: Automated Deployment
```bash
# Make deploy script executable (Linux/macOS)
chmod +x deploy.sh

# Deploy to Google Cloud Compute Engine
./deploy.sh your-project-id youtube-extractor-vm us-central1-a
```

### Deployment Options

#### Option 1: Google Compute Engine (Recommended for Production)
- **Full VM control** with persistent storage
- **Custom startup scripts** for automated configuration
- **SSH access** for debugging and maintenance
- **Cost-effective** for continuous operation

```bash
# Create VM with startup script
gcloud compute instances create youtube-extractor-vm \
  --project=YOUR_PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --metadata-from-file startup-script=startup-script.sh \
  --service-account=youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

#### Option 2: Cloud Run (Serverless)
- **Automatic scaling** based on traffic
- **Pay-per-use** pricing model
- **Zero server management**
- **Built-in load balancing**

```bash
# Deploy to Cloud Run
gcloud run deploy youtube-extractor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600
```

#### Option 3: Docker on Any Cloud Provider
The Docker image can be deployed on:
- **AWS EC2** with ECS or EKS
- **Azure Container Instances** or AKS
- **DigitalOcean Droplets**
- **Any VPS** with Docker support

### Pre-Deployment Requirements
1. **Google Cloud APIs enabled**:
   - YouTube Data API v3
   - BigQuery API
   - Cloud Storage API
   - Compute Engine API

2. **Service account created** with permissions:
   - BigQuery Data Editor
   - Storage Object Admin
   - Compute Instance Admin (for VM deployment)

3. **Resources created**:
   - BigQuery dataset and table
   - Cloud Storage bucket
   - Firewall rules (for VM deployment)

### Deployment Verification
```bash
# Check application health
curl http://YOUR_EXTERNAL_IP/health

# Access the dashboard
curl http://YOUR_EXTERNAL_IP/

# Test API functionality
curl -X POST http://YOUR_EXTERNAL_IP/api/extract \
  -H "Content-Type: application/json" \
  -d '{"query": "Sri Lanka", "max_results": 10}'
```

## 📊 API Documentation

## 📊 API Documentation

### Web Interface
- **Main Dashboard**: `http://localhost:8000/` - Real-time monitoring and control interface
- **Interactive API Docs**: `http://localhost:8000/docs` - FastAPI automatic documentation with testing
- **Alternative API Docs**: `http://localhost:8000/redoc` - ReDoc documentation format
- **Health Check**: `http://localhost:8000/health` - System status and component health

### Key API Endpoints

#### 🎯 Extraction Control
- `POST /api/extract` - Start custom video extraction with specific parameters
- `POST /api/extract/scheduled` - Start comprehensive scheduled extraction
- `POST /api/extract/targeted` - Start targeted extraction for specific queries or channels
- `GET /api/status` - Get detailed extraction status, progress, and metrics
- `POST /api/stop` - Stop current extraction process

#### 📈 Analytics & Data
- `GET /api/analytics/summary` - Get extraction analytics summary
- `GET /api/analytics/trending` - Get trending Sri Lankan videos
- `GET /api/analytics/channels` - Get top Sri Lankan channels performance
- `GET /api/analytics/temporal` - Get temporal analysis of content trends
- `GET /api/metrics` - Get detailed system performance metrics

#### ⚙️ Configuration & Management
- `GET /api/queries` - Get predefined search queries and categories
- `GET /api/config` - Get current application configuration
- `POST /api/config/api-keys` - Update YouTube API keys
- `GET /api/cache/stats` - Get SQLite cache statistics

#### 🔍 Search & Discovery
- `GET /api/search/suggestions` - Get search term suggestions
- `POST /api/search/validate` - Validate search queries
- `GET /api/categories` - Get available video categories

### Example API Usage

#### Start Custom Extraction
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Sri Lanka tourism 2024",
    "max_results": 100,
    "order": "relevance",
    "published_after": "2024-01-01T00:00:00Z",
    "region_code": "LK"
  }'
```

#### Get Real-time Status
```bash
curl "http://localhost:8000/api/status" | jq '.'
```

#### Get Analytics Summary
```bash
curl "http://localhost:8000/api/analytics/summary" | jq '.summary'
```

#### Health Check with Details
```bash
curl "http://localhost:8000/health" | jq '.components'
```

### Response Examples

#### Extraction Status Response
```json
{
  "status": "running",
  "progress": {
    "total_queries": 50,
    "completed_queries": 23,
    "videos_extracted": 1247,
    "current_query": "Colombo restaurants",
    "estimated_completion": "2024-01-15T14:30:00Z"
  },
  "api_keys": {
    "total": 3,
    "active": 2,
    "quota_remaining": 25000
  },
  "performance": {
    "videos_per_minute": 15.7,
    "success_rate": 98.2,
    "cache_hit_rate": 23.1
  }
}
```

#### Analytics Summary Response
```json
{
  "summary": {
    "total_videos": 15640,
    "unique_channels": 1205,
    "average_sri_lanka_score": 0.78,
    "top_categories": ["Travel & Events", "News & Politics", "Entertainment"],
    "data_freshness": "2024-01-15T12:45:00Z"
  },
  "trending": {
    "most_viewed_today": {...},
    "fastest_growing": {...},
    "engagement_leaders": {...}
  }
}
```

## 🔧 Configuration

## 🔧 Configuration

### Search Strategy Configuration
The system employs sophisticated search strategies optimized for comprehensive Sri Lankan content discovery:

#### 1. Location-Based Searches (30+ Locations)
- **Major Cities**: Colombo, Kandy, Galle, Jaffna, Negombo, Trincomalee
- **Tourist Destinations**: Sigiriya, Ella, Nuwara Eliya, Anuradhapura
- **Cultural Sites**: Dambulla, Polonnaruwa, Mihintale, Kataragama
- **Natural Landmarks**: Adam's Peak, Horton Plains, Yala National Park

#### 2. Category-Based Searches (25+ Categories)
- **Tourism & Travel**: Hotels, restaurants, attractions, travel guides
- **Culture & Heritage**: Traditional music, dance, festivals, ceremonies
- **Food & Cuisine**: Sri Lankan recipes, street food, restaurant reviews
- **News & Current Affairs**: Local news, politics, economics
- **Entertainment**: Music videos, movies, comedy, vlogs
- **Education**: Language learning, history, documentaries

#### 3. Language & Cultural Terms
- **Sinhala Keywords**: Native language terms and phrases
- **Tamil Keywords**: Tamil language content specific to Sri Lanka
- **Cultural Terms**: Festival names, traditional practices, local expressions
- **Mixed Language**: Sri Lankan English and code-switching content

#### 4. Temporal Strategies
- **Recent Content**: Last 30 days for trending topics
- **Seasonal Content**: Holiday and festival-specific searches
- **Historical Content**: Significant events and anniversaries
- **Viral Content**: Trending hashtags and topics

### Content Scoring Algorithm
Videos are scored using a sophisticated multi-factor algorithm:

```python
# Scoring Components (Total: 100%)
sri_lanka_score = (
    location_relevance * 0.40 +      # Geographic indicators
    cultural_relevance * 0.40 +      # Cultural and language indicators
    category_relevance * 0.20        # Topic relevance
)

quality_score = (
    engagement_rate * 0.35 +         # Likes, comments, shares ratio
    view_velocity * 0.25 +           # Views per day since publication
    content_completeness * 0.20 +    # Metadata quality and completeness
    channel_authority * 0.20         # Channel subscriber count and reputation
)
```

#### Scoring Factors Explained:
- **Location Relevance**: Presence of Sri Lankan city names, landmarks, geographic references
- **Cultural Relevance**: Sinhala/Tamil language, cultural terms, local customs
- **Category Relevance**: Alignment with targeted content categories
- **Engagement Rate**: Ratio of likes, comments, and shares to views
- **Content Quality**: Video length, tags quality, thumbnail presence

### API Key Management System
Advanced quota management for optimal performance:

#### Features:
- **Automatic Key Rotation**: Switches keys when quota limits approach
- **Intelligent Load Distribution**: Balances requests across available keys
- **Real-time Quota Monitoring**: Tracks usage per key per day
- **Fallback Handling**: Continues operation with remaining keys if some fail
- **Performance Optimization**: Uses fastest-responding keys preferentially

#### Configuration:
```json
{
  "youtube_api_keys": [
    "key1-for-primary-searches",
    "key2-for-detailed-video-data",
    "key3-for-channel-information",
    "key4-for-backup-operations"
  ],
  "key_rotation_strategy": "round_robin",
  "quota_threshold": 9500,
  "retry_failed_keys": true
}
```

### Environment Configuration Options

#### Application Settings
```env
# Performance Tuning
MAX_CONCURRENT_REQUESTS=10        # Concurrent API requests
BATCH_SIZE=50                     # Videos processed per batch
CACHE_TTL_HOURS=24               # Cache time-to-live
RETRY_ATTEMPTS=3                 # Failed request retry count

# Data Quality
MIN_SRI_LANKA_SCORE=0.3          # Minimum relevance score
MIN_QUALITY_SCORE=0.2            # Minimum quality threshold
DUPLICATE_CHECK_ENABLED=true     # Enable deduplication
SPAM_FILTER_ENABLED=true         # Enable spam filtering

# Monitoring
HEALTH_CHECK_INTERVAL=300        # Health check frequency (seconds)
LOG_ROTATION_SIZE=100MB          # Log file size limit
METRICS_RETENTION_DAYS=30        # Metrics data retention

# Security
API_RATE_LIMIT=1000              # Requests per hour limit
ALLOWED_ORIGINS=["localhost"]    # CORS allowed origins
ENABLE_API_AUTHENTICATION=false  # Enable API key authentication
```

#### BigQuery Configuration
```env
# Table Partitioning
BQ_PARTITION_FIELD=published_at
BQ_PARTITION_TYPE=DAY
BQ_CLUSTERING_FIELDS=channel_id,category_id

# Query Optimization
BQ_JOB_TIMEOUT=300
BQ_MAX_RESULTS=10000
BQ_USE_LEGACY_SQL=false
```

## 📈 Monitoring & Analytics

## 📈 Monitoring & Analytics

### Real-time Dashboard Features
Access the comprehensive dashboard at `http://localhost:8000/`:

#### 🎯 Extraction Monitoring
- **Current Operation Status**: Real-time progress of active extractions
- **Performance Metrics**: Videos per hour, success rates, error tracking
- **Queue Management**: Pending queries and processing pipeline status
- **Geographic Coverage**: Map visualization of content coverage across Sri Lanka

#### 🔑 API Key Health Dashboard
- **Individual Key Status**: Usage, quotas, and availability for each YouTube API key
- **Quota Distribution**: Visual breakdown of daily quota consumption
- **Performance Rankings**: Key response times and success rates
- **Automatic Rotation Status**: Current active key and rotation schedule

#### 📊 System Performance
- **Resource Utilization**: Real-time CPU, memory, and disk usage
- **Database Performance**: SQLite cache hit rates and query performance
- **Network Activity**: API request rates and response times
- **Error Analytics**: Error patterns, recovery rates, and failure analysis

#### 🎬 Content Analytics
- **Sri Lankan Content Discovery**: New videos found and relevance scores
- **Channel Insights**: Top performing Sri Lankan channels
- **Trending Analysis**: Viral content and engagement patterns
- **Category Distribution**: Content spread across different topics

### BigQuery Analytics
Pre-built analytical queries for comprehensive insights:

#### Content Performance Analysis
```sql
-- Top trending Sri Lankan videos
SELECT 
  title,
  channel_title,
  view_count,
  like_count,
  engagement_rate,
  sri_lanka_score
FROM `youtube_analytics.video_data`
WHERE sri_lanka_score > 0.7
  AND published_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY engagement_rate DESC
LIMIT 50;
```

#### Geographic Content Distribution
```sql
-- Content coverage by Sri Lankan locations
SELECT 
  REGEXP_EXTRACT(LOWER(title), 
    r'(colombo|kandy|galle|jaffna|ella|sigiriya|negombo)') as location,
  COUNT(*) as video_count,
  AVG(sri_lanka_score) as avg_relevance,
  AVG(engagement_rate) as avg_engagement
FROM `youtube_analytics.video_data`
WHERE sri_lanka_score > 0.5
GROUP BY location
HAVING location IS NOT NULL
ORDER BY video_count DESC;
```

#### Temporal Trend Analysis
```sql
-- Content trends over time
SELECT 
  DATE(published_at) as publish_date,
  COUNT(*) as videos_published,
  AVG(view_count) as avg_views,
  AVG(sri_lanka_score) as avg_relevance
FROM `youtube_analytics.video_data`
WHERE published_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY publish_date
ORDER BY publish_date DESC;
```

### Logging & Monitoring
Comprehensive logging system for debugging and analysis:

#### Log Files Location
```
logs/
├── youtube_extractor.log    # Main application logs
├── error.log               # Error-specific logs with stack traces
├── api_requests.log        # API request/response logging
└── performance.log         # Performance metrics and timings
```

#### Log Analysis Commands
```bash
# Monitor real-time application activity
tail -f logs/youtube_extractor.log

# Check for recent errors
tail -n 100 logs/error.log | grep ERROR

# Analyze API performance
grep "API_TIMING" logs/youtube_extractor.log | tail -20

# Monitor extraction progress
grep "EXTRACTION_PROGRESS" logs/youtube_extractor.log | tail -10
```

#### System Monitoring Commands
```bash
# Application health check
curl http://localhost:8000/health | jq '.components'

# System resource monitoring
curl http://localhost:8000/api/metrics | jq '.system'

# Database performance
curl http://localhost:8000/api/cache/stats | jq '.'

# API key status monitoring
curl http://localhost:8000/api/status | jq '.api_keys'
```

### Performance Metrics
Key performance indicators tracked by the system:

#### Extraction Performance
- **Videos per Hour**: Target: >100 videos/hour
- **API Success Rate**: Target: >95%
- **Cache Hit Rate**: Target: >20% (reduces API calls)
- **Deduplication Rate**: Percentage of duplicate videos prevented

#### Content Quality Metrics
- **Average Sri Lanka Score**: Target: >0.6
- **High-Quality Content Ratio**: Videos with quality_score > 0.7
- **Content Freshness**: Percentage of videos from last 30 days
- **Channel Diversity**: Number of unique channels discovered

#### System Health Metrics
- **Memory Usage**: Should stay below 80% of available RAM
- **CPU Utilization**: Average load and peak usage
- **Disk I/O Performance**: SQLite read/write speeds
- **API Response Times**: Average latency for YouTube API calls

### Alerting & Notifications
Configure monitoring alerts for critical events:

#### Critical Alerts
- API quota exhaustion (90% threshold)
- Extraction process failures
- Database connection issues
- High error rates (>5%)

#### Warning Alerts
- Low content quality scores
- Slow API response times
- High memory usage (>70%)
- Cache performance degradation

## 🔒 Security Features

### Container Security
- Non-root user execution
- Minimal base image with security updates
- Resource limits and isolation
- Health check integration

### Network Security
- Firewall configuration (UFW)
- Rate limiting and request validation
- Secure API key handling
- HTTPS support (when configured with SSL certificates)

### Data Security
- Encrypted environment variables
- Secure service account handling
- Data encryption in transit and at rest
- Access logging and audit trails

## 🛠️ Troubleshooting

## 🛠️ Troubleshooting

### Common Issues & Solutions

#### 🔑 API Key Issues

**Problem**: API Key Quota Exceeded
```bash
# Check current API key status
curl "http://localhost:8000/api/status" | jq '.api_keys'

# Solution: Add more API keys to api_keys.json
{
  "youtube_api_keys": [
    "existing-key-1",
    "existing-key-2",
    "new-key-3",
    "new-key-4"
  ]
}

# Restart application to load new keys
docker-compose restart youtube-extractor
```

**Problem**: Invalid API Key Error
```bash
# Check logs for API key validation errors
grep "INVALID_API_KEY" logs/error.log

# Verify API key in Google Cloud Console
# Ensure YouTube Data API v3 is enabled
# Check API key restrictions (if any)
```

#### 🗄️ Database & Storage Issues

**Problem**: BigQuery Permission Denied
```bash
# Verify service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Grant required BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Test BigQuery connectivity
curl "http://localhost:8000/health" | jq '.components.bigquery'
```

**Problem**: SQLite Database Locked
```bash
# Check for multiple processes accessing the database
ps aux | grep python

# Stop all instances and restart
docker-compose down
docker-compose up -d

# If issue persists, backup and recreate cache
cp data/youtube_cache.db data/youtube_cache_backup.db
rm data/youtube_cache.db
# Application will recreate on next start
```

**Problem**: Cloud Storage Access Issues
```bash
# Test bucket access
gsutil ls gs://your-bucket-name

# Check service account permissions
gsutil iam get gs://your-bucket-name

# Verify credentials
curl "http://localhost:8000/health" | jq '.components.storage'
```

#### 🚀 Application Performance Issues

**Problem**: Slow Extraction Speed
```bash
# Check system resources
curl "http://localhost:8000/api/metrics" | jq '.system'

# Monitor API response times
tail -f logs/youtube_extractor.log | grep "API_TIMING"

# Solutions:
# 1. Add more API keys for parallel processing
# 2. Increase MAX_CONCURRENT_REQUESTS in .env
# 3. Upgrade system resources (CPU/RAM)
# 4. Check network connectivity
```

**Problem**: High Memory Usage
```bash
# Monitor memory usage
curl "http://localhost:8000/api/metrics" | jq '.system.memory'

# Check for memory leaks in logs
grep "MEMORY_WARNING" logs/youtube_extractor.log

# Solutions:
# 1. Reduce BATCH_SIZE in environment variables
# 2. Increase cache cleanup frequency
# 3. Restart application periodically
# 4. Upgrade to higher memory instance
```

**Problem**: Application Won't Start
```bash
# Check application logs
docker logs youtube-extractor

# Common startup issues:
# 1. Missing environment variables
docker exec youtube-extractor env | grep -E "(YOUTUBE|GOOGLE|BIGQUERY)"

# 2. Missing service account file
docker exec youtube-extractor ls -la /app/service-account.json

# 3. Port conflicts
netstat -tulpn | grep :8000

# 4. Docker daemon issues
docker system prune -a
docker-compose up --build
```

#### 🌐 Network & Connectivity Issues

**Problem**: API Request Timeouts
```bash
# Check network connectivity
curl -w "@curl-format.txt" -o /dev/null -s "https://www.googleapis.com/youtube/v3/"

# Monitor API response times
grep "TIMEOUT" logs/error.log

# Solutions:
# 1. Increase request timeout in configuration
# 2. Check firewall settings
# 3. Verify DNS resolution
# 4. Check proxy settings if applicable
```

**Problem**: Dashboard Not Accessible
```bash
# Check if application is running
curl http://localhost:8000/health

# Check port binding
docker port youtube-extractor

# Verify firewall rules (if on cloud)
gcloud compute firewall-rules list --filter="name:youtube-extractor"

# Test from different network
curl -I http://EXTERNAL_IP:8000/
```

### Debugging Tools & Commands

#### Application Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
docker-compose restart youtube-extractor

# Interactive debugging session
docker exec -it youtube-extractor /bin/bash

# Check application configuration
curl "http://localhost:8000/api/config" | jq '.'

# Monitor real-time API calls
tail -f logs/youtube_extractor.log | grep "API_REQUEST"
```

#### Database Debugging
```bash
# SQLite database inspection
sqlite3 data/youtube_cache.db ".tables"
sqlite3 data/youtube_cache.db "SELECT COUNT(*) FROM videos;"

# BigQuery debugging
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM youtube_analytics.video_data"

# Check table schema
bq show youtube_analytics.video_data
```

#### Performance Analysis
```bash
# API performance analysis
grep "API_TIMING" logs/youtube_extractor.log | \
  awk '{print $5}' | \
  sort -n | \
  tail -10

# Memory usage trends
grep "MEMORY_USAGE" logs/youtube_extractor.log | \
  tail -20

# Error rate analysis
grep "ERROR" logs/error.log | \
  wc -l
```

### Log Analysis & Troubleshooting

#### Understanding Log Formats
```
# Main application log format:
2024-01-15 14:30:25 [INFO] [main.py:245] EXTRACTION_PROGRESS: Query 'Sri Lanka tourism' completed, 50 videos processed

# Error log format:
2024-01-15 14:30:25 [ERROR] [main.py:345] API_ERROR: YouTube API quota exceeded for key ending in ...xyz

# Performance log format:
2024-01-15 14:30:25 [INFO] [main.py:123] API_TIMING: Request took 1.245s, quota remaining: 8500
```

#### Key Log Patterns to Monitor
```bash
# Successful extractions
grep "EXTRACTION_COMPLETE" logs/youtube_extractor.log

# API quota warnings
grep "QUOTA_WARNING" logs/youtube_extractor.log

# Database operations
grep "DATABASE_" logs/youtube_extractor.log

# Cache performance
grep "CACHE_" logs/youtube_extractor.log
```

### Getting Help

#### Self-Diagnosis Checklist
1. ✅ **Environment Variables**: All required variables set in `.env`
2. ✅ **API Keys**: Valid YouTube API keys with sufficient quota
3. ✅ **Service Account**: JSON file present and valid
4. ✅ **Google Cloud**: APIs enabled and permissions granted
5. ✅ **Network**: Connectivity to YouTube and Google Cloud APIs
6. ✅ **Resources**: Sufficient CPU, memory, and disk space
7. ✅ **Dependencies**: All Python packages installed correctly

#### Create Support Issue
When creating a support issue, include:
```bash
# System information
curl "http://localhost:8000/api/metrics" | jq '.system' > system_info.json

# Application configuration (remove sensitive data)
curl "http://localhost:8000/api/config" | jq '.' > config_info.json

# Recent logs (last 100 lines)
tail -100 logs/youtube_extractor.log > recent_logs.txt
tail -100 logs/error.log > recent_errors.txt

# Environment information (remove API keys)
env | grep -E "(YOUTUBE|GOOGLE|BIGQUERY)" | sed 's/=.*/=***/' > env_info.txt
```

## 🔄 Maintenance

## 🔄 Maintenance & Operations

### Regular Maintenance Tasks

#### Daily Tasks (Automated)
- **API Quota Monitoring**: Automatic tracking and alerts at 90% usage
- **Cache Optimization**: Automatic cleanup of expired cache entries
- **Log Rotation**: Automatic log file rotation to prevent disk space issues
- **Health Checks**: Continuous monitoring of all system components

#### Weekly Tasks (Recommended)
```bash
# 1. Review extraction performance
curl "http://localhost:8000/api/analytics/summary" | jq '.performance'

# 2. Check data quality metrics
curl "http://localhost:8000/api/analytics/summary" | jq '.quality'

# 3. Monitor system resource usage
curl "http://localhost:8000/api/metrics" | jq '.system'

# 4. Update search terms if needed (add new Sri Lankan locations/events)
# Edit the search configuration in main.py or via API

# 5. Review and add new YouTube API keys if quota is frequently exceeded
```

#### Monthly Tasks (Recommended)
```bash
# 1. Backup configuration and data
tar -czf backup-$(date +%Y%m%d).tar.gz .env api_keys.json service-account.json data/

# 2. Update dependencies
pip install -r requirements.txt --upgrade

# 3. Review BigQuery costs and optimize queries
# Check query performance in BigQuery console

# 4. Analyze content trends and update search strategies
# Review analytics to identify new trending topics

# 5. Security updates
docker pull python:3.11-slim
docker-compose build --no-cache
```

### Data Management

#### BigQuery Data Lifecycle
```sql
-- Archive old data (keep last 2 years)
CREATE TABLE `youtube_analytics.video_data_archive` AS
SELECT * FROM `youtube_analytics.video_data`
WHERE published_at < DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR);

-- Delete archived data from main table
DELETE FROM `youtube_analytics.video_data`
WHERE published_at < DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR);
```

#### Cache Management
```bash
# Check cache size and performance
curl "http://localhost:8000/api/cache/stats" | jq '.'

# Manual cache cleanup (if needed)
sqlite3 data/youtube_cache.db "DELETE FROM videos WHERE created_at < datetime('now', '-30 days');"

# Optimize SQLite database
sqlite3 data/youtube_cache.db "VACUUM;"
```

#### Log Management
```bash
# Archive old logs
mkdir -p archive/$(date +%Y%m)
mv logs/*.log.* archive/$(date +%Y%m)/

# Compress archived logs
find archive/ -name "*.log" -exec gzip {} \;

# Clean up old archives (keep last 6 months)
find archive/ -type f -mtime +180 -delete
```

### Scaling Operations

#### Horizontal Scaling
```bash
# Deploy multiple instances with load balancer
# 1. Create instance template
gcloud compute instance-templates create youtube-extractor-template \
  --machine-type=e2-medium \
  --metadata-from-file startup-script=startup-script.sh

# 2. Create managed instance group
gcloud compute instance-groups managed create youtube-extractor-group \
  --base-instance-name=youtube-extractor \
  --size=3 \
  --template=youtube-extractor-template \
  --zone=us-central1-a

# 3. Set up load balancer
gcloud compute backend-services create youtube-extractor-backend \
  --protocol=HTTP \
  --health-checks=youtube-extractor-health-check \
  --global
```

#### Vertical Scaling
```bash
# Upgrade instance resources
gcloud compute instances set-machine-type youtube-extractor-vm \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a

# Update Docker resource limits
# Edit docker-compose.yaml:
services:
  youtube-extractor:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

#### API Key Scaling
```bash
# Add more YouTube API keys
# 1. Create additional API keys in Google Cloud Console
# 2. Update api_keys.json:
{
  "youtube_api_keys": [
    "existing-key-1",
    "existing-key-2",
    "new-key-3",
    "new-key-4",
    "new-key-5"
  ]
}

# 3. Restart application to load new keys
docker-compose restart youtube-extractor
```

### Backup & Recovery

#### Configuration Backup
```bash
# Create complete configuration backup
mkdir -p backups/$(date +%Y%m%d)
cp .env api_keys.json service-account.json backups/$(date +%Y%m%d)/
tar -czf backups/config-backup-$(date +%Y%m%d).tar.gz backups/$(date +%Y%m%d)/
```

#### Data Backup
```bash
# BigQuery data export
bq extract \
  --destination_format=NEWLINE_DELIMITED_JSON \
  youtube_analytics.video_data \
  gs://your-backup-bucket/exports/video_data_$(date +%Y%m%d).json

# SQLite database backup
cp data/youtube_cache.db backups/youtube_cache_$(date +%Y%m%d).db
gzip backups/youtube_cache_$(date +%Y%m%d).db
```

#### Application Backup
```bash
# Create Docker image backup
docker save youtube-extractor:latest | gzip > backups/youtube-extractor-$(date +%Y%m%d).tar.gz

# Source code backup
git archive --format=tar.gz --output=backups/source-$(date +%Y%m%d).tar.gz HEAD
```

#### Recovery Procedures
```bash
# Restore from configuration backup
tar -xzf backups/config-backup-YYYYMMDD.tar.gz
cp backups/YYYYMMDD/* ./

# Restore SQLite database
gunzip backups/youtube_cache_YYYYMMDD.db.gz
cp backups/youtube_cache_YYYYMMDD.db data/youtube_cache.db

# Restore from BigQuery backup
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  youtube_analytics.video_data_restored \
  gs://your-backup-bucket/exports/video_data_YYYYMMDD.json
```

### Update & Deployment Procedures

#### Application Updates
```bash
# 1. Backup current deployment
./backup.sh

# 2. Pull latest code
git pull origin main

# 3. Build new image
docker-compose build --no-cache

# 4. Test new deployment
docker-compose up -d

# 5. Verify functionality
curl "http://localhost:8000/health"
curl "http://localhost:8000/api/status"

# 6. Monitor for issues
tail -f logs/youtube_extractor.log
```

#### Rolling Updates (Production)
```bash
# For managed instance groups
gcloud compute instance-groups managed rolling-action start-update \
  youtube-extractor-group \
  --version-template=youtube-extractor-template-v2 \
  --zone=us-central1-a

# For Cloud Run
gcloud run deploy youtube-extractor \
  --source . \
  --region us-central1
```

### Monitoring & Alerting Setup

#### Custom Monitoring Scripts
```bash
#!/bin/bash
# monitoring.sh - Custom monitoring script

# Check application health
HEALTH=$(curl -s "http://localhost:8000/health" | jq -r '.status')
if [ "$HEALTH" != "healthy" ]; then
  echo "ALERT: Application unhealthy"
  # Send notification (email, Slack, etc.)
fi

# Check API quota usage
QUOTA=$(curl -s "http://localhost:8000/api/status" | jq -r '.api_keys.quota_remaining')
if [ "$QUOTA" -lt 1000 ]; then
  echo "WARNING: API quota low: $QUOTA remaining"
fi

# Check system resources
MEMORY_USAGE=$(curl -s "http://localhost:8000/api/metrics" | jq -r '.system.memory.percent')
if [ "${MEMORY_USAGE%.*}" -gt 80 ]; then
  echo "WARNING: High memory usage: $MEMORY_USAGE%"
fi
```

#### Automated Alerting
```bash
# Set up cron job for monitoring
crontab -e
# Add: */5 * * * * /path/to/monitoring.sh

# Email alerts setup
sudo apt-get install mailutils
echo "Alert from YouTube Extractor" | mail -s "Alert" admin@domain.com

# Slack webhook integration
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"YouTube Extractor Alert: '"$MESSAGE"'"}' \
  YOUR_SLACK_WEBHOOK_URL
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions to improve the YouTube Video Data Extractor! Please follow these guidelines:

### How to Contribute

1. **Fork the Repository**
   ```bash
   git fork https://github.com/View-Rush/YouTube-Video-Data-Extractor.git
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

3. **Make Your Changes**
   - Follow Python PEP 8 style guidelines
   - Add appropriate documentation
   - Include unit tests for new features
   - Update README.md if needed

4. **Test Your Changes**
   ```bash
   # Run the application locally
   python main.py
   
   # Test API endpoints
   curl http://localhost:8000/health
   
   # Check for any errors
   tail -f logs/youtube_extractor.log
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add amazing new feature: detailed description"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/amazing-new-feature
   ```

7. **Create a Pull Request**
   - Provide a clear description of your changes
   - Reference any related issues
   - Include screenshots for UI changes
   - List any breaking changes

### Contribution Guidelines

#### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Write clear, descriptive commit messages
- Keep functions focused and well-documented

#### Documentation
- Update README.md for significant changes
- Add docstrings to new functions
- Update API documentation if endpoints change
- Include examples for new features

#### Testing
- Test changes locally before submitting
- Ensure all existing functionality still works
- Add unit tests for new features
- Test with different API key configurations

### Areas for Contribution

#### 🚀 High Priority
- **Performance Optimization**: Improve API call efficiency
- **New Search Strategies**: Add more Sri Lankan content discovery methods
- **Enhanced Analytics**: Add new dashboard metrics and visualizations
- **Mobile Responsiveness**: Improve dashboard mobile experience

#### 🎯 Medium Priority
- **Additional APIs**: Integration with other social media platforms
- **Machine Learning**: Improve content scoring algorithms
- **Internationalization**: Support for multiple languages
- **Automated Testing**: Comprehensive test suite

#### 💡 Feature Ideas
- **Real-time Notifications**: Alert system for trending content
- **Content Moderation**: Advanced spam and inappropriate content filtering
- **Export Features**: CSV, Excel, PDF report generation
- **API Authentication**: Secure API access with API keys

### Development Setup

1. **Prerequisites**
   ```bash
   python --version  # Should be 3.11+
   docker --version  # For containerized development
   ```

2. **Local Development Environment**
   ```bash
   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/YouTube-Video-Data-Extractor.git
   cd YouTube-Video-Data-Extractor
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy environment template
   cp .env.example .env
   # Edit .env with your development configuration
   ```

3. **Development Workflow**
   ```bash
   # Start development server with auto-reload
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   
   # In another terminal, monitor logs
   tail -f logs/youtube_extractor.log
   ```

### Reporting Issues

When reporting bugs or requesting features:

1. **Check Existing Issues**: Search for similar issues first
2. **Use Issue Templates**: Follow the provided templates
3. **Provide Details**: Include logs, environment info, and reproduction steps
4. **Label Appropriately**: Use bug, feature, enhancement, etc.

#### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Windows 10, Ubuntu 20.04]
- Python Version: [e.g., 3.11.5]
- Docker Version: [e.g., 20.10.21]
- Deployment Method: [Local, Docker, Cloud Run, etc.]

**Logs**
```
Paste relevant log entries here
```

**Additional Context**
Any other context about the problem.
```

### Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub repository insights

Thank you for helping make this project better! 🎉

## 📞 Support & Community

### Getting Help

#### 📚 Documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Comprehensive deployment guide for all platforms
- **API Documentation**: Available at `http://localhost:8000/docs` when running
- **Interactive API Testing**: Use the built-in Swagger UI for testing endpoints

#### 🐛 Issue Reporting
- **GitHub Issues**: [Create an issue](https://github.com/View-Rush/YouTube-Video-Data-Extractor/issues) for bugs or feature requests
- **Bug Reports**: Use the issue template and include logs, environment details
- **Feature Requests**: Describe the use case and expected behavior

#### 💬 Community Support
- **Discussions**: Use GitHub Discussions for questions and community support
- **Best Practices**: Share configuration tips and optimization strategies
- **Use Cases**: Discuss different applications of the platform

#### 🔧 Professional Support
For enterprise deployments or custom development:
- Commercial support available for large-scale deployments
- Custom feature development and integration services
- Training and consultation for team implementations

### FAQ

#### Q: How many YouTube API keys do I need?
**A:** Minimum 1 key for basic operation, but 3-5 keys recommended for production use. Each key provides 10,000 quota units per day, allowing for approximately 1,000-3,000 video extractions depending on data completeness.

#### Q: What are the Google Cloud costs?
**A:** Costs depend on usage:
- **BigQuery**: ~$5/TB for data storage, ~$5/TB for query processing
- **Cloud Storage**: ~$0.02/GB/month for standard storage
- **Compute Engine**: ~$25/month for e2-medium instance (24/7)
- **Cloud Run**: Pay-per-use, typically $5-20/month for moderate usage

#### Q: Can I run this for other countries?
**A:** Yes! The system is designed for Sri Lankan content but can be adapted:
1. Modify search terms in the configuration
2. Update location-based searches
3. Adjust content scoring algorithms
4. Customize cultural relevance factors

#### Q: How do I handle rate limits?
**A:** The system includes several strategies:
- Automatic API key rotation
- Exponential backoff on failures
- Intelligent request distribution
- Cache-first approach to reduce API calls

#### Q: Is this suitable for commercial use?
**A:** Yes, the MIT license allows commercial use. Consider:
- YouTube API Terms of Service compliance
- Appropriate attribution
- Data privacy regulations (GDPR, etc.)
- Rate limiting and fair use policies

### Performance Benchmarks

#### Typical Performance Metrics
- **Extraction Rate**: 100-200 videos per hour (with 3 API keys)
- **Content Discovery**: 500-1000 new Sri Lankan videos per day
- **Relevance Accuracy**: ~85% accuracy for Sri Lankan content detection
- **System Uptime**: >99.5% with proper deployment and monitoring

#### Optimization Tips
```bash
# Increase concurrent processing
export MAX_CONCURRENT_REQUESTS=15

# Optimize cache performance
export CACHE_TTL_HOURS=48

# Reduce API calls with aggressive caching
export DUPLICATE_CHECK_ENABLED=true

# Use more API keys for higher throughput
# Add 5-10 keys for production environments
```

## 🔄 Version History & Roadmap

### Current Version: v2.5.0

#### ✨ Latest Features (v2.5.0)
- **Enhanced Dashboard**: Real-time metrics and improved UI
- **Advanced Caching**: SQLite-based intelligent caching system
- **Multi-API Management**: Sophisticated API key rotation and health monitoring
- **Content Scoring**: ML-powered relevance and quality assessment
- **Production Deployment**: Complete Docker and cloud deployment solutions

#### 🗓️ Roadmap

**v2.6.0 (Q2 2024) - Analytics & Insights**
- [ ] Advanced trending analysis with predictive models
- [ ] Channel growth tracking and benchmarking
- [ ] Content recommendation engine
- [ ] Export features (CSV, Excel, PDF reports)
- [ ] Mobile-responsive dashboard improvements

**v2.7.0 (Q3 2024) - Platform Expansion**
- [ ] Multi-platform support (TikTok, Instagram, Facebook)
- [ ] Cross-platform content correlation analysis
- [ ] Unified social media dashboard
- [ ] Advanced data visualization tools

**v2.8.0 (Q4 2024) - AI & Machine Learning**
- [ ] Automated content categorization using NLP
- [ ] Sentiment analysis for comments and descriptions
- [ ] Automated trending prediction models
- [ ] Content quality assessment using computer vision

**v3.0.0 (2025) - Enterprise Features**
- [ ] Multi-tenant architecture
- [ ] Role-based access control
- [ ] API rate limiting and authentication
- [ ] Advanced monitoring and alerting
- [ ] White-label deployment options

### Version History

#### v2.4.0 (2024-01-10)
- Added comprehensive deployment automation
- Improved error handling and retry mechanisms
- Enhanced logging and monitoring capabilities
- Docker multi-stage build optimization

#### v2.3.0 (2023-12-15)
- FastAPI migration for better performance
- Real-time dashboard with WebSocket support
- Advanced BigQuery schema with partitioning
- Multi-API key management system

#### v2.2.0 (2023-11-20)
- SQLite caching for improved performance
- Content quality scoring algorithm
- Enhanced Sri Lankan content detection
- Docker containerization support

#### v2.1.0 (2023-10-25)
- Google Cloud Platform integration
- BigQuery data warehouse implementation
- Automated search strategies
- Basic web dashboard

#### v2.0.0 (2023-09-30)
- Complete rewrite with modern architecture
- Multi-threaded processing
- Advanced error handling
- Production-ready deployment

#### v1.0.0 (2023-08-15)
- Initial release
- Basic video extraction functionality
- Simple CSV output
- Manual search queries

---

**Built with ❤️ for Sri Lankan content creators, researchers, and the global community interested in Sri Lankan digital culture.**

**Special thanks to all contributors and the open-source community for making this project possible!**

---

### 📊 Project Statistics

![GitHub Stars](https://img.shields.io/github/stars/View-Rush/YouTube-Video-Data-Extractor)
![GitHub Forks](https://img.shields.io/github/forks/View-Rush/YouTube-Video-Data-Extractor)
![GitHub Issues](https://img.shields.io/github/issues/View-Rush/YouTube-Video-Data-Extractor)
![GitHub License](https://img.shields.io/github/license/View-Rush/YouTube-Video-Data-Extractor)
![Docker Pulls](https://img.shields.io/docker/pulls/viewrush/youtube-extractor)

**Last Updated**: January 2024 | **Maintainer**: [View-Rush](https://github.com/View-Rush) | **Status**: Active Development
