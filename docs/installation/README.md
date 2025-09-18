# Installation Guide

This guide covers the installation and initial setup of the Chelal Hospital Management System backend.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- PostgreSQL 12 or higher
- Redis 6.0 or higher (for caching and WebSocket support)
- Git

### Development Tools (Optional)
- Docker and Docker Compose
- Postman or similar API testing tool
- Python virtual environment manager (venv, conda, etc.)

## Installation Methods

### Method 1: Local Development Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```bash
cp .env.example .env  # If .env.example exists
```

Edit `.env` with your configuration:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone
```

#### 5. Set Up Database
```bash
# Create PostgreSQL database
sudo -u postgres createdb chelal_hms

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### 6. Install Additional Dependencies
```bash
# For image handling
pip install Pillow

# For development (optional)
pip install django-debug-toolbar
```

#### 7. Run the Development Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### Method 2: Docker Setup

#### 1. Clone Repository
```bash
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend
```

#### 2. Build and Run with Docker Compose
```bash
docker-compose up --build
```

This will start:
- Django application on port 8000
- PostgreSQL database on port 5432
- Redis on port 6379

#### 3. Run Migrations in Docker
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Post-Installation Setup

### 1. Load Initial Data (Optional)
```bash
python manage.py loaddata fixtures/initial_data.json
```

### 2. Set Up Celery (for background tasks)
```bash
# Start Celery worker
celery -A Backend worker -l info

# Start Celery beat (scheduler)
celery -A Backend beat -l info
```

### 3. Configure External Services

#### Email Configuration
Update email settings in your `.env` file for appointment reminders and notifications.

#### SMS Configuration (Twilio)
Set up Twilio credentials for SMS appointment reminders.

### 4. Verify Installation
```bash
# Run system checks
python manage.py check

# Run tests
python manage.py test

# Check API endpoints
curl http://localhost:8000/api/
```

## Common Installation Issues

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep chelal_hms
```

### Redis Connection Issues
```bash
# Check Redis is running
redis-cli ping

# Should return "PONG"
```

### Python Package Issues
```bash
# Clear pip cache
pip cache purge

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. [API Overview](../api/overview.md) - Learn about the API structure
2. [Authentication](../authentication/README.md) - Set up API authentication
3. [Development Setup](../development/setup.md) - Configure development environment
4. [Deployment Guide](../deployment/README.md) - Deploy to production

## Support

If you encounter issues during installation:
1. Check the [Troubleshooting Guide](../troubleshooting/README.md)
2. Review the [FAQ](../faq/README.md)
3. Contact the development team