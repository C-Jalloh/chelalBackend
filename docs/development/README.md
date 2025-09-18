# Development Guide - Chelal Hospital Management System

## Development Environment Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Local Development Setup

#### 1. Clone and Setup Repository
```bash
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Development Environment Variables
Create `.env` file for development:
```env
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=chelal_hms_dev
DB_USER=postgres
DB_PASSWORD=dev_password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

# Email (for development - use console backend)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Twilio (test credentials)
TWILIO_ACCOUNT_SID=test_sid
TWILIO_AUTH_TOKEN=test_token
TWILIO_PHONE_NUMBER=+1234567890
```

#### 3. Database Setup
```bash
# Create development database
createdb chelal_hms_dev

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

#### 4. Start Development Server
```bash
# Start Django development server
python manage.py runserver

# In separate terminals, start Celery services
celery -A Backend worker --loglevel=info
celery -A Backend beat --loglevel=info
```

## Project Structure

```
chelalBackend/
├── Backend/                    # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Main settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration (WebSocket)
├── core/                      # Main application
│   ├── models.py             # Database models
│   ├── views.py              # API views
│   ├── serializers.py        # DRF serializers
│   ├── urls.py               # App URL patterns
│   ├── permissions.py        # Custom permissions
│   ├── signals.py            # Django signals
│   ├── tasks.py              # Celery tasks
│   ├── consumers.py          # WebSocket consumers
│   ├── admin.py              # Django admin configuration
│   ├── tests.py              # Test cases
│   └── management/           # Custom management commands
│       └── commands/
│           └── send_appointment_reminders.py
├── docs/                     # Documentation
├── patient_documents/        # Uploaded files
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker configuration
├── Dockerfile               # Docker image definition
└── manage.py                # Django management script
```

## Development Workflow

### Branch Management

#### Main Branches
- `main`: Production-ready code
- `develop`: Integration branch for features
- `staging`: Pre-production testing

#### Feature Development
```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/patient-portal

# Work on feature...
git add .
git commit -m "feat: add patient portal endpoints"

# Push and create pull request
git push origin feature/patient-portal
```

#### Commit Message Convention
Use conventional commits format:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add patient search functionality
fix(auth): resolve JWT token expiration issue
docs(api): update authentication documentation
test(models): add patient model validation tests
```

### Code Standards

#### Python Style Guide
Follow PEP 8 with these specific guidelines:

```python
# Import order
import os
import sys
from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers

from .utils import helper_function

# Class naming
class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""
    
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'date_of_birth']

# Method naming and docstrings
def create_patient_record(patient_data):
    """
    Create a new patient record with validation.
    
    Args:
        patient_data (dict): Patient information
        
    Returns:
        Patient: Created patient instance
        
    Raises:
        ValidationError: If patient data is invalid
    """
    pass

# Constants
MAX_APPOINTMENT_DURATION = 60  # minutes
DEFAULT_PAGE_SIZE = 20
```

#### Django Best Practices

**Models:**
```python
class Patient(models.Model):
    """Patient demographic and contact information."""
    
    unique_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique patient identifier"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'core_patient'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['unique_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.unique_id})"
    
    def get_full_name(self):
        """Return patient's full name."""
        return f"{self.first_name} {self.last_name}"
```

**Views:**
```python
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient model operations.
    
    Provides standard CRUD operations plus custom actions.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['gender', 'age']
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """Get patient's appointments."""
        patient = self.get_object()
        appointments = patient.appointments.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
```

**Serializers:**
```python
class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model with validation."""
    
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'unique_id', 'first_name', 'last_name', 
                 'full_name', 'age', 'date_of_birth', 'gender']
        read_only_fields = ['id', 'full_name', 'age']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_age(self, obj):
        if obj.date_of_birth:
            today = date.today()
            return today.year - obj.date_of_birth.year
        return None
    
    def validate_unique_id(self, value):
        """Validate patient unique ID format."""
        if not value.startswith('P'):
            raise serializers.ValidationError(
                "Patient ID must start with 'P'"
            )
        return value
```

### Testing

#### Test Structure
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Patient

User = get_user_model()

class PatientModelTest(TestCase):
    """Test Patient model functionality."""
    
    def setUp(self):
        self.patient_data = {
            'unique_id': 'P001',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'Male'
        }
    
    def test_patient_creation(self):
        """Test patient creation with valid data."""
        patient = Patient.objects.create(**self.patient_data)
        self.assertEqual(patient.unique_id, 'P001')
        self.assertEqual(str(patient), 'John Doe (P001)')
    
    def test_patient_unique_id_constraint(self):
        """Test unique constraint on patient ID."""
        Patient.objects.create(**self.patient_data)
        with self.assertRaises(IntegrityError):
            Patient.objects.create(**self.patient_data)

class PatientAPITest(APITestCase):
    """Test Patient API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_patient(self):
        """Test patient creation via API."""
        data = {
            'unique_id': 'P001',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'Male'
        }
        response = self.client.post('/api/patients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
```

#### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test core.tests.PatientModelTest

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

#### Test Data Management
```python
# Use fixtures for consistent test data
# fixtures/test_data.json
[
    {
        "model": "core.role",
        "pk": 1,
        "fields": {
            "name": "Doctor",
            "description": "Medical Doctor"
        }
    }
]

# Load in tests
class PatientAPITest(APITestCase):
    fixtures = ['test_data.json']
```

### Database Migrations

#### Creating Migrations
```bash
# Create migration for model changes
python manage.py makemigrations

# Create migration with custom name
python manage.py makemigrations --name add_patient_emergency_contact

# Create empty migration for data migration
python manage.py makemigrations --empty core --name populate_patient_data
```

#### Data Migrations
```python
# Migration file for data changes
from django.db import migrations

def populate_default_roles(apps, schema_editor):
    Role = apps.get_model('core', 'Role')
    default_roles = ['Doctor', 'Nurse', 'Admin', 'Pharmacist']
    for role_name in default_roles:
        Role.objects.get_or_create(name=role_name)

def reverse_populate_roles(apps, schema_editor):
    Role = apps.get_model('core', 'Role')
    Role.objects.filter(name__in=['Doctor', 'Nurse', 'Admin', 'Pharmacist']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_default_roles, reverse_populate_roles),
    ]
```

### API Development

#### Adding New Endpoints
1. **Define Model** (if needed)
2. **Create Serializer**
3. **Implement ViewSet**
4. **Add URL Pattern**
5. **Write Tests**
6. **Update Documentation**

#### Example: Adding Patient Notes Feature
```python
# 1. Model (in models.py)
class PatientNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

# 2. Serializer (in serializers.py)
class PatientNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = PatientNote
        fields = ['id', 'content', 'author_name', 'created_at']

# 3. ViewSet (in views.py)
class PatientNoteViewSet(viewsets.ModelViewSet):
    serializer_class = PatientNoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PatientNote.objects.filter(patient_id=self.kwargs['patient_pk'])
    
    def perform_create(self, serializer):
        serializer.save(
            patient_id=self.kwargs['patient_pk'],
            author=self.request.user
        )

# 4. URL (in urls.py)
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register('patients', PatientViewSet)

patient_router = routers.NestedDefaultRouter(router, 'patients', lookup='patient')
patient_router.register('notes', PatientNoteViewSet, basename='patient-notes')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(patient_router.urls)),
]
```

### Performance Optimization

#### Database Query Optimization
```python
# Use select_related for foreign keys
patients = Patient.objects.select_related('doctor').all()

# Use prefetch_related for reverse foreign keys
patients = Patient.objects.prefetch_related('appointments').all()

# Avoid N+1 queries
class PatientSerializer(serializers.ModelSerializer):
    appointments_count = serializers.SerializerMethodField()
    
    def get_appointments_count(self, obj):
        # Use annotation in viewset instead
        return obj.appointments_count if hasattr(obj, 'appointments_count') else 0

# In viewset
class PatientViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Patient.objects.annotate(
            appointments_count=Count('appointments')
        )
```

#### Caching Strategies
```python
from django.core.cache import cache
from django.conf import settings

def get_patient_stats(patient_id):
    cache_key = f'patient_stats_{patient_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Expensive calculation
        stats = calculate_patient_statistics(patient_id)
        cache.set(cache_key, stats, timeout=3600)  # 1 hour
    
    return stats

# Cache invalidation
@receiver(post_save, sender=Appointment)
def invalidate_patient_cache(sender, instance, **kwargs):
    cache_key = f'patient_stats_{instance.patient_id}'
    cache.delete(cache_key)
```

### Debugging

#### Django Debug Toolbar (Development)
```python
# Add to INSTALLED_APPS in development
INSTALLED_APPS = [
    # ... other apps
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ... other middleware
]

# Only show in development
INTERNAL_IPS = ['127.0.0.1', 'localhost']
```

#### Logging Configuration
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
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# In views.py
import logging
logger = logging.getLogger('core')

def my_view(request):
    logger.debug('Processing request for user %s', request.user.id)
    # ... view logic
```

### Code Quality Tools

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

# Install pre-commit
pip install pre-commit
pre-commit install
```

#### Code Formatting
```bash
# Install formatting tools
pip install black isort flake8

# Format code
black .
isort .

# Check code style
flake8 .
```

### Documentation

#### Docstring Standards
```python
def create_appointment(patient_id, doctor_id, appointment_date, **kwargs):
    """
    Create a new appointment for a patient.
    
    Args:
        patient_id (int): ID of the patient
        doctor_id (int): ID of the doctor
        appointment_date (datetime): Date and time of appointment
        **kwargs: Additional appointment parameters
        
    Returns:
        Appointment: Created appointment instance
        
    Raises:
        ValidationError: If appointment data is invalid
        ConflictError: If appointment time conflicts with existing appointment
        
    Example:
        >>> appointment = create_appointment(
        ...     patient_id=1,
        ...     doctor_id=2,
        ...     appointment_date=datetime.now() + timedelta(days=1),
        ...     appointment_type='Consultation'
        ... )
        >>> appointment.id
        1
    """
    pass
```

#### API Documentation
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class PatientViewSet(viewsets.ModelViewSet):
    @extend_schema(
        description="Create a new patient record",
        request=PatientSerializer,
        responses={201: PatientSerializer},
        tags=['Patients']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='search',
                description='Search patients by name or ID',
                required=False,
                type=str
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

---

For deployment and production considerations, see the [Deployment Guide](../deployment/README.md).