# Deployment Guide

This guide covers deploying the Chelal Hospital Management System to production environments.

## Overview

The Chelal HMS can be deployed using various strategies:
- Docker containers with orchestration (recommended)
- Traditional server deployment
- Cloud platform deployment (AWS, GCP, Azure)
- Kubernetes clusters

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: Reliable internet connection with TLS certificates

### Required Services
- PostgreSQL 12+ database server
- Redis 6.0+ for caching and WebSocket support
- Web server (Nginx recommended)
- SSL/TLS certificates
- SMTP server for email notifications
- SMS service (Twilio) for SMS notifications

## Docker Deployment (Recommended)

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_HOST=db
      - DB_NAME=chelal_hms
      - DB_USER=postgres
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=chelal_hms
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

  celery:
    build: .
    command: celery -A Backend worker -l info
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A Backend beat -l info
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### 2. Production Environment File

Create `.env.prod`:

```bash
# Security
SECRET_KEY=your-super-secret-key-here
DEBUG=False

# Database
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Twilio SMS
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone

# Security Settings
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Storage (AWS S3 example)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=us-east-1
```

### 3. Production Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "Backend.wsgi:application"]
```

### 4. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server web:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Admin interface
        location /admin/ {
            proxy_pass http://app;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /app/media/;
            expires 1y;
            add_header Cache-Control "public";
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 5. Deployment Commands

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files (if not done in Dockerfile)
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Traditional Server Deployment

### 1. Server Setup (Ubuntu 20.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx supervisor -y

# Install Node.js for frontend assets (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE chelal_hms;
CREATE USER chelal_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chelal_hms TO chelal_user;
\q

# Configure PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Uncomment and modify:
# listen_addresses = 'localhost'
# max_connections = 100

sudo systemctl restart postgresql
```

### 3. Application Setup

```bash
# Create application user
sudo adduser --system --group --home /opt/chelal chelal

# Clone repository
sudo -u chelal git clone https://github.com/C-Jalloh/chelalBackend.git /opt/chelal/app
cd /opt/chelal/app

# Create virtual environment
sudo -u chelal python3.11 -m venv venv
sudo -u chelal ./venv/bin/pip install -r requirements.txt

# Create environment file
sudo -u chelal cp .env.example .env.prod
sudo -u chelal nano .env.prod
# Configure production settings

# Run migrations
sudo -u chelal ./venv/bin/python manage.py migrate
sudo -u chelal ./venv/bin/python manage.py collectstatic --noinput
sudo -u chelal ./venv/bin/python manage.py createsuperuser
```

### 4. Gunicorn Configuration

Create `/etc/supervisor/conf.d/chelal.conf`:

```ini
[program:chelal]
command=/opt/chelal/app/venv/bin/gunicorn --workers 3 --bind unix:/opt/chelal/app/gunicorn.sock Backend.wsgi:application
directory=/opt/chelal/app
user=chelal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chelal/gunicorn.log
environment=PATH="/opt/chelal/app/venv/bin"

[program:chelal-celery]
command=/opt/chelal/app/venv/bin/celery -A Backend worker -l info
directory=/opt/chelal/app
user=chelal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chelal/celery.log
environment=PATH="/opt/chelal/app/venv/bin"

[program:chelal-celery-beat]
command=/opt/chelal/app/venv/bin/celery -A Backend beat -l info
directory=/opt/chelal/app
user=chelal
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/chelal/celery-beat.log
environment=PATH="/opt/chelal/app/venv/bin"
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/chelal`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /opt/chelal/app;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        root /opt/chelal/app;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/chelal/app/gunicorn.sock;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/chelal /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance Setup
```bash
# Launch EC2 instance (Ubuntu 20.04)
# Configure security group:
# - Port 22 (SSH)
# - Port 80 (HTTP)
# - Port 443 (HTTPS)
# - Port 5432 (PostgreSQL - only from app servers)

# Instance recommendations:
# - t3.medium for development
# - t3.large or m5.large for production
# - c5.xlarge for high-traffic production
```

#### 2. RDS Database Setup
```bash
# Create RDS PostgreSQL instance
# Engine: PostgreSQL 14
# Instance class: db.t3.micro (dev) or db.t3.small (prod)
# Storage: 20GB+ with auto-scaling
# Backup retention: 7 days
# Multi-AZ: Yes for production
```

#### 3. ElastiCache Redis Setup
```bash
# Create ElastiCache Redis cluster
# Node type: cache.t3.micro (dev) or cache.t3.small (prod)
# Number of replicas: 1 for production
# Backup retention: 5 days
```

#### 4. S3 Storage for Media Files
```python
# settings.py additions for S3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'private'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Storage backends
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'
```

### Google Cloud Platform

#### 1. Compute Engine Setup
```bash
# Create Compute Engine instance
gcloud compute instances create chelal-hms \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server
```

#### 2. Cloud SQL PostgreSQL
```bash
# Create Cloud SQL instance
gcloud sql instances create chelal-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1
```

#### 3. Cloud Storage for Media
```python
# settings.py for Google Cloud Storage
GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID')
GS_DEFAULT_ACL = 'private'

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
```

## Kubernetes Deployment

### 1. Deployment Configuration

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chelal-hms
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chelal-hms
  template:
    metadata:
      labels:
        app: chelal-hms
    spec:
      containers:
      - name: chelal-hms
        image: chelal/hms:latest
        ports:
        - containerPort: 8000
        env:
        - name: DEBUG
          value: "False"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: chelal-secrets
              key: secret-key
        - name: DB_HOST
          value: postgres-service
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: chelal-hms-service
spec:
  selector:
    app: chelal-hms
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 2. ConfigMap and Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: chelal-secrets
type: Opaque
data:
  secret-key: <base64-encoded-secret>
  db-password: <base64-encoded-password>
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: chelal-config
data:
  DEBUG: "False"
  ALLOWED_HOSTS: "your-domain.com,www.your-domain.com"
```

## Monitoring and Logging

### 1. Application Monitoring

```python
# Add to requirements.txt
sentry-sdk[django]==1.14.0
django-prometheus==2.2.0

# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True
)

# Add to INSTALLED_APPS
INSTALLED_APPS += ['django_prometheus']

# Add to middleware
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

### 2. Log Configuration

```python
# Enhanced logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chelal/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.SentryHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console', 'sentry'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'console', 'sentry'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 3. Health Checks

```python
# health_check/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """Basic health check endpoint."""
    status = {
        'status': 'ok',
        'database': 'unknown',
        'cache': 'unknown',
        'redis': 'unknown'
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['database'] = 'ok'
    except Exception:
        status['database'] = 'error'
        status['status'] = 'error'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 30)
        if cache.get('health_check') == 'ok':
            status['cache'] = 'ok'
        else:
            status['cache'] = 'error'
    except Exception:
        status['cache'] = 'error'
        status['status'] = 'error'
    
    # Redis check
    try:
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        status['redis'] = 'ok'
    except Exception:
        status['redis'] = 'error'
        status['status'] = 'error'
    
    return JsonResponse(status)
```

## Backup and Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="chelal_hms"

# Create backup
pg_dump -h localhost -U postgres $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/database/
```

### 2. Media Files Backup

```bash
#!/bin/bash
# backup_media.sh

DATE=$(date +%Y%m%d_%H%M%S)
MEDIA_DIR="/app/media"
BACKUP_DIR="/backup/media"

# Create compressed backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $MEDIA_DIR .

# Upload to S3
aws s3 cp $BACKUP_DIR/media_$DATE.tar.gz s3://your-backup-bucket/media/

# Keep only last 30 days locally
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +30 -delete
```

### 3. Automated Backup with Cron

```bash
# Add to crontab
# Database backup daily at 2 AM
0 2 * * * /opt/chelal/scripts/backup_db.sh

# Media backup weekly on Sunday at 3 AM
0 3 * * 0 /opt/chelal/scripts/backup_media.sh

# System backup monthly on 1st at 4 AM
0 4 1 * * /opt/chelal/scripts/backup_system.sh
```

## Security Considerations

### 1. Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. SSL/TLS Certificates

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Security Updates

```bash
# Automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_patient_last_name ON core_patient(last_name);
CREATE INDEX idx_appointment_date ON core_appointment(appointment_date);
CREATE INDEX idx_encounter_patient ON core_encounter(patient_id);
CREATE INDEX idx_encounter_doctor ON core_encounter(doctor_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM core_patient WHERE last_name = 'Smith';
```

### 2. Caching Strategy

```python
# Redis caching configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'chelal',
        'TIMEOUT': 300,
    }
}

# Cache frequently accessed data
from django.core.cache import cache

def get_patient_summary(patient_id):
    cache_key = f'patient_summary_{patient_id}'
    summary = cache.get(cache_key)
    if summary is None:
        summary = calculate_patient_summary(patient_id)
        cache.set(cache_key, summary, 3600)  # Cache for 1 hour
    return summary
```

### 3. Static File Optimization

```python
# Static file compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add to middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]
```

## Troubleshooting

### Common Deployment Issues

#### Database Connection Errors
```bash
# Check database connectivity
pg_isready -h localhost -p 5432

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### Static Files Not Loading
```bash
# Verify static files collection
python manage.py collectstatic --noinput --verbosity=2

# Check Nginx static file configuration
sudo nginx -t
sudo systemctl reload nginx
```

#### High Memory Usage
```bash
# Monitor memory usage
free -h
ps aux --sort=-%mem | head

# Optimize Gunicorn workers
# Rule of thumb: (2 x CPU cores) + 1
gunicorn --workers 5 --max-requests 1000 --max-requests-jitter 50
```

### Log Analysis

```bash
# Django application logs
tail -f /var/log/chelal/django.log

# Nginx access logs
tail -f /var/log/nginx/access.log

# Database slow queries
sudo tail -f /var/log/postgresql/postgresql-14-main.log | grep "slow query"
```

## Maintenance Tasks

### Regular Maintenance

```bash
#!/bin/bash
# maintenance.sh - Run weekly

# Update system packages
apt update && apt upgrade -y

# Clean up old log files
find /var/log -name "*.log" -mtime +30 -delete

# Vacuum PostgreSQL database
sudo -u postgres vacuumdb --all --analyze

# Clear old cache entries
echo "FLUSHDB" | redis-cli

# Django cleanup
python manage.py clearsessions
python manage.py clear_cache
```

### Database Maintenance

```sql
-- Weekly database maintenance
VACUUM ANALYZE;
REINDEX DATABASE chelal_hms;

-- Monitor database size
SELECT pg_size_pretty(pg_database_size('chelal_hms'));

-- Check for long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

## Scaling Considerations

### Horizontal Scaling

```yaml
# Load balancer configuration
version: '3.8'
services:
  web1:
    <<: *web-service
  web2:
    <<: *web-service
  web3:
    <<: *web-service
  
  load-balancer:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - web1
      - web2
      - web3
```

### Database Scaling

```python
# Read replica configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chelal_hms',
        'HOST': 'master-db.example.com',
        # ... other settings
    },
    'read': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chelal_hms',
        'HOST': 'read-replica.example.com',
        # ... other settings
    }
}

DATABASE_ROUTERS = ['core.routers.DatabaseRouter']
```

For more information, see:
- [Operations Guide](../operations/README.md)
- [Monitoring Setup](../operations/monitoring.md)
- [Security Guidelines](../security/README.md)