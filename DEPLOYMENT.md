# Deployment Guide - YouTube Video Data Extractor

This guide will walk you through deploying the Enhanced YouTube Video Data Extractor for Sri Lankan content on Google Cloud Platform.

## 🚀 Quick Start Deployment

### Option 1: Automated Deployment (Recommended)
```bash
# 1. Configure your environment
cp .env.example .env
# Edit .env with your actual values

# 2. Run automated deployment
./deploy.sh your-project-id youtube-extractor-vm us-central1-a
```

### Option 2: Manual Step-by-Step Deployment
Follow the detailed instructions below for complete control over the deployment process.

## 📋 Pre-Deployment Checklist

### 1. Google Cloud Setup
- [ ] Google Cloud Project created
- [ ] Billing enabled
- [ ] Required APIs enabled:
  - YouTube Data API v3
  - BigQuery API
  - Cloud Storage API
  - Compute Engine API
- [ ] Service account created with permissions:
  - BigQuery Data Editor
  - Storage Object Admin
  - Compute Instance Admin

### 2. API Keys Setup
- [ ] YouTube Data API keys obtained (minimum 1, recommended 3-5)
- [ ] API keys tested and working
- [ ] Daily quotas verified (10,000 units per key per day)

### 3. Local Environment
- [ ] Google Cloud SDK installed and configured
- [ ] Docker installed (for containerized deployment)
- [ ] Git repository cloned
- [ ] Environment variables configured

## 🔧 Step-by-Step Deployment

### Step 1: Prepare Google Cloud Resources

#### 1.1 Create Storage Bucket
```bash
# Create bucket for video data storage
gsutil mb -l us-central1 gs://youtube-data-sri-lanka-$(date +%s)

# Enable versioning and lifecycle management
gsutil versioning set on gs://youtube-data-sri-lanka-$(date +%s)
```

#### 1.2 Create BigQuery Dataset
```bash
# Create dataset
bq mk --location=us-central1 youtube_analytics

# Create the main table with enhanced schema
bq mk --table \
  youtube_analytics.video_data \
  video_id:STRING,published_at:TIMESTAMP,title:STRING,description:STRING,channel_id:STRING,channel_title:STRING,category_id:STRING,category_name:STRING,duration:STRING,dimension:STRING,definition:STRING,caption:STRING,licensed_content:BOOLEAN,projection:STRING,view_count:INTEGER,like_count:INTEGER,comment_count:INTEGER,thumbnail_default:STRING,thumbnail_medium:STRING,thumbnail_high:STRING,thumbnail_standard:STRING,thumbnail_maxres:STRING,tags:STRING,default_language:STRING,default_audio_language:STRING,topic_categories:STRING,region_restriction_allowed:STRING,region_restriction_blocked:STRING,content_rating:STRING,sri_lanka_score:FLOAT,location_relevance:FLOAT,cultural_relevance:FLOAT,category_relevance:FLOAT,quality_score:FLOAT,engagement_rate:FLOAT,is_trending:BOOLEAN,extracted_at:TIMESTAMP,extraction_batch_id:STRING,api_key_used:STRING,search_query:STRING,search_type:STRING,channel_subscriber_count:INTEGER,channel_video_count:INTEGER,channel_view_count:INTEGER,channel_description:STRING
```

#### 1.3 Setup Service Account
```bash
# Create service account
gcloud iam service-accounts create youtube-extractor \
  --description="Service account for YouTube Data Extractor" \
  --display-name="YouTube Extractor"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Configure Environment

#### 2.1 Setup Environment Variables
```bash
# Copy template and edit
cp .env.example .env

# Edit with your actual values
nano .env
```

Required values:
```env
GOOGLE_CLOUD_PROJECT_ID=your-actual-project-id
GCS_BUCKET_NAME=your-bucket-name
YOUTUBE_API_KEY_1=your-youtube-api-key-1
YOUTUBE_API_KEY_2=your-youtube-api-key-2
YOUTUBE_API_KEY_3=your-youtube-api-key-3
```

#### 2.2 Update API Keys Configuration
```bash
# Edit api_keys.json
nano api_keys.json
```

```json
{
  "youtube_api_keys": [
    "your-youtube-api-key-1",
    "your-youtube-api-key-2",
    "your-youtube-api-key-3"
  ]
}
```

### Step 3: Choose Deployment Method

## 🔹 Method A: Google Compute Engine Deployment

### 3A.1 Create VM Instance
```bash
# Create VM with startup script
gcloud compute instances create youtube-extractor-vm \
  --project=YOUR_PROJECT_ID \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --network-interface=network-tier=PREMIUM,subnet=default \
  --metadata-from-file startup-script=startup-script.sh \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --create-disk=auto-delete=yes,boot=yes,device-name=youtube-extractor-vm,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20231030,mode=rw,size=50,type=projects/YOUR_PROJECT_ID/zones/us-central1-a/diskTypes/pd-standard \
  --no-shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --labels=project=youtube-extractor,environment=production \
  --reservation-affinity=any
```

### 3A.2 Configure VM
```bash
# SSH into the VM
gcloud compute ssh youtube-extractor-vm --zone=us-central1-a

# The startup script will automatically:
# - Install Docker and dependencies
# - Clone the repository
# - Build and run the application
# - Configure nginx reverse proxy
# - Set up monitoring and logging
# - Configure firewall rules
```

### 3A.3 Upload Configuration Files
```bash
# Copy service account key
gcloud compute scp service-account.json youtube-extractor-vm:~/service-account.json --zone=us-central1-a

# Copy environment file
gcloud compute scp .env youtube-extractor-vm:~/.env --zone=us-central1-a

# Copy API keys file
gcloud compute scp api_keys.json youtube-extractor-vm:~/api_keys.json --zone=us-central1-a
```

### 3A.4 Finalize Setup
```bash
# SSH into VM and finalize setup
gcloud compute ssh youtube-extractor-vm --zone=us-central1-a

# Move files to application directory
sudo mv ~/service-account.json /opt/youtube-extractor/
sudo mv ~/.env /opt/youtube-extractor/
sudo mv ~/api_keys.json /opt/youtube-extractor/

# Restart the service
sudo systemctl restart youtube-extractor

# Check status
sudo systemctl status youtube-extractor
```

## 🔹 Method B: Cloud Run Deployment (Serverless)

### 3B.1 Build and Deploy
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
  --max-instances 1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT_ID=YOUR_PROJECT_ID \
  --set-env-vars GCS_BUCKET_NAME=your-bucket-name \
  --set-env-vars BIGQUERY_DATASET_ID=youtube_analytics \
  --set-env-vars BIGQUERY_TABLE_ID=video_data
```

### 3B.2 Set Environment Variables
```bash
# Set YouTube API keys
gcloud run services update youtube-extractor \
  --region us-central1 \
  --set-env-vars YOUTUBE_API_KEY_1=your-key-1 \
  --set-env-vars YOUTUBE_API_KEY_2=your-key-2 \
  --set-env-vars YOUTUBE_API_KEY_3=your-key-3
```

## 🔹 Method C: Local Docker Deployment

### 3C.1 Build Docker Image
```bash
# Build the image
docker build -t youtube-extractor:latest .

# Test locally
docker run -d \
  --name youtube-extractor-test \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/service-account.json:/app/service-account.json:ro \
  youtube-extractor:latest
```

### 3C.2 Deploy to Container Registry
```bash
# Tag for Google Container Registry
docker tag youtube-extractor:latest gcr.io/YOUR_PROJECT_ID/youtube-extractor:latest

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/youtube-extractor:latest
```

## 🔍 Deployment Verification

### Step 4: Verify Deployment

#### 4.1 Check Application Health
```bash
# Get external IP (for Compute Engine)
gcloud compute instances describe youtube-extractor-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Or get Cloud Run URL
gcloud run services describe youtube-extractor \
  --region us-central1 \
  --format='value(status.url)'

# Test health endpoint
curl http://YOUR_IP_OR_URL/health
```

#### 4.2 Access Dashboard
```bash
# Open in browser
http://YOUR_IP_OR_URL/

# Expected response: Modern dashboard interface
```

#### 4.3 Test API Endpoints
```bash
# Check status
curl http://YOUR_IP_OR_URL/api/status

# Start a test extraction
curl -X POST http://YOUR_IP_OR_URL/api/extract \
  -H "Content-Type: application/json" \
  -d '{"query": "Sri Lanka", "max_results": 10}'
```

#### 4.4 Verify Data Storage
```bash
# Check BigQuery data
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as total_videos FROM youtube_analytics.video_data"

# Check Cloud Storage
gsutil ls gs://your-bucket-name/
```

## 📊 Monitoring Setup

### Step 5: Configure Monitoring

#### 5.1 Set up Log Monitoring
```bash
# View application logs (Compute Engine)
gcloud compute ssh youtube-extractor-vm --zone=us-central1-a
sudo journalctl -u youtube-extractor -f

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=youtube-extractor" --limit=50
```

#### 5.2 Set up Alerting
```bash
# Create uptime check
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/uptime-policy.yaml

# Create alert policy for errors
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/error-policy.yaml
```

#### 5.3 Set up Dashboard
```bash
# Import monitoring dashboard
gcloud monitoring dashboards create \
  --config-from-file=monitoring/dashboard.yaml
```

## 🔐 Security Hardening

### Step 6: Security Configuration

#### 6.1 Configure Firewall (Compute Engine)
```bash
# Allow HTTP traffic
gcloud compute firewall-rules create allow-youtube-extractor \
  --allow tcp:80,tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow HTTP/HTTPS for YouTube Extractor"

# Allow SSH only from specific IPs (recommended)
gcloud compute firewall-rules create allow-ssh-youtube-extractor \
  --allow tcp:22 \
  --source-ranges YOUR_IP/32 \
  --description "Allow SSH for YouTube Extractor admin"
```

#### 6.2 Set up SSL Certificate (Optional)
```bash
# Request Let's Encrypt certificate
sudo certbot --nginx -d yourdomain.com

# Configure auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔄 Maintenance & Operations

### Step 7: Operational Procedures

#### 7.1 Regular Monitoring
```bash
# Check application status
curl http://YOUR_URL/health

# Monitor API key usage
curl http://YOUR_URL/api/status | jq '.api_keys'

# Check extraction progress
curl http://YOUR_URL/api/analytics/summary
```

#### 7.2 Update Deployment
```bash
# For Compute Engine deployment
git pull origin main
docker build -t youtube-extractor:latest .
sudo systemctl restart youtube-extractor

# For Cloud Run deployment
gcloud run deploy youtube-extractor --source .
```

#### 7.3 Backup Procedures
```bash
# Backup BigQuery data
bq extract \
  --destination_format=NEWLINE_DELIMITED_JSON \
  youtube_analytics.video_data \
  gs://your-backup-bucket/video_data_$(date +%Y%m%d).json

# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env api_keys.json service-account.json
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Issue: API Key Quota Exceeded
```bash
# Check API key status
curl http://YOUR_URL/api/status | jq '.api_keys'

# Add more API keys to api_keys.json and restart
```

#### Issue: BigQuery Permission Denied
```bash
# Verify service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:youtube-extractor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

#### Issue: Application Not Starting
```bash
# Check logs
sudo journalctl -u youtube-extractor -f

# Check Docker container
docker logs youtube-extractor

# Verify environment variables
docker exec youtube-extractor env | grep YOUTUBE
```

#### Issue: Low Performance
```bash
# Scale up VM instance
gcloud compute instances set-machine-type youtube-extractor-vm \
  --machine-type=e2-standard-2 \
  --zone=us-central1-a

# Add more worker threads in .env
WORKER_THREADS=8
```

## 📈 Scaling Considerations

### Horizontal Scaling
```bash
# Create instance template
gcloud compute instance-templates create youtube-extractor-template \
  --machine-type=e2-medium \
  --metadata-from-file startup-script=startup-script.sh

# Create managed instance group
gcloud compute instance-groups managed create youtube-extractor-group \
  --base-instance-name=youtube-extractor \
  --size=3 \
  --template=youtube-extractor-template \
  --zone=us-central1-a
```

### Load Balancing
```bash
# Create load balancer
gcloud compute backend-services create youtube-extractor-backend \
  --protocol=HTTP \
  --health-checks=youtube-extractor-health-check \
  --global

# Add instance group to backend
gcloud compute backend-services add-backend youtube-extractor-backend \
  --instance-group=youtube-extractor-group \
  --instance-group-zone=us-central1-a \
  --global
```

## ✅ Deployment Checklist

- [ ] Google Cloud Project setup complete
- [ ] Required APIs enabled
- [ ] Service account created and configured
- [ ] Storage bucket created
- [ ] BigQuery dataset and table created
- [ ] YouTube API keys configured
- [ ] Environment variables set
- [ ] Application deployed successfully
- [ ] Health checks passing
- [ ] Dashboard accessible
- [ ] Data extraction working
- [ ] Monitoring configured
- [ ] Firewall rules configured
- [ ] Backup procedures documented
- [ ] Team access configured
- [ ] Documentation updated

## 🎯 Success Metrics

Your deployment is successful when:

1. **Application Health**: `/health` endpoint returns 200 OK
2. **Data Flow**: Videos are being extracted and stored in BigQuery
3. **API Performance**: All API keys showing healthy status
4. **Dashboard Access**: Web interface loads and displays real-time data
5. **Error Rate**: Less than 1% error rate in logs
6. **Performance**: Processing at least 100 videos per hour
7. **Storage**: Data properly organized in BigQuery and GCS
8. **Monitoring**: Alerts configured and working

## 📞 Support

If you encounter issues during deployment:

1. Check the troubleshooting section above
2. Review application logs
3. Verify all configuration values
4. Test API connectivity
5. Check Google Cloud quotas and billing
6. Create an issue with detailed error logs

---

**Happy Deploying! 🚀**
