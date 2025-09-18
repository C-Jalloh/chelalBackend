# Security Documentation

This document outlines the security implementation and best practices for the Chelal Hospital Management System.

## Overview

The Chelal HMS implements comprehensive security measures to protect patient data and ensure HIPAA compliance. Security is implemented at multiple layers: application, database, network, and infrastructure.

## Authentication and Authorization

### JWT Authentication
The system uses JSON Web Tokens (JWT) for stateless authentication:

```python
# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
}
```

### Role-Based Access Control (RBAC)
Users are assigned roles with specific permissions:

#### Roles
- **Admin**: Full system access
- **Doctor**: Medical records, prescriptions, appointments
- **Nurse**: Patient care, vitals, basic records
- **Receptionist**: Appointments, patient registration
- **Pharmacist**: Pharmacy operations, dispensing
- **Lab Technician**: Lab orders and results

#### Permission System
```python
class IsDocitorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.role.name == 'Doctor'
```

### Multi-Factor Authentication (MFA)
Planned for future implementation:
- SMS-based verification
- Email-based verification
- TOTP (Time-based One-Time Password)

## Data Protection

### Encryption
#### Data at Rest
- Database encryption using PostgreSQL TDE
- File encryption for uploaded documents
- Encrypted backups

#### Data in Transit
- TLS 1.3 for all communications
- Certificate pinning for mobile apps
- Encrypted API communications

#### Application-Level Encryption
```python
from cryptography.fernet import Fernet

class EncryptedField(models.TextField):
    """Custom field for encrypting sensitive data."""
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_data(value)
    
    def to_python(self, value):
        if isinstance(value, str):
            return value
        return decrypt_data(value)
    
    def get_prep_value(self, value):
        return encrypt_data(value)
```

### Data Anonymization
For development and testing environments:
```python
def anonymize_patient_data(patient):
    """Anonymize patient data for non-production use."""
    patient.first_name = f"Patient{patient.id}"
    patient.last_name = "Anonymous"
    patient.email = f"patient{patient.id}@example.com"
    patient.phone_number = "+1234567890"
    patient.address = "123 Anonymous St"
    return patient
```

## Input Validation and Sanitization

### API Input Validation
```python
class PatientSerializer(serializers.ModelSerializer):
    def validate_phone_number(self, value):
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value
    
    def validate_email(self, value):
        if value:
            validate_email(value)
        return value.lower()
```

### SQL Injection Prevention
- Use Django ORM exclusively
- Parameterized queries for raw SQL
- Input sanitization at API layer

### XSS Prevention
- Content Security Policy headers
- Input sanitization
- Output encoding

## Session Management

### Session Security
```python
# Session settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

### Session Timeout
```python
class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                idle_time = timezone.now() - datetime.fromisoformat(last_activity)
                if idle_time > timedelta(minutes=30):
                    logout(request)
            request.session['last_activity'] = timezone.now().isoformat()
        
        return self.get_response(request)
```

## Audit Logging

### Audit Trail Implementation
```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
```

### Automatic Audit Logging
```python
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=Patient)
def log_patient_changes(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        user=get_current_user(),
        action=action,
        model_name='Patient',
        object_id=str(instance.id),
        description=f"Patient {action.lower()}d: {instance}",
        ip_address=get_client_ip(),
        user_agent=get_user_agent()
    )
```

## Network Security

### HTTPS Enforcement
```python
# Force HTTPS in production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    "https://chelalhms.com",
    "https://app.chelalhms.com",
]
CORS_ALLOW_CREDENTIALS = True
```

### Rate Limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='ALL')
@ratelimit(key='user', rate='1000/h', method='ALL')
def api_view(request):
    pass
```

## Database Security

### Connection Security
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
            'sslcert': '/path/to/client-cert.pem',
            'sslkey': '/path/to/client-key.pem',
            'sslrootcert': '/path/to/ca-cert.pem',
        },
    }
}
```

### Row-Level Security
```sql
-- Enable RLS on sensitive tables
ALTER TABLE core_patient ENABLE ROW LEVEL SECURITY;

-- Create policies for data access
CREATE POLICY patient_access_policy ON core_patient
    FOR ALL TO app_role
    USING (
        -- Users can only access patients they're authorized for
        EXISTS (
            SELECT 1 FROM core_user_authorized_patients
            WHERE user_id = current_user_id() AND patient_id = core_patient.id
        )
    );
```

## API Security

### Request Validation
```python
class APISecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Validate request size
        if request.META.get('CONTENT_LENGTH'):
            content_length = int(request.META['CONTENT_LENGTH'])
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                return HttpResponse('Request too large', status=413)
        
        # Validate content type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if not content_type.startswith('application/json'):
                return HttpResponse('Invalid content type', status=400)
        
        return self.get_response(request)
```

### API Response Security
```python
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = "default-src 'self'"
        
        return response
```

## Compliance and Standards

### HIPAA Compliance
- Minimum necessary access
- Audit trails for all data access
- Data encryption at rest and in transit
- Secure user authentication
- Regular security assessments

### Security Controls Mapping
| Control | Implementation |
|---------|----------------|
| Access Control | Role-based permissions, MFA |
| Audit and Accountability | Comprehensive audit logging |
| Configuration Management | Infrastructure as Code |
| Identification and Authentication | JWT with strong passwords |
| System and Communications Protection | TLS, encryption |
| System and Information Integrity | Input validation, monitoring |

## Incident Response

### Security Incident Classification
- **Critical**: Data breach, system compromise
- **High**: Authentication bypass, privilege escalation
- **Medium**: DoS attack, data exposure
- **Low**: Failed login attempts, minor vulnerabilities

### Response Procedures
1. **Detection**: Automated monitoring and alerting
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore systems and services
6. **Lessons Learned**: Document and improve

### Contact Information
- Security Team: security@chelalhms.com
- Incident Response: +1-XXX-XXX-XXXX
- Management Escalation: management@chelalhms.com

## Security Testing

### Automated Security Testing
```python
# Security test examples
class SecurityTestCase(TestCase):
    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        malicious_input = "'; DROP TABLE core_patient; --"
        response = self.client.get(f'/api/patients/?search={malicious_input}')
        self.assertEqual(response.status_code, 200)
        # Verify no SQL injection occurred
    
    def test_xss_protection(self):
        """Test XSS protection."""
        malicious_script = "<script>alert('xss')</script>"
        response = self.client.post('/api/patients/', {
            'first_name': malicious_script
        })
        # Verify script is escaped in response
```

### Penetration Testing
- Quarterly external penetration testing
- Annual internal security assessments
- Continuous vulnerability scanning
- Code security reviews

## Security Monitoring

### Real-time Monitoring
```python
class SecurityEventMonitor:
    @staticmethod
    def log_failed_login(username, ip_address):
        SecurityEvent.objects.create(
            event_type='FAILED_LOGIN',
            username=username,
            ip_address=ip_address,
            severity='MEDIUM'
        )
    
    @staticmethod
    def detect_brute_force(ip_address):
        failed_attempts = SecurityEvent.objects.filter(
            event_type='FAILED_LOGIN',
            ip_address=ip_address,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        if failed_attempts >= 5:
            # Block IP address
            BlockedIP.objects.create(ip_address=ip_address)
            # Send alert
            send_security_alert(f"Brute force attack from {ip_address}")
```

### Security Metrics
- Failed login attempts per hour
- Unauthorized access attempts
- Data export frequency
- Password change frequency
- Session timeout occurrences

## Security Configuration

### Environment Variables
```bash
# Security-related environment variables
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=jwt-specific-secret
ENCRYPTION_KEY=data-encryption-key
DB_SSL_CERT=/path/to/db-cert.pem
API_RATE_LIMIT=1000/hour
SESSION_TIMEOUT=30  # minutes
```

### Production Security Checklist
- [ ] SECRET_KEY is unique and secure
- [ ] DEBUG=False in production
- [ ] HTTPS enforced
- [ ] Database SSL enabled
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Security headers configured
- [ ] File upload restrictions in place
- [ ] Regular security updates applied
- [ ] Backup encryption enabled

## Security Updates and Maintenance

### Regular Security Tasks
- Weekly vulnerability scans
- Monthly security patch reviews
- Quarterly access reviews
- Annual security training
- Continuous monitoring updates

### Security Update Process
1. **Vulnerability Assessment**: Scan for new vulnerabilities
2. **Risk Analysis**: Evaluate impact and urgency
3. **Testing**: Test patches in staging environment
4. **Deployment**: Apply patches to production
5. **Verification**: Confirm patches are effective
6. **Documentation**: Update security documentation

## Contact and Resources

### Security Team
- Email: security@chelalhms.com
- Phone: +1-XXX-XXX-XXXX
- On-call: security-oncall@chelalhms.com

### External Resources
- NIST Cybersecurity Framework
- OWASP Security Guidelines
- HIPAA Security Rule
- Django Security Documentation

---

*This document is reviewed and updated quarterly or when significant security changes are made.*