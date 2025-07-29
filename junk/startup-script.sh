#!/bin/bash

# Enhanced startup script for Compute Engine instance
# This script runs automatically when the instance starts

set -euo pipefail

# Configuration
APP_NAME="youtube-extractor"
APP_USER="appuser"
APP_DIR="/opt/$APP_NAME"
PYTHON_VERSION="3.11"
LOG_FILE="/var/log/$APP_NAME-startup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting enhanced YouTube Data Extractor setup"

# Update system
log "Updating system packages"
apt-get update -y
apt-get upgrade -y

# Install required packages
log "Installing system dependencies"
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nginx \
    supervisor \
    git \
    curl \
    htop \
    ufw \
    logrotate \
    sqlite3 \
    build-essential \
    pkg-config

# Create application user if it doesn't exist
if ! id -u $APP_USER > /dev/null 2>&1; then
    log "Creating application user: $APP_USER"
    useradd -m -s /bin/bash $APP_USER
    usermod -aG sudo $APP_USER
fi

# Create application directory
log "Setting up application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update application code (if using git)
# Uncomment if you want to pull from git repository
# if [ ! -d ".git" ]; then
#     log "Cloning application repository"
#     git clone https://github.com/yourusername/youtube-extractor.git .
# else
#     log "Updating application from repository"
#     git pull
# fi

# Create virtual environment
log "Creating Python virtual environment"
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
log "Installing Python dependencies"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create necessary directories
log "Creating application directories"
mkdir -p logs data static templates backups
chmod 755 logs data static templates backups

# Set proper permissions
log "Setting file permissions"
chown -R $APP_USER:$APP_USER $APP_DIR
chmod +x main.py

# Create enhanced systemd service
log "Creating systemd service"
cat > /etc/systemd/system/$APP_NAME.service << 'EOF'
[Unit]
Description=Enhanced YouTube Data Extractor for Sri Lanka
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/youtube-extractor
Environment=PATH=/opt/youtube-extractor/venv/bin
Environment=PYTHONPATH=/opt/youtube-extractor
Environment=PYTHONUNBUFFERED=1

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/youtube-extractor

# Restart configuration
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=300

# Execution
ExecStart=/opt/youtube-extractor/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Create enhanced nginx configuration
log "Configuring nginx reverse proxy"
cat > /etc/nginx/sites-available/$APP_NAME << 'EOF'
# Enhanced nginx configuration for YouTube Data Extractor
upstream app_backend {
    server 127.0.0.1:8000 fail_timeout=30s max_fails=3;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 64M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logging
    access_log /var/log/nginx/youtube-extractor.access.log;
    error_log /var/log/nginx/youtube-extractor.error.log;
    
    # Main application
    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        # Enable buffering for better performance
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://app_backend/health;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/youtube-extractor/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }
    
    # Robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
    }
}
EOF

# Enable nginx site
log "Enabling nginx configuration"
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
log "Testing nginx configuration"
nginx -t

# Setup firewall
log "Configuring firewall"
ufw --force enable
ufw allow ssh
ufw allow http
ufw allow https

# Setup logrotate for application logs
log "Configuring log rotation"
cat > /etc/logrotate.d/$APP_NAME << 'EOF'
/opt/youtube-extractor/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 appuser appuser
    postrotate
        systemctl reload youtube-extractor
    endscript
}

/var/log/nginx/youtube-extractor.*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# Create monitoring script
log "Creating monitoring script"
cat > /usr/local/bin/youtube-extractor-monitor.sh << 'EOF'
#!/bin/bash

# Simple monitoring script for YouTube Data Extractor
APP_NAME="youtube-extractor"
LOG_FILE="/var/log/$APP_NAME-monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if service is running
if ! systemctl is-active --quiet $APP_NAME; then
    log "ERROR: $APP_NAME service is not running. Attempting restart..."
    systemctl restart $APP_NAME
    sleep 10
    
    if systemctl is-active --quiet $APP_NAME; then
        log "SUCCESS: $APP_NAME service restarted successfully"
    else
        log "CRITICAL: Failed to restart $APP_NAME service"
    fi
fi

# Check if application is responding
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log "WARNING: Application health check failed"
else
    log "INFO: Application health check passed"
fi

# Check disk space
DISK_USAGE=$(df /opt | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    log "WARNING: Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | awk 'FNR==2{printf "%.2f", $3/($3+$4)*100}')
if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
    log "WARNING: Memory usage is at ${MEMORY_USAGE}%"
fi
EOF

chmod +x /usr/local/bin/youtube-extractor-monitor.sh

# Setup cron job for monitoring
log "Setting up monitoring cron job"
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/youtube-extractor-monitor.sh") | crontab -

# Reload systemd and start services
log "Starting services"
systemctl daemon-reload
systemctl enable $APP_NAME
systemctl enable nginx

# Start nginx first
systemctl restart nginx
sleep 2

# Start the application
systemctl restart $APP_NAME
sleep 5

# Check service status
log "Checking service status"
if systemctl is-active --quiet $APP_NAME; then
    log "✅ $APP_NAME service is running"
else
    log "❌ $APP_NAME service failed to start"
    systemctl status $APP_NAME --no-pager
fi

if systemctl is-active --quiet nginx; then
    log "✅ nginx service is running"
else
    log "❌ nginx service failed to start"
    systemctl status nginx --no-pager
fi

# Final health check
log "Performing final health check"
sleep 10
if curl -f http://localhost/health > /dev/null 2>&1; then
    log "✅ Application is responding to health checks"
    log "🎉 Enhanced YouTube Data Extractor setup completed successfully!"
    
    # Get external IP
    EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google" 2>/dev/null || echo "Unable to determine")
    log "📍 Application is available at: http://$EXTERNAL_IP"
    log "📊 Health check: http://$EXTERNAL_IP/health"
    log "📈 Dashboard: http://$EXTERNAL_IP/"
    log "📚 API Documentation: http://$EXTERNAL_IP/docs"
else
    log "❌ Application health check failed. Check logs for details."
    log "🔍 Check application logs: journalctl -u $APP_NAME -f"
    log "🔍 Check nginx logs: tail -f /var/log/nginx/youtube-extractor.error.log"
fi

log "Setup script completed. Check $LOG_FILE for details."
