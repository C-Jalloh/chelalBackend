# Development Standards - Chelal Hospital Management System

## Overview

This document establishes coding standards, best practices, and development guidelines for the Chelal HMS project to ensure code quality, maintainability, and team collaboration.

## Code Style Guidelines

### Python Style Guide

#### PEP 8 Compliance
- **Line Length**: Maximum 88 characters (Black formatter standard)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Follow PEP 8 import ordering
- **Naming**: Use descriptive names following Python conventions

#### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime, timedelta

# Third-party imports
import requests
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Local application imports
from .models import Patient, Appointment
from .utils import send_notification
from .permissions import CanViewPatients
```

#### Naming Conventions
```python
# Variables and functions: snake_case
patient_name = "John Doe"
def get_patient_appointments(patient_id):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_APPOINTMENT_DURATION = 120
DEFAULT_PAGE_SIZE = 20

# Classes: PascalCase
class PatientSerializer(serializers.ModelSerializer):
    pass

# Private methods: _leading_underscore
def _validate_appointment_time(self, time):
    pass

# Django model fields: snake_case
class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
```

### Django Best Practices

#### Model Design
```python
class Patient(models.Model):
    """
    Patient model representing hospital patients.
    
    Stores patient demographic information and medical identifiers.
    """
    
    # Use descriptive field names
    unique_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique patient identifier (e.g., P001234)"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    
    # Use choices for limited options
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Add timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_patient'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['unique_id']),
            models.Index(fields=['last_name', 'first_name']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'date_of_birth'],
                name='unique_patient_identity'
            )
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.unique_id})"
    
    def get_full_name(self):
        """Return patient's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calculate patient's age in years."""
        from django.utils import timezone
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
```

#### View Design
```python
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient model operations.
    
    Provides CRUD operations and custom actions for patient management.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, CanViewPatients]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['gender', 'created_at']
    search_fields = ['first_name', 'last_name', 'unique_id']
    ordering_fields = ['last_name', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        
        Returns:
            QuerySet: Filtered patient queryset
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Role-based filtering
        if user.role.name == 'Doctor':
            return queryset.filter(appointments__doctor=user).distinct()
        elif user.role.name == 'Nurse':
            return queryset.filter(ward__nurses=user).distinct()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        """
        Get patient's appointments.
        
        Args:
            request: HTTP request
            pk: Patient ID
            
        Returns:
            Response: Patient's appointments
        """
        patient = self.get_object()
        appointments = patient.appointments.all().order_by('-date', '-time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_reminder(self, request, pk=None):
        """
        Send appointment reminder to patient.
        
        Args:
            request: HTTP request with reminder data
            pk: Patient ID
            
        Returns:
            Response: Reminder status
        """
        patient = self.get_object()
        # Implementation here
        return Response({'status': 'reminder_sent'})
```

#### Serializer Design
```python
class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer for Patient model with validation and computed fields.
    """
    
    # Read-only computed fields
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    appointments_count = serializers.SerializerMethodField()
    
    # Custom validation fields
    confirm_email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'unique_id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'contact_info', 'email',
            'confirm_email', 'address', 'appointments_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_name', 'age', 'appointments_count']
        extra_kwargs = {
            'unique_id': {'help_text': 'Unique patient identifier'},
            'contact_info': {'help_text': 'Primary contact phone number'},
        }
    
    def get_full_name(self, obj):
        """Get patient's full name."""
        return obj.get_full_name()
    
    def get_age(self, obj):
        """Get patient's age."""
        return obj.get_age()
    
    def get_appointments_count(self, obj):
        """Get count of patient's appointments."""
        if hasattr(obj, 'appointments_count'):
            return obj.appointments_count
        return obj.appointments.count()
    
    def validate_unique_id(self, value):
        """
        Validate patient unique ID format.
        
        Args:
            value: Unique ID value
            
        Returns:
            str: Validated unique ID
            
        Raises:
            ValidationError: If ID format is invalid
        """
        if not value.startswith('P'):
            raise serializers.ValidationError(
                "Patient ID must start with 'P'"
            )
        
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Patient ID must contain only digits after 'P'"
            )
        
        return value.upper()
    
    def validate(self, attrs):
        """
        Validate serializer data.
        
        Args:
            attrs: Serializer attributes
            
        Returns:
            dict: Validated attributes
            
        Raises:
            ValidationError: If validation fails
        """
        # Email confirmation validation
        if attrs.get('email') and attrs.get('confirm_email'):
            if attrs['email'] != attrs['confirm_email']:
                raise serializers.ValidationError(
                    "Email addresses do not match"
                )
        
        # Remove confirm_email from validated data
        attrs.pop('confirm_email', None)
        
        return attrs
```

## Testing Standards

### Test Organization
```python
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, Mock

from .models import Patient, Appointment
from .serializers import PatientSerializer

User = get_user_model()

class PatientModelTest(TestCase):
    """Test Patient model functionality."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods."""
        cls.patient_data = {
            'unique_id': 'P001',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'contact_info': '+2207834351',
        }
    
    def setUp(self):
        """Set up test environment for each test method."""
        self.patient = Patient.objects.create(**self.patient_data)
    
    def test_patient_creation(self):
        """Test patient creation with valid data."""
        self.assertEqual(self.patient.unique_id, 'P001')
        self.assertEqual(self.patient.get_full_name(), 'John Doe')
        self.assertIsInstance(self.patient.get_age(), int)
    
    def test_patient_str_representation(self):
        """Test patient string representation."""
        expected = 'John Doe (P001)'
        self.assertEqual(str(self.patient), expected)
    
    def test_unique_id_constraint(self):
        """Test unique constraint on patient ID."""
        with self.assertRaises(IntegrityError):
            Patient.objects.create(**self.patient_data)
    
    def test_age_calculation(self):
        """Test age calculation accuracy."""
        # Test with known date of birth
        from datetime import date
        patient = Patient.objects.create(
            unique_id='P002',
            first_name='Jane',
            last_name='Smith',
            date_of_birth=date(1995, 6, 15),
            gender='F'
        )
        
        # Age should be calculated correctly
        self.assertGreaterEqual(patient.get_age(), 25)

class PatientAPITest(APITestCase):
    """Test Patient API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role=Role.objects.create(name='Doctor')
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test patient
        self.patient = Patient.objects.create(
            unique_id='P001',
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='M'
        )
    
    def test_list_patients(self):
        """Test patient list endpoint."""
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_patient(self):
        """Test patient creation via API."""
        data = {
            'unique_id': 'P002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': '1995-06-15',
            'gender': 'F',
            'contact_info': '+2207834352'
        }
        response = self.client.post('/api/patients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 2)
    
    def test_patient_detail(self):
        """Test patient detail endpoint."""
        response = self.client.get(f'/api/patients/{self.patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unique_id'], 'P001')
    
    def test_patient_update(self):
        """Test patient update."""
        data = {'first_name': 'Jonathan'}
        response = self.client.patch(f'/api/patients/{self.patient.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.first_name, 'Jonathan')
    
    def test_unauthorized_access(self):
        """Test unauthorized access prevention."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @patch('core.tasks.send_sms_notification')
    def test_send_reminder_with_mock(self, mock_send_sms):
        """Test appointment reminder with mocked SMS service."""
        mock_send_sms.return_value = True
        
        response = self.client.post(f'/api/patients/{self.patient.id}/send_reminder/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_sms.assert_called_once()

class PatientSerializerTest(TestCase):
    """Test Patient serializer."""
    
    def setUp(self):
        """Set up test environment."""
        self.patient_data = {
            'unique_id': 'P001',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'M'
        }
    
    def test_valid_serialization(self):
        """Test serialization with valid data."""
        serializer = PatientSerializer(data=self.patient_data)
        self.assertTrue(serializer.is_valid())
    
    def test_invalid_unique_id(self):
        """Test validation with invalid unique ID."""
        data = self.patient_data.copy()
        data['unique_id'] = 'invalid_id'
        
        serializer = PatientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('unique_id', serializer.errors)
    
    def test_computed_fields(self):
        """Test computed fields in serializer."""
        patient = Patient.objects.create(**self.patient_data)
        serializer = PatientSerializer(patient)
        
        self.assertIn('full_name', serializer.data)
        self.assertIn('age', serializer.data)
        self.assertEqual(serializer.data['full_name'], 'John Doe')
```

### Test Coverage Requirements
- **Minimum Coverage**: 90% line coverage
- **Model Tests**: All model methods and properties
- **View Tests**: All endpoints and actions
- **Serializer Tests**: All validation logic
- **Integration Tests**: Critical user workflows

## Documentation Standards

### Docstring Format
```python
def create_appointment(patient_id, doctor_id, appointment_date, **kwargs):
    """
    Create a new appointment for a patient.
    
    This function creates an appointment after validating the patient and doctor
    availability. It also checks for scheduling conflicts and business rules.
    
    Args:
        patient_id (int): The ID of the patient
        doctor_id (int): The ID of the doctor
        appointment_date (datetime): The date and time for the appointment
        **kwargs: Additional appointment parameters
            - appointment_type (str): Type of appointment (default: 'Consultation')
            - duration (int): Duration in minutes (default: 30)
            - notes (str): Additional notes
    
    Returns:
        Appointment: The created appointment instance
    
    Raises:
        ValidationError: If the appointment data is invalid
        ConflictError: If there's a scheduling conflict
        PermissionDenied: If the user lacks permission
    
    Example:
        >>> appointment = create_appointment(
        ...     patient_id=1,
        ...     doctor_id=2,
        ...     appointment_date=datetime(2024, 10, 15, 10, 0),
        ...     appointment_type='Follow-up'
        ... )
        >>> appointment.id
        1
    
    Note:
        This function sends an automatic confirmation email to the patient
        if EMAIL_NOTIFICATIONS is enabled in settings.
    """
    pass
```

### Code Comments
```python
class AppointmentViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        # Validate appointment time is in the future
        appointment_datetime = datetime.combine(
            request.data['date'], 
            request.data['time']
        )
        if appointment_datetime <= timezone.now():
            return Response(
                {'error': 'Appointment must be in the future'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check doctor availability
        doctor_id = request.data['doctor']
        existing_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            date=request.data['date'],
            time=request.data['time'],
            status__in=['Scheduled', 'Confirmed']
        )
        
        if existing_appointments.exists():
            return Response(
                {'error': 'Doctor is not available at this time'},
                status=status.HTTP_409_CONFLICT
            )
        
        return super().create(request, *args, **kwargs)
```

## Git Workflow Standards

### Branch Naming
```bash
# Feature branches
feature/patient-search-enhancement
feature/sms-notifications

# Bug fixes
bugfix/appointment-timezone-issue
bugfix/payment-calculation-error

# Hotfixes
hotfix/security-patch-jwt
hotfix/critical-data-loss

# Release branches
release/v1.2.0
release/v1.2.1
```

### Commit Message Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```bash
feat(api): add patient search by phone number
fix(billing): correct tax calculation for insurance claims
docs(api): update authentication endpoint documentation
test(models): add comprehensive patient model tests
refactor(views): simplify appointment creation logic
```

### Pull Request Template
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Code coverage maintained/improved

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is properly commented
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests added/updated for changes

## Related Issues
Closes #123
Related to #456

## Screenshots (if applicable)
Add screenshots for UI changes.

## Additional Notes
Any additional information for reviewers.
```

## Security Standards

### Input Validation
```python
# Always validate and sanitize user input
def validate_phone_number(phone):
    """Validate and normalize phone number."""
    import re
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Validate format
    if not re.match(r'^\+?[\d]{10,15}$', cleaned):
        raise ValidationError('Invalid phone number format')
    
    return cleaned

# Use Django's built-in validation
class PatientForm(forms.ModelForm):
    def clean_contact_info(self):
        contact_info = self.cleaned_data.get('contact_info')
        return validate_phone_number(contact_info)
```

### SQL Injection Prevention
```python
# Good: Use Django ORM
patients = Patient.objects.filter(last_name__icontains=search_term)

# Good: Use parameterized queries if raw SQL is necessary
cursor.execute(
    "SELECT * FROM core_patient WHERE last_name ILIKE %s",
    [f'%{search_term}%']
)

# Bad: Never do this
cursor.execute(f"SELECT * FROM core_patient WHERE last_name ILIKE '%{search_term}%'")
```

### Authentication & Authorization
```python
# Always check permissions
class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanViewPatients]
    
    def get_queryset(self):
        # Filter based on user permissions
        user = self.request.user
        if user.role.name == 'Doctor':
            return Patient.objects.filter(appointments__doctor=user).distinct()
        return super().get_queryset()
```

## Performance Standards

### Database Queries
```python
# Good: Use select_related for foreign keys
patients = Patient.objects.select_related('created_by').all()

# Good: Use prefetch_related for reverse foreign keys
patients = Patient.objects.prefetch_related('appointments').all()

# Good: Use annotations for aggregations
patients = Patient.objects.annotate(
    appointment_count=Count('appointments')
)

# Bad: N+1 queries
for patient in patients:
    print(patient.appointments.count())  # Database hit for each patient
```

### Caching
```python
from django.core.cache import cache

def get_patient_stats(patient_id):
    """Get patient statistics with caching."""
    cache_key = f'patient_stats_{patient_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Expensive calculation
        stats = calculate_patient_statistics(patient_id)
        cache.set(cache_key, stats, timeout=3600)  # 1 hour
    
    return stats
```

## Quality Assurance

### Code Review Checklist

#### Functionality
- [ ] Code works as intended
- [ ] Edge cases handled
- [ ] Error conditions handled gracefully
- [ ] Business logic is correct

#### Code Quality
- [ ] Code is readable and maintainable
- [ ] Functions/classes have single responsibility
- [ ] No code duplication
- [ ] Appropriate abstractions used

#### Testing
- [ ] Unit tests cover new/changed code
- [ ] Tests are meaningful and comprehensive
- [ ] Integration tests for new features
- [ ] Manual testing completed

#### Security
- [ ] Input validation implemented
- [ ] Authorization checks in place
- [ ] No sensitive data exposed
- [ ] SQL injection prevention

#### Performance
- [ ] No obvious performance issues
- [ ] Database queries optimized
- [ ] Appropriate caching used
- [ ] Memory usage reasonable

### Continuous Integration

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.942
    hooks:
      - id: mypy
        additional_dependencies: [django-stubs]
```

#### CI Pipeline
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run linting
      run: |
        flake8 .
        black --check .
        isort --check-only .
    
    - name: Run tests
      run: |
        python manage.py test
        
    - name: Run security checks
      run: |
        bandit -r . -f json
        safety check
```

---

Following these standards ensures code quality, maintainability, and team productivity across the Chelal HMS project.