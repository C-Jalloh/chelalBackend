# Quick Start Guide

Get up and running with the Chelal Hospital Management System in minutes.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher  
- Redis 6.0 or higher
- Git

## Quick Setup (Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb chelal_hms

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Start Development Server

```bash
# Start the server
python manage.py runserver

# The API will be available at http://localhost:8000/api/
```

## Test the API

### 1. Login to get access token

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

### 2. Use the token to access endpoints

```bash
# Get patients list
curl -H "Authorization: Bearer <your-access-token>" \
  http://localhost:8000/api/patients/

# Create a patient
curl -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer <your-access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe", 
    "date_of_birth": "1990-01-01",
    "gender": "M"
  }'
```

## Next Steps

1. **Learn the API**: [API Documentation](../api/overview.md)
2. **Setup Authentication**: [Authentication Guide](../authentication/README.md)
3. **Development Workflow**: [Development Guidelines](../development/guidelines.md)
4. **Deploy to Production**: [Deployment Guide](../deployment/README.md)

## Need Help?

- [Installation Guide](../installation/README.md) - Detailed installation instructions
- [Troubleshooting](../troubleshooting/README.md) - Common issues and solutions
- [FAQ](../faq/README.md) - Frequently asked questions

## Docker Quick Start

```bash
# Clone repository
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend

# Start with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# API available at http://localhost:8000/api/
```