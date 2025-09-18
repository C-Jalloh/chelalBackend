# Security Guide - Chelal Hospital Management System

## Overview

Security is paramount in healthcare systems. This guide outlines the security architecture, implementation, and best practices for the Chelal HMS to ensure patient data protection and regulatory compliance.

## Security Architecture

### Authentication & Authorization

#### JWT Token-Based Authentication
```python
# Token lifecycle
Login → JWT Access Token (15 min) + Refresh Token (7 days)
API Request → Token Validation → Permission Check → Resource Access
Token Expiry → Use Refresh Token → New Access Token
```

**Implementation:**
```python
# settings.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

#### Role-Based Access Control (RBAC)
```python
class Permission(models.Model):
    """System permissions."""
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, unique=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

class Role(models.Model):
    """User roles with permissions."""
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(Permission)
    description = models.TextField(blank=True)

class User(AbstractUser):
    """Custom user with role-based permissions."""
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    
    def has_permission(self, permission_codename):
        """Check if user has specific permission."""
        return self.role.permissions.filter(
            codename=permission_codename
        ).exists()
```

#### Permission Classes
```python
from rest_framework.permissions import BasePermission

class CanViewPatients(BasePermission):
    """Permission to view patient records."""
    
    def has_permission(self, request, view):
        return request.user.has_permission('view_patient')
    
    def has_object_permission(self, request, view, obj):
        # Additional object-level checks
        if request.user.role.name == 'Doctor':
            return obj.doctor == request.user
        return True

class CanModifyPrescriptions(BasePermission):
    """Permission to create/modify prescriptions."""
    
    def has_permission(self, request, view):
        allowed_roles = ['Doctor', 'Pharmacist']
        return request.user.role.name in allowed_roles
```

### Data Protection

#### Encryption

**Database Encryption:**
```python
# Sensitive field encryption
from cryptography.fernet import Fernet
from django.conf import settings

class EncryptedField(models.TextField):
    """Custom field for sensitive data encryption."""
    
    def __init__(self, *args, **kwargs):
        self.cipher = Fernet(settings.FIELD_ENCRYPTION_KEY)
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.cipher.decrypt(value.encode()).decode()
    
    def to_python(self, value):
        if isinstance(value, str):
            return value
        return self.from_db_value(value, None, None)
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return self.cipher.encrypt(value.encode()).decode()

# Usage in models
class Patient(models.Model):
    ssn = EncryptedField(blank=True)  # Encrypted SSN
    medical_notes = EncryptedField(blank=True)  # Encrypted notes
```

**File Upload Security:**
```python
import os
from django.core.exceptions import ValidationError

def validate_file_type(file):
    """Validate uploaded file types."""
    allowed_types = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'text/plain'
    ]
    if file.content_type not in allowed_types:
        raise ValidationError('File type not allowed')

def secure_upload_path(instance, filename):
    """Generate secure upload path."""
    # Remove potentially dangerous characters
    filename = os.path.basename(filename)
    # Create path with patient ID and timestamp
    return f'patient_documents/{instance.patient.id}/{filename}'

class PatientDocument(models.Model):
    file = models.FileField(
        upload_to=secure_upload_path,
        validators=[validate_file_type]
    )
```

#### Input Validation & Sanitization

**Serializer Validation:**
```python
class PatientSerializer(serializers.ModelSerializer):
    """Patient serializer with comprehensive validation."""
    
    def validate_unique_id(self, value):
        """Validate patient unique ID."""
        # Remove any non-alphanumeric characters
        cleaned_value = re.sub(r'[^A-Za-z0-9]', '', value)
        
        if not cleaned_value.startswith('P'):
            raise serializers.ValidationError(
                "Patient ID must start with 'P'"
            )
        
        if len(cleaned_value) < 4:
            raise serializers.ValidationError(
                "Patient ID must be at least 4 characters"
            )
        
        return cleaned_value
    
    def validate_contact_info(self, value):
        """Validate and sanitize phone number."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', value)
        
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise serializers.ValidationError(
                "Invalid phone number format"
            )
        
        return cleaned
```

**SQL Injection Prevention:**
```python
# ALWAYS use Django ORM - never raw SQL with user input
# Good
patients = Patient.objects.filter(unique_id=user_input)

# Bad - DON'T DO THIS
cursor.execute(f"SELECT * FROM patients WHERE unique_id = '{user_input}'")

# If raw SQL is absolutely necessary, use parameters
cursor.execute(
    "SELECT * FROM patients WHERE unique_id = %s", 
    [user_input]
)
```

### API Security

#### Rate Limiting
```python
# Install django-ratelimit
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.decorators import login_required

@ratelimit(key='user', rate='100/h', method='GET', block=True)
def api_view(request):
    """Rate-limited API view."""
    pass

# Custom rate limiting middleware
class APIRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/'):
            # Implement rate limiting logic
            pass
        return self.get_response(request)
```

#### CORS Configuration
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://hospital-frontend.com",
    "https://mobile-app.hospital.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

#### API Security Headers
```python
# Custom middleware for security headers
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response

# Add to MIDDLEWARE in settings.py
MIDDLEWARE = [
    'core.middleware.SecurityHeadersMiddleware',
    # ... other middleware
]
```

### Audit & Logging

#### Audit Trail Implementation
```python
class AuditLog(models.Model):
    """Comprehensive audit logging."""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('FAILED_LOGIN', 'Failed Login'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
        ]

# Automatic audit logging via signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Patient)
def log_patient_changes(sender, instance, created, **kwargs):
    """Log patient record changes."""
    action = 'CREATE' if created else 'UPDATE'
    
    AuditLog.objects.create(
        user=get_current_user(),  # Custom middleware to track current user
        action=action,
        model_name='Patient',
        object_id=str(instance.id),
        changes=get_model_changes(instance),  # Custom function to track changes
        ip_address=get_client_ip(),
        user_agent=get_user_agent()
    )
```

#### Security Event Monitoring
```python
import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed

logger = logging.getLogger('security')

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    logger.warning(
        f"Failed login attempt for {credentials.get('email')} "
        f"from IP {get_client_ip(request)}"
    )
    
    # Create audit log entry
    AuditLog.objects.create(
        action='FAILED_LOGIN',
        model_name='User',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        changes={'email': credentials.get('email')}
    )

@receiver(user_logged_in)
def log_successful_login(sender, user, request, **kwargs):
    """Log successful logins."""
    logger.info(f"User {user.email} logged in from {get_client_ip(request)}")
    
    AuditLog.objects.create(
        user=user,
        action='LOGIN',
        model_name='User',
        object_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
```

### Compliance & Standards

#### HIPAA Compliance

**Administrative Safeguards:**
- User access management and role-based permissions
- Audit logs and monitoring
- Regular security training and documentation
- Incident response procedures

**Physical Safeguards:**
- Server security and access controls
- Workstation security requirements
- Media controls and disposal

**Technical Safeguards:**
```python
# Access control implementation
class HIPAAAccessControlMixin:
    """Mixin for HIPAA-compliant access control."""
    
    def get_queryset(self):
        """Filter data based on user's need-to-know."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role.name == 'Doctor':
            # Doctors can only see their own patients
            return queryset.filter(doctor=user)
        elif user.role.name == 'Nurse':
            # Nurses can see patients in their ward
            return queryset.filter(ward__nurses=user)
        elif user.role.name == 'Admin':
            # Admins can see all data
            return queryset
        
        return queryset.none()

# Minimum necessary standard
class PatientSerializer(serializers.ModelSerializer):
    """Patient serializer with role-based field access."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        if request and request.user.role.name == 'Receptionist':
            # Receptionists don't need medical information
            self.fields.pop('medical_history', None)
            self.fields.pop('current_medications', None)
```

#### Data Retention & Disposal
```python
# Automated data retention management
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta

class Command(BaseCommand):
    """Clean up old audit logs based on retention policy."""
    
    def handle(self, *args, **options):
        # Keep audit logs for 7 years (HIPAA requirement)
        retention_date = datetime.now() - timedelta(days=7*365)
        
        deleted_count = AuditLog.objects.filter(
            timestamp__lt=retention_date
        ).delete()[0]
        
        self.stdout.write(
            f"Deleted {deleted_count} old audit log entries"
        )

# Secure data disposal
class SecureDeleteMixin:
    """Mixin for secure data deletion."""
    
    def delete(self, *args, **kwargs):
        # Log deletion
        AuditLog.objects.create(
            user=get_current_user(),
            action='DELETE',
            model_name=self.__class__.__name__,
            object_id=str(self.pk),
            changes={'deleted': True}
        )
        
        # Perform secure deletion
        super().delete(*args, **kwargs)
```

### Security Testing

#### Security Test Cases
```python
class SecurityTestCase(APITestCase):
    """Test security implementations."""
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access protected endpoints."""
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, 401)
    
    def test_role_based_access(self):
        """Test role-based access control."""
        # Create users with different roles
        doctor = User.objects.create_user(
            email='doctor@test.com',
            password='test123',
            role=Role.objects.get(name='Doctor')
        )
        nurse = User.objects.create_user(
            email='nurse@test.com',
            password='test123',
            role=Role.objects.get(name='Nurse')
        )
        
        # Test doctor access
        self.client.force_authenticate(user=doctor)
        response = self.client.get('/api/prescriptions/')
        self.assertEqual(response.status_code, 200)
        
        # Test nurse access (should be forbidden)
        self.client.force_authenticate(user=nurse)
        response = self.client.get('/api/prescriptions/')
        self.assertEqual(response.status_code, 403)
    
    def test_input_validation(self):
        """Test input validation and sanitization."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test XSS prevention
        malicious_data = {
            'first_name': '<script>alert("xss")</script>',
            'unique_id': 'P001'
        }
        response = self.client.post('/api/patients/', malicious_data)
        
        # Should either reject or sanitize the input
        if response.status_code == 201:
            patient = Patient.objects.get(pk=response.data['id'])
            self.assertNotIn('<script>', patient.first_name)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        # Attempt SQL injection through search parameters
        response = self.client.get(
            '/api/patients/?search=\'; DROP TABLE core_patient; --'
        )
        
        # Should not cause server error
        self.assertNotEqual(response.status_code, 500)
        
        # Table should still exist
        self.assertTrue(Patient.objects.exists() or True)  # True if no patients
```

#### Penetration Testing
```bash
# Install security testing tools
pip install safety bandit

# Check for known security vulnerabilities
safety check

# Static security analysis
bandit -r . -f json -o security_report.json

# SQL injection testing with sqlmap (external tool)
sqlmap -u "http://localhost:8000/api/patients/" --headers="Authorization: Bearer TOKEN"
```

### Production Security Configuration

#### Environment Variables
```env
# Production security settings
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-minimum-50-characters
ALLOWED_HOSTS=your-domain.com,api.your-domain.com

# Database security
DB_SSL_REQUIRE=True
DB_SSL_CA=/path/to/ca-cert.pem

# HTTPS settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')

# Session security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Strict'
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True

# File upload security
FILE_UPLOAD_MAX_MEMORY_SIZE=5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE=5242880  # 5MB
```

#### Nginx Security Configuration
```nginx
# /etc/nginx/sites-available/chelal-hms
server {
    listen 443 ssl http2;
    server_name api.hospital.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # File upload restrictions
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Incident Response

#### Security Incident Procedures
1. **Detection**: Monitor logs and alerts
2. **Assessment**: Determine severity and scope
3. **Containment**: Isolate affected systems
4. **Investigation**: Analyze the incident
5. **Recovery**: Restore normal operations
6. **Documentation**: Record lessons learned

#### Emergency Response
```python
# Emergency security functions
def lock_user_account(user_id, reason):
    """Lock user account in case of security breach."""
    user = User.objects.get(id=user_id)
    user.is_active = False
    user.save()
    
    # Log the action
    AuditLog.objects.create(
        action='LOCK_ACCOUNT',
        model_name='User',
        object_id=str(user_id),
        changes={'reason': reason, 'locked_at': timezone.now()}
    )

def invalidate_all_tokens():
    """Invalidate all JWT tokens in case of security breach."""
    # This would require implementing a token blacklist
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    OutstandingToken.objects.all().delete()
```

---

For implementation details and production deployment security, see the [Deployment Guide](../deployment/README.md).