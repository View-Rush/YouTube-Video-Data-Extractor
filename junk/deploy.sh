#!/bin/bash

# Deployment script for Google Cloud Compute Engine

set -e

echo "Deploying YouTube Data Extractor to Google Cloud Compute Engine..."

# Variables
PROJECT_ID=${1:-"your-project-id"}
INSTANCE_NAME=${2:-"youtube-extractor"}
ZONE=${3:-"us-central1-a"}
MACHINE_TYPE=${4:-"e2-medium"}

# Create compute instance if it doesn't exist
echo "Creating Compute Engine instance..."
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=$(gcloud iam service-accounts list --filter="displayName:Compute Engine default service account" --format="value(email)") \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20231030,mode=rw,size=20,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,application=youtube-extractor \
    --reservation-affinity=any \
    --tags=http-server,https-server || echo "Instance might already exist"

# Wait for instance to be ready
echo "Waiting for instance to be ready..."
sleep 30

# Copy files to instance
echo "Copying application files to instance..."
gcloud compute scp --zone=$ZONE --project=$PROJECT_ID --recurse . $INSTANCE_NAME:~/youtube-extractor/

# Install and setup application
echo "Setting up application on instance..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    set -e
    
    # Update system
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv nginx supervisor
    
    # Create application directory
    sudo mkdir -p /opt/youtube-extractor
    sudo cp -r ~/youtube-extractor/* /opt/youtube-extractor/
    sudo chown -R www-data:www-data /opt/youtube-extractor
    
    # Create virtual environment and install dependencies
    cd /opt/youtube-extractor
    sudo -u www-data python3 -m venv venv
    sudo -u www-data venv/bin/pip install --upgrade pip
    sudo -u www-data venv/bin/pip install -r requirements.txt
    
    # Create logs directory
    sudo -u www-data mkdir -p /opt/youtube-extractor/logs
    
    # Setup systemd service
    sudo cp youtube-extractor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable youtube-extractor
    
    # Setup nginx reverse proxy
    sudo tee /etc/nginx/sites-available/youtube-extractor > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Enable nginx site
    sudo ln -sf /etc/nginx/sites-available/youtube-extractor /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    # Start the application
    sudo systemctl start youtube-extractor
    sudo systemctl status youtube-extractor
"

echo "Deployment completed!"
echo "Access your application at: http://$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"
