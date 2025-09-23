# Frequently Asked Questions (FAQ)

Common questions and answers about the Chelal Hospital Management System.

## General Questions

### What is Chelal HMS?

Chelal Hospital Management System is a comprehensive Django REST API backend designed for managing hospital operations including patient records, appointments, medical encounters, pharmacy management, billing, and more.

### What technologies does it use?

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL 12+
- **Cache/Sessions**: Redis 6.0+
- **Authentication**: JWT (JSON Web Tokens)
- **Background Tasks**: Celery
- **Real-time**: WebSocket support with Channels
- **API Documentation**: Auto-generated with DRF

### Is it HIPAA compliant?

The system implements many HIPAA-required features including:
- Audit logging for all data access
- Role-based access control
- Data encryption at rest and in transit
- Secure authentication and authorization
- Data backup and recovery procedures

However, full HIPAA compliance depends on proper deployment, configuration, and operational procedures.

## Installation and Setup

### What are the system requirements?

**Minimum Requirements:**
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+
- 4GB RAM
- 10GB storage

**Recommended for Production:**
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- 16GB RAM
- 100GB+ SSD storage

### Can I use SQLite instead of PostgreSQL?

While Django supports SQLite, we strongly recommend PostgreSQL for production use because:
- Better concurrent access handling
- Advanced data types and features
- Better performance for complex queries
- Required for some advanced features (JSON fields, full-text search)

### Do I need Docker to run the system?

No, Docker is optional but recommended because:
- Consistent environment across development and production
- Easier dependency management
- Simplified deployment process
- Isolation from host system

You can install and run everything directly on your system.

## API and Development

### How do I authenticate with the API?

The API uses JWT authentication:

1. **Login** to get access and refresh tokens:
```bash
POST /api/auth/login/
{
    "username": "your-username",
    "password": "your-password"
}
```

2. **Use the access token** in requests:
```bash
Authorization: Bearer <access-token>
```

3. **Refresh** when the token expires:
```bash
POST /api/auth/refresh/
{
    "refresh": "your-refresh-token"
}
```

### What user roles are available?

- **Admin**: Full system access
- **Doctor**: Medical records, prescriptions, appointments
- **Nurse**: Patient care, vitals, basic records
- **Receptionist**: Appointments, patient registration
- **Pharmacist**: Pharmacy operations, dispensing
- **Lab Technician**: Lab orders and results

### How do I add a new user role?

1. Create the role in the database:
```python
role = Role.objects.create(
    name="New Role",
    description="Description of the role",
    permissions={
        "view_patient": True,
        "create_appointment": True,
        # ... other permissions
    }
)
```

2. Update permission classes in views:
```python
from core.permissions import IsNewRoleOrReadOnly
```

3. Document the new role and its permissions.

### Can I customize the API responses?

Yes, you can customize responses by:
- Modifying serializers in `core/serializers.py`
- Creating custom views in `core/views.py`
- Adding custom fields to models
- Using Django REST Framework's customization features

### How do I add a new API endpoint?

1. **Create the view** in `core/views.py`:
```python
@api_view(['GET'])
def my_custom_endpoint(request):
    # Your logic here
    return Response(data)
```

2. **Add to URLs** in `core/urls.py`:
```python
path('my-endpoint/', views.my_custom_endpoint, name='my-endpoint'),
```

3. **Add permissions** if needed
4. **Write tests** for the new endpoint
5. **Update documentation**

## Data and Models

### How do I add a new field to an existing model?

1. **Modify the model** in `core/models.py`:
```python
class Patient(models.Model):
    # existing fields...
    new_field = models.CharField(max_length=100, blank=True)
```

2. **Create migration**:
```bash
python manage.py makemigrations
```

3. **Apply migration**:
```bash
python manage.py migrate
```

4. **Update serializers** if the field should be exposed via API
5. **Update documentation**

### How do I create a backup of the database?

```bash
# Create backup
pg_dump -h localhost -U postgres chelal_hms > backup.sql

# Restore backup
psql -h localhost -U postgres chelal_hms < backup.sql

# Automated backup script
python manage.py dumpdata > data_backup.json
```

### Can I import existing patient data?

Yes, you can import data using several methods:

1. **Django fixtures**:
```bash
python manage.py loaddata your_data.json
```

2. **Custom management command**:
```python
# Create command in core/management/commands/
python manage.py import_patients --file patients.csv
```

3. **API bulk import** (if implemented)
4. **Direct database import** (requires careful mapping)

### How do I export data?

```bash
# Export all data
python manage.py dumpdata > all_data.json

# Export specific models
python manage.py dumpdata core.Patient > patients.json

# Export to CSV via API
GET /api/patients/export/?format=csv
```

## Security and Permissions

### How do I reset a user's password?

**Via Django admin:**
1. Login to `/admin/`
2. Go to Users
3. Select the user
4. Use "change password" form

**Via command line:**
```bash
python manage.py changepassword username
```

**Via API** (if implemented):
```bash
POST /api/auth/password-reset/
{
    "email": "user@example.com"
}
```

### How do I lock/unlock a user account?

```python
# Via Django shell
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='username')
user.is_active = False  # Lock account
user.save()

user.is_active = True   # Unlock account
user.save()
```

### How are audit logs stored?

Audit logs are stored in the `AuditLog` model and include:
- User who performed the action
- Action type (CREATE, UPDATE, DELETE, VIEW)
- Model and object affected
- Timestamp
- IP address and user agent
- Description of the change

Access audit logs via Django admin or custom reports.

### Can I see who accessed a patient's record?

Yes, check the audit logs:
```python
from core.models import AuditLog

# Get all access to a specific patient
logs = AuditLog.objects.filter(
    model_name='Patient',
    object_id='123'
).order_by('-timestamp')
```

## Deployment and Operations

### What hosting options do I have?

1. **Cloud Platforms**: AWS, Google Cloud, Azure, DigitalOcean
2. **VPS Providers**: Linode, Vultr, Hetzner
3. **Platform-as-a-Service**: Heroku, Railway, Render
4. **On-premises**: Your own servers
5. **Container Platforms**: Kubernetes, Docker Swarm

### How do I scale the application?

**Horizontal Scaling:**
- Multiple application servers behind a load balancer
- Database read replicas
- Redis cluster for caching
- CDN for static files

**Vertical Scaling:**
- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement caching strategies
- Use database connection pooling

### How do I monitor the application?

1. **Health Checks**: `/api/health/` endpoint
2. **Logs**: Application and system logs
3. **Metrics**: Prometheus/Grafana setup
4. **Error Tracking**: Sentry integration
5. **Database Monitoring**: PostgreSQL stats
6. **Performance**: Response time monitoring

### How do I update to a new version?

1. **Backup** database and files
2. **Test** in staging environment
3. **Pull** new code
4. **Install** new dependencies
5. **Run** database migrations
6. **Collect** static files
7. **Restart** application services
8. **Verify** deployment

### What should I backup?

1. **Database**: Full PostgreSQL dump
2. **Media Files**: Uploaded patient documents
3. **Configuration**: Environment files and settings
4. **Static Files**: If customized
5. **SSL Certificates**: If using custom certificates

## Integration and Customization

### Can I integrate with existing hospital systems?

Yes, common integration patterns include:

1. **HL7 FHIR**: Healthcare data exchange standard
2. **REST APIs**: Custom API integrations
3. **Database**: Direct database connections
4. **File-based**: CSV/JSON import/export
5. **Webhooks**: Real-time notifications

### How do I add SMS notifications?

SMS is already supported via Twilio:

1. **Configure** Twilio credentials in environment
2. **Set up** appointment reminders
3. **Use** the notification system:
```python
from core.notifications import send_sms
send_sms(phone_number, message)
```

### Can I customize the email templates?

Yes, email templates are in `templates/email/`:
- Modify existing templates
- Create new templates
- Use Django's template system
- Support for HTML and text emails

### How do I add real-time notifications?

Real-time notifications use WebSocket:

1. **Connect** to WebSocket endpoint:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/USER_ID/');
```

2. **Send** notifications from backend:
```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f"user_{user_id}",
    {
        "type": "notification.message",
        "message": "Your appointment is starting soon"
    }
)
```

## Troubleshooting

### The API returns 500 errors

1. **Check** application logs
2. **Verify** database connectivity
3. **Ensure** Redis is running
4. **Check** environment configuration
5. **Review** recent changes

### Slow API responses

1. **Check** database query performance
2. **Add** database indexes
3. **Implement** caching
4. **Optimize** serializers
5. **Use** pagination for large datasets

### Users can't login

1. **Verify** user account is active
2. **Check** password is correct
3. **Ensure** JWT configuration is correct
4. **Review** authentication backend
5. **Check** for account lockouts

### How do I get help?

1. **Documentation**: Check relevant docs sections
2. **Logs**: Review application and system logs
3. **GitHub Issues**: Search existing issues or create new one
4. **Community**: Join project discussions
5. **Support**: Contact development team

---

## Still Have Questions?

- [Installation Guide](../installation/README.md)
- [API Documentation](../api/overview.md)
- [Troubleshooting](../troubleshooting/README.md)
- [Development Guidelines](../development/guidelines.md)

Can't find your answer? [Create an issue](https://github.com/C-Jalloh/chelalBackend/issues) with your question.