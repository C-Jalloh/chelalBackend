# Configuration Guide - Chelal Hospital Management System

## Overview

This guide covers configuration options for the Chelal HMS, including environment settings, feature toggles, and customization options for different deployment scenarios.

## Environment Configuration

### Environment Variables

#### Core Django Settings
```env
# Basic Django Configuration
DEBUG=False
SECRET_KEY=your-very-long-secret-key-minimum-50-characters-long-and-random
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com,api.your-domain.com

# Language and Timezone
LANGUAGE_CODE=en-us
TIME_ZONE=UTC
USE_I18N=True
USE_L10N=True
USE_TZ=True
```

#### Database Configuration
```env
# PostgreSQL Database
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Alternative format
DB_NAME=chelal_hms
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
DB_SSL_REQUIRE=False  # Set to True in production
```

#### Cache Configuration
```env
# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# Cache timeout settings
CACHE_TIMEOUT=300  # 5 minutes default
SESSION_CACHE_TIMEOUT=1800  # 30 minutes
```

#### Email Configuration
```env
# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@hospital.com
```

#### SMS Configuration (Twilio)
```env
# Twilio SMS Settings
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SMS_ENABLED=True
```

#### File Storage Configuration
```env
# Local File Storage (Development)
MEDIA_ROOT=/path/to/media/files
STATIC_ROOT=/path/to/static/files

# AWS S3 Storage (Production)
USE_S3=True
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=your-cloudfront-domain.com
```

#### Security Configuration
```env
# Security Settings
SECURE_SSL_REDIRECT=True  # Force HTTPS
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# Session Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Strict'
SESSION_COOKIE_AGE=1800  # 30 minutes

# CSRF Protection
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE='Strict'
```

#### Background Tasks (Celery)
```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ACCEPT_CONTENT=['json']
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
```

## Feature Configuration

### Hospital Information
```python
# settings.py or environment variables
HOSPITAL_NAME="Chelal General Hospital"
HOSPITAL_ADDRESS="123 Hospital Street, Banjul, Gambia"
HOSPITAL_PHONE="+220 123 4567"
HOSPITAL_EMAIL="info@chelalhospital.com"
HOSPITAL_WEBSITE="https://www.chelalhospital.com"
```

### Appointment Settings
```env
# Appointment Configuration
DEFAULT_APPOINTMENT_DURATION=30  # minutes
APPOINTMENT_BUFFER_TIME=5  # minutes between appointments
MAX_ADVANCE_BOOKING_DAYS=90  # how far ahead patients can book
ENABLE_ONLINE_BOOKING=True
REQUIRE_APPOINTMENT_CONFIRMATION=True
```

### Notification Settings
```env
# Notification Configuration
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_SMS_NOTIFICATIONS=True
ENABLE_PUSH_NOTIFICATIONS=False

# Reminder Settings
APPOINTMENT_REMINDER_HOURS=24,2  # 24 hours and 2 hours before
MEDICATION_REMINDER_ENABLED=True
LAB_RESULT_NOTIFICATION_ENABLED=True
```

### Billing Configuration
```env
# Billing Settings
CURRENCY_CODE=GMD  # Gambian Dalasi
CURRENCY_SYMBOL=D
TAX_RATE=0.15  # 15% tax rate
ENABLE_INSURANCE_BILLING=True
REQUIRE_PAYMENT_AUTHORIZATION=False
```

## Role-Based Configuration

### User Roles and Permissions
```python
# Custom role configuration in settings.py
DEFAULT_ROLES = {
    'Doctor': {
        'permissions': [
            'view_patient', 'add_patient', 'change_patient',
            'view_appointment', 'add_appointment', 'change_appointment',
            'view_encounter', 'add_encounter', 'change_encounter',
            'view_prescription', 'add_prescription', 'change_prescription',
            'view_laborder', 'add_laborder', 'change_laborder',
        ],
        'description': 'Full clinical access'
    },
    'Nurse': {
        'permissions': [
            'view_patient', 'change_patient',
            'view_appointment', 'change_appointment',
            'view_encounter', 'add_encounter', 'change_encounter',
            'view_vitals', 'add_vitals', 'change_vitals',
        ],
        'description': 'Patient care and monitoring'
    },
    'Pharmacist': {
        'permissions': [
            'view_patient',
            'view_prescription', 'change_prescription',
            'view_medicationitem', 'add_medicationitem', 'change_medicationitem',
            'view_stockbatch', 'add_stockbatch', 'change_stockbatch',
        ],
        'description': 'Pharmacy operations'
    },
    'Receptionist': {
        'permissions': [
            'view_patient', 'add_patient', 'change_patient',
            'view_appointment', 'add_appointment', 'change_appointment',
            'view_bill', 'add_bill', 'change_bill',
        ],
        'description': 'Front desk operations'
    },
    'Admin': {
        'permissions': ['*'],  # All permissions
        'description': 'System administration'
    }
}
```

### Department Configuration
```python
DEPARTMENTS = [
    'Emergency Medicine',
    'Internal Medicine',
    'Pediatrics',
    'Surgery',
    'Obstetrics & Gynecology',
    'Radiology',
    'Laboratory',
    'Pharmacy',
    'Administration',
]
```

## API Configuration

### API Settings
```env
# API Configuration
API_VERSION=v1
API_RATE_LIMIT=100/hour  # per user
API_RATE_LIMIT_ANON=10/hour  # anonymous users
API_PAGE_SIZE=20
API_MAX_PAGE_SIZE=100

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://mobile-app.com
CORS_ALLOW_CREDENTIALS=True
```

### JWT Token Configuration
```python
# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

## Localization Configuration

### Multi-language Support
```python
# Internationalization settings
USE_I18N = True
USE_L10N = True

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'French'),
    ('wo', 'Wolof'),  # Local language
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Default language
LANGUAGE_CODE = 'en'
```

### Date and Time Configuration
```python
# Time zone settings
TIME_ZONE = 'Africa/Banjul'  # Gambia timezone
USE_TZ = True

# Date format settings
DATE_FORMAT = 'd/m/Y'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd/m/Y H:i'

# First day of week (0=Sunday, 1=Monday)
FIRST_DAY_OF_WEEK = 1  # Monday
```

## Integration Configuration

### External API Integrations
```env
# Laboratory Information System
LIS_ENABLED=False
LIS_API_URL=https://lab-system.com/api/
LIS_API_KEY=your_lis_api_key

# Radiology Information System
RIS_ENABLED=False
RIS_API_URL=https://radiology-system.com/api/
RIS_API_KEY=your_ris_api_key

# Health Information Exchange
HIE_ENABLED=False
HIE_API_URL=https://hie-system.com/api/
HIE_API_KEY=your_hie_api_key
```

### Payment Gateway Configuration
```env
# Payment Processing
PAYMENT_GATEWAY_ENABLED=False
PAYMENT_GATEWAY_TYPE=stripe  # stripe, paypal, local
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
```

## Logging Configuration

### Advanced Logging Setup
```python
# Comprehensive logging configuration
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
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chelal-hms/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chelal-hms/audit.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/chelal-hms/security.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## Environment-Specific Configurations

### Development Environment
```env
# Development specific settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Development database
DATABASE_URL=sqlite:///db.sqlite3

# Console email backend
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Disable security features for development
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Enable debug toolbar
ENABLE_DEBUG_TOOLBAR=True
```

### Staging Environment
```env
# Staging specific settings
DEBUG=False
ALLOWED_HOSTS=staging.chelalhospital.com

# Staging database
DATABASE_URL=postgresql://user:pass@staging-db:5432/chelal_hms_staging

# Email backend with logging
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=/tmp/app-messages

# Reduced security for testing
SECURE_SSL_REDIRECT=False
```

### Production Environment
```env
# Production settings
DEBUG=False
ALLOWED_HOSTS=chelalhospital.com,api.chelalhospital.com

# Production database with SSL
DATABASE_URL=postgresql://user:pass@prod-db:5432/chelal_hms_prod?sslmode=require

# Production email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Full security enabled
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## Performance Configuration

### Database Optimization
```python
# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require' if os.getenv('DB_SSL_REQUIRE') == 'True' else 'disable',
        },
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

### Cache Configuration
```python
# Multi-level caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'chelal_hms',
        'TIMEOUT': 300,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'chelal_sessions',
        'TIMEOUT': 1800,
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
```

## Configuration Management

### Configuration Files Structure
```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py           # Common settings
│   ├── development.py    # Development overrides
│   ├── staging.py        # Staging overrides
│   ├── production.py     # Production overrides
│   └── testing.py        # Test settings
├── environments/
│   ├── .env.development
│   ├── .env.staging
│   ├── .env.production
│   └── .env.testing
└── docker/
    ├── docker-compose.yml
    ├── docker-compose.staging.yml
    └── docker-compose.production.yml
```

### Environment Detection
```python
# settings/__init__.py
import os

environment = os.getenv('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
elif environment == 'testing':
    from .testing import *
else:
    from .development import *
```

### Configuration Validation
```python
# config/validators.py
import os
from django.core.exceptions import ImproperlyConfigured

def validate_required_settings():
    """Validate that all required settings are configured."""
    required_settings = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not os.getenv(setting):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ImproperlyConfigured(
            f"Missing required environment variables: {', '.join(missing_settings)}"
        )

# Call validation on startup
validate_required_settings()
```

---

For environment-specific deployment instructions, see the [Deployment Guide](../deployment/README.md).
For security configuration details, see the [Security Guide](../security/README.md).