# Enhanced YouTube Video Data Extractor for Sri Lankan Content

A comprehensive, scalable YouTube video data extraction and analysis platform specifically designed for Sri Lankan content. This enhanced version includes advanced features for continuous data collection, intelligent content analysis, and robust deployment on Google Cloud Platform.

## 🚀 Key Features

### Core Functionality
- **Comprehensive Sri Lankan Content Discovery**: Advanced search strategies covering 30+ locations and 25+ categories
- **Intelligent Content Analysis**: ML-powered content scoring and Sri Lankan relevance detection
- **Multi-API Key Management**: Automatic rotation and quota management for unlimited scalability
- **Robust Error Handling**: Exponential backoff, automatic retries, and graceful degradation
- **Real-time Analytics**: Live dashboard with extraction metrics and performance monitoring

### Enhanced Data Collection
- **Smart Deduplication**: Local SQLite cache prevents duplicate video processing
- **Content Quality Scoring**: Algorithmic ranking based on engagement, relevance, and content quality
- **Advanced Filtering**: Remove spam, irrelevant content, and low-quality videos
- **Comprehensive Metadata**: 40+ data points per video including engagement metrics, channel statistics, and content analysis

### Storage & Analytics
- **Google Cloud Storage**: Organized data storage with automatic lifecycle management
- **BigQuery Integration**: Partitioned and clustered tables for optimal query performance
- **Advanced Analytics**: Trending videos, channel analytics, temporal analysis, and content insights
- **Data Backup**: Automatic backup systems with fallback storage options

### Production-Ready Features
- **Containerized Deployment**: Multi-stage Docker build with security best practices
- **Monitoring & Logging**: Comprehensive logging, health checks, and system monitoring
- **Auto-scaling**: Designed for Google Cloud Compute Engine with auto-restart capabilities
- **Security**: Non-root container execution, firewall configuration, and secure API handling

## 📋 Prerequisites

### Required Services
1. **Google Cloud Project** with the following APIs enabled:
   - YouTube Data API v3
   - BigQuery API
   - Cloud Storage API

2. **YouTube API Keys**: Multiple keys recommended for higher quota limits

3. **Google Cloud Resources**:
   - Cloud Storage bucket
   - BigQuery dataset
   - Compute Engine instance (optional)

### System Requirements
- Python 3.11+
- 2GB RAM minimum (4GB recommended)
- 10GB disk space minimum
- Internet connection with good bandwidth

## ⚙️ Installation & Setup

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Youtube\ Video\ Data\ Extractor
```

### 2. Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
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
```

### 3. Setup API Keys
Update `api_keys.json`:
```json
{
  "youtube_api_keys": [
    "your-youtube-api-key-1",
    "your-youtube-api-key-2",
    "your-youtube-api-key-3"
  ]
}
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t youtube-extractor .

# Run with environment variables
docker run -d \
  --name youtube-extractor \
  -p 8000:8000 \
  -e GOOGLE_CLOUD_PROJECT_ID=your-project-id \
  -e YOUTUBE_API_KEY_1=your-api-key \
  -v ./service-account.json:/app/service-account.json:ro \
  youtube-extractor
```

### Docker Compose
```bash
# Configure environment in .env file
docker-compose up -d
```

## ☁️ Google Cloud Deployment

### Automatic Deployment
```bash
# Deploy to Compute Engine
./deploy.sh your-project-id youtube-extractor-vm us-central1-a
```

### Manual Compute Engine Setup
1. Create a VM instance with Ubuntu 22.04
2. Copy the startup script: `startup-script.sh`
3. Run the startup script as root
4. Monitor logs: `journalctl -u youtube-extractor -f`

### Cloud Run Deployment
```bash
# Build and deploy to Cloud Run
gcloud run deploy youtube-extractor \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600 \
  --max-instances 1
```

## 📊 API Documentation

### Dashboard
- **Main Dashboard**: `http://localhost:8000/` - Real-time monitoring and control interface
- **API Documentation**: `http://localhost:8000/docs` - Interactive API documentation
- **Health Check**: `http://localhost:8000/health` - System status and component health

### Key API Endpoints

#### Extraction Control
- `POST /api/extract` - Start custom extraction
- `POST /api/extract/scheduled` - Start comprehensive scheduled extraction
- `POST /api/extract/targeted` - Start targeted extraction for specific queries
- `GET /api/status` - Get detailed extraction status and metrics

#### Analytics
- `GET /api/analytics/summary` - Get extraction analytics summary
- `GET /api/analytics/trending` - Get trending Sri Lankan videos
- `GET /api/analytics/channels` - Get top Sri Lankan channels
- `GET /api/metrics` - Get detailed system metrics

#### Configuration
- `GET /api/queries` - Get predefined search queries and categories

### Example API Usage

#### Start Custom Extraction
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Sri Lanka tourism",
    "max_results": 100,
    "order": "relevance",
    "published_after": "2024-01-01T00:00:00Z"
  }'
```

#### Get Analytics Summary
```bash
curl "http://localhost:8000/api/analytics/summary"
```

## 🔧 Configuration

### Search Strategy Configuration
The system uses multiple search strategies optimized for Sri Lankan content:

1. **Location-based searches**: 30+ Sri Lankan cities and landmarks
2. **Category-based searches**: Tourism, culture, food, news, etc.
3. **Cultural term searches**: Sinhala, Tamil, and cultural keywords
4. **Temporal strategies**: Recent content, trending content, historical content

### Content Scoring Algorithm
Videos are scored based on:
- **Location relevance** (40%): Presence of Sri Lankan location indicators
- **Cultural relevance** (40%): Cultural terms and language indicators  
- **Category relevance** (20%): Topic and category alignment
- **Quality metrics**: View count, engagement rate, content completeness

### API Key Management
- **Automatic rotation**: Keys rotate when quota limits are reached
- **Intelligent allocation**: Distributes load across available keys
- **Health monitoring**: Tracks success rates and quota usage
- **Fallback handling**: Continues operation when some keys are unavailable

## 📈 Monitoring & Analytics

### Real-time Dashboard Features
- **Extraction Status**: Current operation status and progress
- **API Key Health**: Usage, quotas, and availability for each key
- **Performance Metrics**: Videos per hour, success rates, error tracking
- **System Health**: Memory usage, CPU usage, disk space
- **Data Quality**: Content scoring, relevance metrics, deduplication stats

### BigQuery Analytics
Pre-built queries for:
- Trending content analysis
- Channel performance metrics
- Temporal content patterns
- Geographic content distribution
- Engagement trend analysis

### Logs and Monitoring
- **Application logs**: `/opt/youtube-extractor/logs/`
- **System logs**: `journalctl -u youtube-extractor`
- **Nginx logs**: `/var/log/nginx/youtube-extractor.*.log`
- **Monitoring script**: Automatic health checks every 5 minutes

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

### Common Issues

#### API Key Problems
```bash
# Check API key status
curl "http://localhost:8000/api/status" | jq '.api_keys'

# Verify API keys in logs
journalctl -u youtube-extractor | grep "API key"
```

#### Storage Issues
```bash
# Check BigQuery connectivity
gcloud bigquery query --use_legacy_sql=false "SELECT 1"

# Check GCS bucket access
gsutil ls gs://your-bucket-name
```

#### Performance Issues
```bash
# Monitor system resources
htop

# Check application metrics
curl "http://localhost:8000/api/metrics"

# Monitor extraction progress
curl "http://localhost:8000/api/status"
```

### Log Analysis
```bash
# Application logs
tail -f /opt/youtube-extractor/logs/youtube_extractor.log

# Error logs specifically
tail -f /opt/youtube-extractor/logs/error.log

# System service logs
journalctl -u youtube-extractor -f

# Nginx access logs
tail -f /var/log/nginx/youtube-extractor.access.log
```

## 🔄 Maintenance

### Regular Tasks
1. **Monitor API quotas**: Check daily usage and add keys as needed
2. **Review data quality**: Check content scoring and relevance metrics
3. **Update search terms**: Add new locations and categories periodically
4. **Database maintenance**: Monitor BigQuery costs and optimize queries
5. **Security updates**: Keep dependencies and system packages updated

### Backup Procedures
1. **Configuration backup**: Backup environment files and API keys
2. **Data backup**: BigQuery exports and GCS snapshots
3. **Application backup**: Docker images and source code
4. **Monitoring backup**: Log retention and metric history

### Scaling Considerations
- **Horizontal scaling**: Deploy multiple instances with load balancing
- **API key scaling**: Add more YouTube API keys for higher throughput
- **Storage scaling**: Monitor BigQuery and GCS usage, implement archiving
- **Compute scaling**: Upgrade instance types or add auto-scaling groups

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review logs for error details

## 🔄 Version History

### v2.0.0 (Current)
- Enhanced content analysis and scoring
- Multi-API key management with intelligent rotation
- Advanced BigQuery schema with partitioning
- Real-time monitoring dashboard
- Production-ready deployment scripts
- Comprehensive error handling and logging

### v1.0.0
- Basic video extraction functionality
- Simple BigQuery integration
- Basic web interface

---

**Built with ❤️ for Sri Lankan content creators and researchers**
