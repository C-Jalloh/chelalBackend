# Troubleshooting Guide

Common issues and solutions for the Chelal Hospital Management System.

## Installation Issues

### Django Backend Module Not Found

**Error**: `ModuleNotFoundError: No module named 'Backend'`

**Solution**:
```bash
# Ensure Backend directory exists with proper files
mkdir -p Backend
# Copy the configuration files from docs/installation/
# Or check if the Backend directory was created correctly
```

### Database Connection Issues

**Error**: `django.db.utils.OperationalError: FATAL: database "chelal_hms" does not exist`

**Solution**:
```bash
# Create the database
sudo -u postgres createdb chelal_hms

# Or using psql
sudo -u postgres psql
CREATE DATABASE chelal_hms;
\q
```

**Error**: `django.db.utils.OperationalError: FATAL: password authentication failed`

**Solution**:
```bash
# Reset PostgreSQL password
sudo -u postgres psql
ALTER USER postgres PASSWORD 'newpassword';
\q

# Update your .env file with the correct password
```

### Redis Connection Issues

**Error**: `ConnectionError: Error 111 connecting to localhost:6379. Connection refused.`

**Solution**:
```bash
# Install and start Redis
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis connection
redis-cli ping
# Should return "PONG"
```

### Python Package Issues

**Error**: `ImportError: No module named 'PIL'`

**Solution**:
```bash
# Install Pillow for image handling
pip install Pillow

# Or reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## API Issues

### Authentication Errors

**Error**: `401 Unauthorized: Authentication credentials were not provided`

**Solution**:
```bash
# Ensure you're including the Authorization header
curl -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/api/patients/

# Check if token is expired - login again to get new token
```

**Error**: `403 Forbidden: You do not have permission to perform this action`

**Solution**:
- Check user role and permissions
- Verify the user has the required role for the endpoint
- Contact admin to assign proper permissions

### Token Issues

**Error**: `Token is invalid or expired`

**Solution**:
```bash
# Use refresh token to get new access token
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your-refresh-token"}'

# Or login again
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

## Development Issues

### Migration Errors

**Error**: `django.db.utils.IntegrityError: duplicate key value violates unique constraint`

**Solution**:
```bash
# Reset migrations (development only)
python manage.py migrate core zero
python manage.py migrate

# Or manually fix data conflicts in database
```

**Error**: `Migration is unapplied`

**Solution**:
```bash
# Check migration status
python manage.py showmigrations

# Apply specific migration
python manage.py migrate core 0001_initial

# Or apply all migrations
python manage.py migrate
```

### Static Files Issues

**Error**: Static files not loading (CSS, JS not found)

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# For development, ensure DEBUG=True in settings
# For production, configure web server to serve static files
```

### Import Errors

**Error**: `ImportError: attempted relative import with no known parent package`

**Solution**:
- Check Python path and module structure
- Ensure `__init__.py` files exist in directories
- Use absolute imports instead of relative imports

## Performance Issues

### Slow Database Queries

**Issue**: API responses are slow

**Solution**:
```python
# Add database indexes for frequently queried fields
# Check django.log for slow queries
# Use select_related() and prefetch_related() in views

# Example optimization
patients = Patient.objects.select_related('insurance').prefetch_related('encounter_set')
```

### High Memory Usage

**Issue**: Application consuming too much memory

**Solution**:
```bash
# Monitor memory usage
ps aux --sort=-%mem | head

# Optimize database queries
# Implement pagination for large datasets
# Use database aggregation instead of Python loops
```

### Redis Memory Issues

**Issue**: Redis running out of memory

**Solution**:
```bash
# Check Redis memory usage
redis-cli info memory

# Configure Redis max memory
# In redis.conf:
# maxmemory 256mb
# maxmemory-policy allkeys-lru

sudo systemctl restart redis-server
```

## Deployment Issues

### Docker Issues

**Error**: `docker-compose: command not found`

**Solution**:
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Error**: `Permission denied while trying to connect to Docker daemon`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

### Nginx Issues

**Error**: `502 Bad Gateway`

**Solution**:
```bash
# Check if application is running
ps aux | grep gunicorn

# Check Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Error**: SSL certificate issues

**Solution**:
```bash
# Check certificate files exist and are readable
ls -la /etc/ssl/certs/your-domain.crt
ls -la /etc/ssl/private/your-domain.key

# Test SSL configuration
openssl s_client -connect your-domain.com:443
```

### Gunicorn Issues

**Error**: `gunicorn: command not found`

**Solution**:
```bash
# Install gunicorn in virtual environment
source venv/bin/activate
pip install gunicorn

# Or check if virtual environment is activated
which python
```

**Error**: Gunicorn workers dying

**Solution**:
```bash
# Check gunicorn error logs
tail -f /var/log/gunicorn/error.log

# Increase worker memory limit
# Or reduce number of workers if memory constrained
gunicorn --workers 2 --max-requests 1000
```

## Security Issues

### Failed Login Attempts

**Issue**: Multiple failed login attempts from IP

**Solution**:
- Check audit logs for patterns
- Implement rate limiting
- Consider blocking suspicious IPs
- Enable account lockout after multiple failures

### Suspicious Activity

**Issue**: Unusual API access patterns

**Solution**:
```bash
# Check access logs
tail -f /var/log/nginx/access.log

# Check Django audit logs
tail -f /var/log/chelal/django.log | grep "AUDIT"

# Monitor for unusual patterns
# Implement additional monitoring and alerting
```

## Monitoring and Debugging

### Enable Debug Mode

```python
# In settings.py (development only)
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Database Query Analysis

```python
# Add to view to see SQL queries
from django.db import connection
print(len(connection.queries))
for query in connection.queries:
    print(query['sql'])
```

### API Response Debugging

```bash
# Use curl with verbose output
curl -v -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/patients/

# Use httpie for better formatted output
http GET localhost:8000/api/patients/ \
  Authorization:"Bearer <token>"
```

## Getting Help

### Log Locations

```bash
# Application logs
tail -f /var/log/chelal/django.log

# Database logs
tail -f /var/log/postgresql/postgresql-14-main.log

# Web server logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u chelal-hms -f
```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/api/health/

# Check database connectivity
python manage.py dbshell

# Check Redis connectivity
redis-cli ping
```

### Debug Commands

```bash
# Django shell for debugging
python manage.py shell

# Check Django configuration
python manage.py check

# Test email configuration
python manage.py sendtestemail your-email@example.com

# Show Django settings
python manage.py diffsettings
```

### Support Channels

1. **Documentation**: Check relevant documentation sections
2. **Logs**: Review application and system logs
3. **Issues**: Create GitHub issue with detailed information
4. **Community**: Join project discussions

### Creating a Bug Report

Include the following information:
- Django version and Python version
- Operating system and version
- Complete error message and traceback
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant configuration files (sanitized)

### Performance Profiling

```python
# Add Django Debug Toolbar for development
pip install django-debug-toolbar

# Add to INSTALLED_APPS
INSTALLED_APPS += ['debug_toolbar']

# Add to middleware
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Configure internal IPs
INTERNAL_IPS = ['127.0.0.1']
```

---

For more help:
- [Installation Guide](../installation/README.md)
- [Development Guidelines](../development/guidelines.md)
- [Deployment Guide](../deployment/README.md)
- [FAQ](../faq/README.md)