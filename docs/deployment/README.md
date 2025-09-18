# Deployment Guide - Chelal Hospital Management System

## Overview

This guide covers production deployment of the Chelal HMS, including infrastructure setup, security configuration, monitoring, and maintenance procedures.

## Deployment Architecture

### Production Infrastructure

```
Internet → Load Balancer → Web Servers → Application → Database
                       → Static Files   → Redis Cache
                                      → Background Tasks
```

**Components:**
- **Load Balancer**: Nginx or AWS ALB
- **Web Servers**: Multiple Gunicorn instances
- **Database**: PostgreSQL with replication
- **Cache**: Redis cluster
- **Background Tasks**: Celery workers
- **Static Files**: CDN or S3 storage
- **Monitoring**: Logging and metrics collection

## Production Environment Setup

### Server Requirements

#### Minimum Specifications
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Network**: 1Gbps connection
- **OS**: Ubuntu 20.04 LTS or similar

#### Recommended Specifications
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 200GB+ SSD with backup
- **Network**: High-speed redundant connections
- **OS**: Ubuntu 22.04 LTS

### Infrastructure Components

#### Database Server (PostgreSQL)
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql-14 postgresql-contrib

# Configure PostgreSQL
sudo -u postgres createdb chelal_hms_prod
sudo -u postgres createuser chelal_user
sudo -u postgres psql -c "ALTER USER chelal_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chelal_hms_prod TO chelal_user;"
```

**Production Configuration (`/etc/postgresql/14/main/postgresql.conf`):**
```conf
# Memory settings
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Connection settings
max_connections = 200
listen_addresses = '*'

# Performance settings
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Redis Server
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis for production
sudo nano /etc/redis/redis.conf
```

**Redis Configuration:**
```conf
# Security
requirepass your_redis_password
bind 127.0.0.1

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

#### Web Server (Nginx)
```bash
# Install Nginx
sudo apt install nginx

# Configure SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**Nginx Configuration (`/etc/nginx/sites-available/chelal-hms`):**
```nginx
upstream chelal_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # File Upload
    client_max_body_size 10M;
    
    # Static Files
    location /static/ {
        alias /var/www/chelal-hms/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/chelal-hms/media/;
        expires 30d;
    }
    
    # API Endpoints
    location / {
        proxy_pass http://chelal_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Application Deployment

### Using Docker (Recommended)

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build: .
    restart: always
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/chelal_hms_prod
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    command: gunicorn Backend.wsgi:application --workers 4 --bind 0.0.0.0:8000

  worker:
    build: .
    restart: always
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/chelal_hms_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A Backend worker --loglevel=info

  beat:
    build: .
    restart: always
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/chelal_hms_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A Backend beat --loglevel=info

  db:
    image: postgres:14
    restart: always
    environment:
      - POSTGRES_DB=chelal_hms_prod
      - POSTGRES_USER=chelal_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --requirepass your_redis_password
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

#### Deployment Script
```bash
#!/bin/bash
# deploy.sh

set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build and deploy
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Restart services
docker-compose -f docker-compose.prod.yml restart web worker beat

echo "Deployment complete!"
```

### Manual Deployment

#### Application Setup
```bash
# Create application user
sudo useradd --system --shell /bin/bash --home /opt/chelal-hms chelal

# Clone application
sudo git clone https://github.com/C-Jalloh/chelalBackend.git /opt/chelal-hms/app
sudo chown -R chelal:chelal /opt/chelal-hms

# Setup Python environment
sudo -u chelal python3 -m venv /opt/chelal-hms/venv
sudo -u chelal /opt/chelal-hms/venv/bin/pip install -r /opt/chelal-hms/app/requirements.txt
```

#### Environment Configuration
```bash
# Production environment file
sudo -u chelal nano /opt/chelal-hms/.env
```

```env
# Production Environment
DEBUG=False
SECRET_KEY=your-very-long-secret-key-minimum-50-characters
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Database
DATABASE_URL=postgresql://chelal_user:secure_password@localhost:5432/chelal_hms_prod

# Redis
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password

# File Storage (AWS S3)
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=chelal-hms-media
AWS_S3_REGION_NAME=us-east-1
```

#### Systemd Services

**Gunicorn Service (`/etc/systemd/system/chelal-hms.service`):**
```ini
[Unit]
Description=Chelal HMS Django Application
After=network.target

[Service]
Type=notify
User=chelal
Group=chelal
WorkingDirectory=/opt/chelal-hms/app
Environment=PATH=/opt/chelal-hms/venv/bin
EnvironmentFile=/opt/chelal-hms/.env
ExecStart=/opt/chelal-hms/venv/bin/gunicorn Backend.wsgi:application \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/chelal-hms/access.log \
    --error-logfile /var/log/chelal-hms/error.log \
    --log-level info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service (`/etc/systemd/system/chelal-celery.service`):**
```ini
[Unit]
Description=Chelal HMS Celery Worker
After=network.target

[Service]
Type=forking
User=chelal
Group=chelal
WorkingDirectory=/opt/chelal-hms/app
Environment=PATH=/opt/chelal-hms/venv/bin
EnvironmentFile=/opt/chelal-hms/.env
ExecStart=/opt/chelal-hms/venv/bin/celery -A Backend worker \
    --detach \
    --loglevel=info \
    --logfile=/var/log/chelal-hms/celery-worker.log \
    --pidfile=/var/run/chelal-hms/celery-worker.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Celery Beat Service (`/etc/systemd/system/chelal-celerybeat.service`):**
```ini
[Unit]
Description=Chelal HMS Celery Beat
After=network.target

[Service]
Type=simple
User=chelal
Group=chelal
WorkingDirectory=/opt/chelal-hms/app
Environment=PATH=/opt/chelal-hms/venv/bin
EnvironmentFile=/opt/chelal-hms/.env
ExecStart=/opt/chelal-hms/venv/bin/celery -A Backend beat \
    --loglevel=info \
    --logfile=/var/log/chelal-hms/celery-beat.log \
    --pidfile=/var/run/chelal-hms/celery-beat.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Service Management
```bash
# Enable and start services
sudo systemctl enable chelal-hms
sudo systemctl enable chelal-celery
sudo systemctl enable chelal-celerybeat

sudo systemctl start chelal-hms
sudo systemctl start chelal-celery
sudo systemctl start chelal-celerybeat

# Check status
sudo systemctl status chelal-hms
sudo systemctl status chelal-celery
sudo systemctl status chelal-celerybeat
```

## Database Management

### Database Backup

#### Automated Backup Script
```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/opt/backups/chelal-hms"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="chelal_hms_prod"
DB_USER="chelal_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME -f $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: backup_$DATE.sql.gz"
```

#### Backup Cron Job
```bash
# Add to crontab (crontab -e)
0 2 * * * /opt/scripts/backup-db.sh >> /var/log/chelal-hms/backup.log 2>&1
```

### Database Restore
```bash
# Restore from backup
gunzip backup_20240917_020000.sql.gz
psql -h localhost -U chelal_user -d chelal_hms_prod -f backup_20240917_020000.sql
```

## Monitoring & Logging

### Application Logging

#### Django Logging Configuration
```python
# settings.py
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
            'filename': '/var/log/chelal-hms/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chelal-hms/django-error.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Health Monitoring

#### Health Check Endpoint
```python
# views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """System health check endpoint."""
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Redis check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        status['services']['redis'] = 'healthy'
    except Exception as e:
        status['services']['redis'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Celery check
    try:
        from django_celery_results.models import TaskResult
        recent_tasks = TaskResult.objects.filter(
            date_created__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        status['services']['celery'] = f'healthy ({recent_tasks} recent tasks)'
    except Exception as e:
        status['services']['celery'] = f'unhealthy: {str(e)}'
    
    return JsonResponse(status)
```

#### External Monitoring

**Uptime Monitoring Script:**
```bash
#!/bin/bash
# monitor.sh

URL="https://your-domain.com/health/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): Service is healthy"
else
    echo "$(date): Service is down (HTTP $RESPONSE)"
    # Send alert (email, SMS, Slack, etc.)
    # /opt/scripts/send-alert.sh "Chelal HMS is down"
fi
```

### Log Analysis

#### Log Rotation
```bash
# /etc/logrotate.d/chelal-hms
/var/log/chelal-hms/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 chelal chelal
    postrotate
        systemctl reload chelal-hms
    endscript
}
```

## Security Configuration

### SSL/TLS Setup

#### Let's Encrypt Certificate
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration
```bash
# UFW Firewall
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8000/tcp  # Block direct app access
```

### Security Headers
```nginx
# Additional Nginx security headers
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
```

## Performance Optimization

### Database Optimization

#### PostgreSQL Tuning
```sql
-- Create indexes for common queries
CREATE INDEX CONCURRENTLY idx_patient_search ON core_patient USING gin(to_tsvector('english', first_name || ' ' || last_name));
CREATE INDEX CONCURRENTLY idx_appointment_date_doctor ON core_appointment(date, doctor_id);
CREATE INDEX CONCURRENTLY idx_encounter_patient_date ON core_encounter(patient_id, start_time);

-- Analyze table statistics
ANALYZE;
```

#### Connection Pooling
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'chelal_hms_prod',
        'USER': 'chelal_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,
    }
}
```

### Caching Strategy

#### Redis Configuration
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'chelal_hms',
        'TIMEOUT': 300,
    }
}

# Session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
- Monitor system health
- Check log files for errors
- Verify backup completion
- Review performance metrics

#### Weekly Tasks
- Update system packages
- Review security logs
- Analyze database performance
- Check disk space usage

#### Monthly Tasks
- Security patch updates
- Database maintenance (VACUUM, REINDEX)
- Review and rotate logs
- Update documentation

### Update Procedures

#### Application Updates
```bash
#!/bin/bash
# update-app.sh

# Backup current version
sudo -u chelal cp -r /opt/chelal-hms/app /opt/chelal-hms/app.backup.$(date +%Y%m%d)

# Pull updates
cd /opt/chelal-hms/app
sudo -u chelal git pull origin main

# Update dependencies
sudo -u chelal /opt/chelal-hms/venv/bin/pip install -r requirements.txt

# Run migrations
sudo -u chelal /opt/chelal-hms/venv/bin/python manage.py migrate

# Collect static files
sudo -u chelal /opt/chelal-hms/venv/bin/python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart chelal-hms
sudo systemctl restart chelal-celery
sudo systemctl restart chelal-celerybeat

echo "Application update completed"
```

### Disaster Recovery

#### Recovery Procedures
1. **Assess Damage**: Determine scope of outage
2. **Restore from Backup**: Use latest valid backup
3. **Verify Data Integrity**: Check data consistency
4. **Restart Services**: Bring system back online
5. **Test Functionality**: Verify all features work
6. **Document Incident**: Record lessons learned

---

For security-specific deployment considerations, see the [Security Guide](../security/README.md).
For monitoring and troubleshooting, see the [Troubleshooting Guide](./troubleshooting.md).