# Installation Guide - Chelal Hospital Management System

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python**: 3.8 or higher
- **Database**: PostgreSQL 12+
- **Cache**: Redis 6+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 20GB available disk space

### Required Software
- Git
- Docker and Docker Compose (for containerized deployment)
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

## Installation Methods

### Method 1: Docker Deployment (Recommended)

Docker provides the easiest way to deploy the system with all dependencies.

#### 1. Clone the Repository
```bash
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend
```

#### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Database Configuration
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-very-long-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio Configuration (for SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

#### 3. Build and Start Services
```bash
docker-compose up -d --build
```

#### 4. Run Database Migrations
```bash
docker-compose exec web python manage.py migrate
```

#### 5. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

#### 6. Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

#### 7. Access the Application
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

### Method 2: Manual Installation

For development or custom deployments, you can install manually.

#### 1. Clone Repository
```bash
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend
```

#### 2. Set up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Install and Configure PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

**PostgreSQL Commands:**
```sql
CREATE DATABASE chelal_hms;
CREATE USER chelal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chelal_hms TO chelal_user;
ALTER USER chelal_user CREATEDB;
\q
```

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql

# Create database
createdb chelal_hms
```

#### 5. Install and Configure Redis

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

#### 6. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` file:
```env
# Database Configuration
DB_NAME=chelal_hms
DB_USER=chelal_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Other configurations...
```

#### 7. Run Database Migrations
```bash
python manage.py migrate
```

#### 8. Create Superuser
```bash
python manage.py createsuperuser
```

#### 9. Load Initial Data (Optional)
```bash
python manage.py loaddata initial_roles.json
python manage.py loaddata sample_data.json
```

#### 10. Start Development Server
```bash
python manage.py runserver
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-minimum-50-characters-long
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# File Storage (Optional - for production)
USE_S3=False
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=us-east-1

# Celery (Background Tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security Headers
SECURE_SSL_REDIRECT=False  # Set to True in production with HTTPS
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Database Configuration

#### PostgreSQL Settings

For production environments, configure PostgreSQL for optimal performance:

```sql
-- /etc/postgresql/12/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Redis Configuration

For production, configure Redis persistence:

```
# /etc/redis/redis.conf
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Background Task Setup

### Celery Configuration

#### 1. Start Celery Worker
```bash
# In a separate terminal
celery -A Backend worker --loglevel=info
```

#### 2. Start Celery Beat Scheduler
```bash
# In another terminal
celery -A Backend beat --loglevel=info
```

#### 3. Monitor Celery Tasks
```bash
celery -A Backend flower
```
Access Flower at: http://localhost:5555

### Systemd Services (Production)

Create systemd service files for production deployment:

#### Celery Worker Service
```ini
# /etc/systemd/system/chelal-celery.service
[Unit]
Description=Chelal HMS Celery Worker
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/chelalBackend
Environment=PATH=/path/to/chelalBackend/venv/bin
ExecStart=/path/to/chelalBackend/venv/bin/celery -A Backend worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Celery Beat Service
```ini
# /etc/systemd/system/chelal-celerybeat.service
[Unit]
Description=Chelal HMS Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/chelalBackend
Environment=PATH=/path/to/chelalBackend/venv/bin
ExecStart=/path/to/chelalBackend/venv/bin/celery -A Backend beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

## Verification

### Health Checks

#### 1. Database Connection
```bash
python manage.py dbshell
```

#### 2. Redis Connection
```bash
redis-cli ping
```
Should return: `PONG`

#### 3. API Health Check
```bash
curl http://localhost:8000/api/health/
```

#### 4. Run Tests
```bash
python manage.py test
```

### Initial Data Verification

#### 1. Access Django Admin
Navigate to: http://localhost:8000/admin/
Login with superuser credentials

#### 2. Test API Endpoints
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your_password"}'

# Use token to access protected endpoint
curl -X GET http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
django.db.utils.OperationalError: could not connect to server
```

**Solution:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database credentials in `.env`
- Ensure database exists: `psql -U postgres -l`

#### 2. Redis Connection Error
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
- Verify Redis is running: `redis-cli ping`
- Check Redis URL in `.env`
- Restart Redis service: `sudo systemctl restart redis`

#### 3. Static Files Not Loading
```
GET /static/admin/css/base.css 404 (Not Found)
```

**Solution:**
```bash
python manage.py collectstatic --noinput
```

#### 4. Celery Tasks Not Processing
**Solution:**
- Check Celery worker is running
- Verify Redis connection
- Check Celery logs for errors

### Log Locations

- **Django Logs**: Console output or configured log files
- **PostgreSQL Logs**: `/var/log/postgresql/`
- **Redis Logs**: `/var/log/redis/`
- **Nginx Logs**: `/var/log/nginx/` (if using Nginx)

## Next Steps

After successful installation:

1. **Review the [Quick Start Guide](../quickstart/README.md)** for basic usage
2. **Configure [Security Settings](../security/README.md)** for production
3. **Set up [Monitoring](../deployment/monitoring.md)** and logging
4. **Read the [API Documentation](../api/README.md)** to start integrating
5. **Check the [User Guides](../user-guides/README.md)** for end-user documentation

---

For deployment to production environments, see the [Deployment Guide](../deployment/README.md).