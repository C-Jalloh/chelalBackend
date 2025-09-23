# Development Guidelines

This document outlines the development standards and guidelines for the Chelal Hospital Management System.

## Development Environment Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+
- Git
- Virtual environment manager

### IDE Setup

#### Visual Studio Code
Recommended extensions:
```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "ms-python.isort",
        "bradlc.vscode-tailwindcss",
        "ms-vscode.vscode-json"
    ]
}
```

#### PyCharm
Configure the following:
- Python interpreter pointing to virtual environment
- Django support enabled
- Code style set to Black
- Import optimization with isort

### Code Style and Standards

#### Python Code Style
We follow PEP 8 with some modifications:

```python
# Line length: 88 characters (Black default)
# Use Black for automatic formatting
# Use isort for import sorting
# Use flake8 for linting

# Example properly formatted code
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_phone_number


class User(AbstractUser):
    """Custom user model with additional fields."""
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[validate_phone_number],
        help_text="User's contact phone number"
    )
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
```

#### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import requests
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework import serializers

# Local application imports
from .models import Patient
from .utils import format_phone_number
```

#### Naming Conventions
- **Classes**: PascalCase (`PatientSerializer`)
- **Functions/Variables**: snake_case (`get_patient_list`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_ATTEMPTS`)
- **Private methods**: Leading underscore (`_validate_data`)

### Django Best Practices

#### Models
```python
class Patient(models.Model):
    """Patient information and demographics."""
    
    # Use descriptive field names
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique patient identifier"
    )
    
    # Always include created/modified timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_patient'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_id})"
    
    def get_absolute_url(self):
        return reverse('patient-detail', kwargs={'pk': self.pk})
```

#### Views
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class PatientViewSet(viewsets.ModelViewSet):
    """Patient management viewset."""
    
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'gender']
    search_fields = ['first_name', 'last_name', 'patient_id']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Get patient's medical history."""
        patient = self.get_object()
        encounters = patient.encounter_set.select_related('doctor')
        serializer = EncounterSerializer(encounters, many=True)
        return Response(serializer.data)
```

#### Serializers
```python
class PatientSerializer(serializers.ModelSerializer):
    """Patient serializer with validation."""
    
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'first_name', 'last_name',
            'full_name', 'age', 'date_of_birth', 'gender',
            'phone_number', 'email'
        ]
        read_only_fields = ['id', 'patient_id']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_age(self, obj):
        from datetime import date
        return (date.today() - obj.date_of_birth).days // 365
    
    def validate_phone_number(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must include country code."
            )
        return value
```

### Testing Standards

#### Test Structure
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class PatientModelTest(TestCase):
    """Test Patient model functionality."""
    
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            gender="M"
        )
    
    def test_str_representation(self):
        """Test string representation of patient."""
        expected = f"John Doe ({self.patient.patient_id})"
        self.assertEqual(str(self.patient), expected)
    
    def test_age_calculation(self):
        """Test age calculation method."""
        age = self.patient.calculate_age()
        self.assertIsInstance(age, int)
        self.assertGreater(age, 0)


class PatientAPITest(APITestCase):
    """Test Patient API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_patient(self):
        """Test patient creation via API."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1985-05-15',
            'gender': 'F'
        }
        response = self.client.post('/api/patients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
```

#### Test Coverage
- Aim for 90%+ test coverage
- Test all model methods
- Test API endpoints (CRUD operations)
- Test edge cases and error conditions
- Use factories for test data generation

### API Development

#### URL Patterns
```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'appointments', AppointmentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

#### Error Handling
```python
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses."""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data
        }
        response.data = custom_response_data
    
    return response
```

### Database Guidelines

#### Migrations
```python
# Example migration
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='patient',
            name='middle_name',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddIndex(
            model_name='patient',
            index=models.Index(fields=['last_name'], name='core_patient_last_name_idx'),
        ),
    ]
```

#### Query Optimization
```python
# Good: Use select_related for foreign keys
patients = Patient.objects.select_related('insurance').all()

# Good: Use prefetch_related for reverse foreign keys
patients = Patient.objects.prefetch_related('encounter_set').all()

# Good: Use only() for specific fields
patients = Patient.objects.only('first_name', 'last_name').all()

# Bad: N+1 queries
for patient in Patient.objects.all():
    print(patient.insurance.provider_name)  # Query for each patient
```

### Security Guidelines

#### Authentication and Authorization
```python
from rest_framework.permissions import BasePermission

class IsDoctorOrReadOnly(BasePermission):
    """Permission for doctors to modify, others read-only."""
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.role.name == 'Doctor'

class IsOwnerOrDoctor(BasePermission):
    """Permission for owners or doctors."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role.name == 'Doctor':
            return True
        return obj.created_by == request.user
```

#### Input Validation
```python
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in format: '+999999999'."
)

class PatientSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(validators=[phone_validator])
    
    def validate_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format.")
        return value.lower()
```

### Documentation Standards

#### Code Documentation
```python
def calculate_patient_age(birth_date):
    """
    Calculate patient age from birth date.
    
    Args:
        birth_date (date): Patient's date of birth
    
    Returns:
        int: Patient's age in years
    
    Raises:
        ValueError: If birth_date is in the future
    
    Example:
        >>> from datetime import date
        >>> calculate_patient_age(date(1990, 1, 1))
        34
    """
    if birth_date > date.today():
        raise ValueError("Birth date cannot be in the future")
    
    return (date.today() - birth_date).days // 365
```

#### API Documentation
Use docstrings for automatic API documentation:

```python
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patients.
    
    Provides CRUD operations for patient records including:
    - List all patients with filtering and search
    - Create new patient records
    - Retrieve, update, and delete individual patients
    - Additional actions for medical history and appointments
    """
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """
        Retrieve patient's complete medical history.
        
        Returns all encounters, prescriptions, and lab results
        for the specified patient.
        """
        pass
```

### Git Workflow

#### Branch Naming
- `feature/add-patient-search` - New features
- `bugfix/fix-appointment-validation` - Bug fixes
- `hotfix/security-patch` - Critical fixes
- `docs/update-api-guide` - Documentation updates

#### Commit Messages
```
feat: add patient search functionality

- Implement full-text search across patient fields
- Add search filters for gender and age range
- Update API documentation for search endpoints

Closes #123
```

#### Pull Request Process
1. Create feature branch from `develop`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Create pull request with detailed description
6. Request code review
7. Address review feedback
8. Merge after approval

### Performance Guidelines

#### Caching Strategy
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def dashboard_stats(request):
    """Cached dashboard statistics."""
    stats = cache.get('dashboard_stats')
    if stats is None:
        stats = calculate_dashboard_stats()
        cache.set('dashboard_stats', stats, 60 * 15)
    return JsonResponse(stats)
```

#### Database Optimization
- Use database indexes for frequently queried fields
- Implement pagination for large datasets
- Use database aggregation instead of Python loops
- Monitor query performance with Django Debug Toolbar

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No hardcoded values
- [ ] Proper error handling
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

### Development Tools

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

#### Makefile Commands
```makefile
.PHONY: test lint format install

install:
	pip install -r requirements.txt

test:
	python manage.py test

lint:
	flake8 .
	black --check .
	isort --check-only .

format:
	black .
	isort .

migrate:
	python manage.py makemigrations
	python manage.py migrate
```

## Next Steps

1. [Testing Guide](../testing/README.md) - Comprehensive testing strategies
2. [Deployment Guide](../deployment/README.md) - Production deployment
3. [API Documentation](../api/README.md) - API development guidelines