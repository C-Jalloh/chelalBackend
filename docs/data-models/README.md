# Data Models - Chelal Hospital Management System

## Overview

The Chelal HMS data model is designed to comprehensively manage all aspects of hospital operations, from patient care to administrative functions. This document provides detailed information about the database schema, relationships, and data management procedures.

## Database Schema Architecture

### Entity Relationship Overview

```
                    ┌─────────────────┐
                    │      User       │
                    │   (Staff)       │
                    └─────────┬───────┘
                              │
                              │ role
                              ▼
                    ┌─────────────────┐     ┌─────────────────┐
                    │      Role       │     │    Patient      │
                    │                 │     │                 │
                    └─────────────────┘     └─────────┬───────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                              ▼                       ▼                       ▼
                    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                    │  Appointment    │     │   Encounter     │     │  Medical        │
                    │                 │     │                 │     │  Conditions     │
                    └─────────────────┘     └─────────┬───────┘     └─────────────────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                              ▼                       ▼                       ▼
                    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                    │ Prescription    │     │     Vitals      │     │   Lab Order     │
                    │                 │     │                 │     │                 │
                    └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Core Models

### User Management

#### User Model
**Purpose**: Central user management for all system users (doctors, nurses, administrators, etc.)

```python
class User(AbstractUser):
    """Extended user model with hospital-specific fields."""
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.ForeignKey('Role', on_delete=models.PROTECT)
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Fields:**
- `email`: Primary identifier for login
- `role`: Links to Role model for permissions
- `employee_id`: Hospital staff identifier
- `license_number`: Professional license (for doctors, nurses)

#### Role Model
**Purpose**: Define user roles and permissions within the system

```python
class Role(models.Model):
    """User roles and permissions."""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField('auth.Permission', blank=True)
    is_active = models.BooleanField(default=True)
```

**Standard Roles:**
- **Doctor**: Clinical care, prescriptions, encounters
- **Nurse**: Patient care, vitals, medication administration
- **Pharmacist**: Medication management, dispensing
- **Receptionist**: Patient registration, appointments
- **Admin**: System administration, user management
- **Lab Technician**: Laboratory orders and results

### Patient Management

#### Patient Model
**Purpose**: Store patient demographic and contact information

```python
class Patient(models.Model):
    """Patient demographic and contact information."""
    
    unique_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    contact_info = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    known_allergies = models.TextField(blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Features:**
- Unique patient identifier system
- Comprehensive contact information
- Emergency contact details
- Medical alert information (allergies, blood type)
- Insurance information linking

#### Medical Condition Model
**Purpose**: Track patient's chronic conditions and medical history

```python
class MedicalCondition(models.Model):
    """Patient chronic conditions and medical history."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_conditions')
    name = models.CharField(max_length=255)
    icd_code = models.CharField(max_length=20, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    notes = models.TextField(blank=True)
    diagnosed_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Appointment Management

#### Appointment Model
**Purpose**: Schedule and manage patient appointments

```python
class Appointment(models.Model):
    """Patient appointment scheduling."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    date = models.DateField()
    time = models.TimeField()
    appointment_type = models.CharField(max_length=50, choices=APPOINTMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    duration = models.PositiveIntegerField(default=30)  # minutes
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Status Choices:**
- `Scheduled`: Initial appointment booking
- `Confirmed`: Patient confirmed attendance
- `In Progress`: Currently seeing patient
- `Completed`: Appointment finished
- `Cancelled`: Appointment cancelled
- `No Show`: Patient didn't attend

### Clinical Management

#### Encounter Model
**Purpose**: Record clinical encounters and visits

```python
class Encounter(models.Model):
    """Clinical encounter or visit."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_encounters')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    encounter_type = models.CharField(max_length=50, choices=ENCOUNTER_TYPE_CHOICES)
    chief_complaint = models.TextField()
    history_present_illness = models.TextField(blank=True)
    physical_examination = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ENCOUNTER_STATUS_CHOICES, default='Active')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
```

#### Vitals Model
**Purpose**: Record patient vital signs

```python
class Vitals(models.Model):
    """Patient vital signs."""
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='vitals')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    recorded_at = models.DateTimeField(auto_now_add=True)
```

#### Prescription Model
**Purpose**: Manage medication prescriptions

```python
class Prescription(models.Model):
    """Medication prescriptions."""
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PRESCRIPTION_STATUS_CHOICES, default='Active')
    prescribed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    prescribed_at = models.DateTimeField(auto_now_add=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_prescriptions')
```

### Laboratory Management

#### Lab Order Model
**Purpose**: Manage laboratory test orders

```python
class LabOrder(models.Model):
    """Laboratory test orders."""
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='lab_orders')
    order_number = models.CharField(max_length=20, unique=True)
    test_name = models.CharField(max_length=255)
    specimen_type = models.CharField(max_length=100, blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='Routine')
    status = models.CharField(max_length=20, choices=LAB_STATUS_CHOICES, default='Ordered')
    ordered_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordered_labs')
    ordered_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_labs')
```

#### Lab Test Catalog Model
**Purpose**: Catalog of available laboratory tests

```python
class LabTestCatalog(models.Model):
    """Catalog of available laboratory tests."""
    
    test_name = models.CharField(max_length=255, unique=True)
    test_code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=100)
    specimen_type = models.CharField(max_length=100)
    normal_range = models.CharField(max_length=200, blank=True)
    units = models.CharField(max_length=50, blank=True)
    turnaround_time = models.PositiveIntegerField()  # hours
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
```

### Pharmacy Management

#### Medication Item Model
**Purpose**: Master catalog of medications

```python
class MedicationItem(models.Model):
    """Medication master catalog."""
    
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    strength = models.CharField(max_length=100)
    dosage_form = models.CharField(max_length=100)
    category = models.ForeignKey('MedicationCategory', on_delete=models.CASCADE)
    manufacturer = models.CharField(max_length=255, blank=True)
    ndc_number = models.CharField(max_length=20, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

#### Stock Batch Model
**Purpose**: Track medication inventory batches

```python
class StockBatch(models.Model):
    """Medication stock batch tracking."""
    
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.CASCADE, related_name='stock_batches')
    batch_number = models.CharField(max_length=100)
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    quantity_received = models.PositiveIntegerField()
    quantity_available = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    received_date = models.DateField(auto_now_add=True)
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
    
    @property
    def days_to_expiry(self):
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days
```

### Billing Management

#### Service Catalog Model
**Purpose**: Define billable services and procedures

```python
class ServiceCatalog(models.Model):
    """Catalog of billable services and procedures."""
    
    service_name = models.CharField(max_length=255)
    service_code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_unit = models.CharField(max_length=50, default='Each')
    cpt_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    requires_authorization = models.BooleanField(default=False)
```

#### Bill Model
**Purpose**: Patient billing and invoicing

```python
class Bill(models.Model):
    """Patient bills and invoices."""
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='bills', null=True, blank=True)
    bill_number = models.CharField(max_length=20, unique=True)
    bill_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=BILL_STATUS_CHOICES, default='Pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
```

#### Payment Model
**Purpose**: Track payments and financial transactions

```python
class Payment(models.Model):
    """Payment transactions."""
    
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_date = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Data Relationships

### Key Foreign Key Relationships

1. **User → Role**: Many-to-One (Users have one role)
2. **Patient → Appointment**: One-to-Many (Patient can have multiple appointments)
3. **Appointment → Encounter**: One-to-One (Each appointment can result in one encounter)
4. **Encounter → Prescription**: One-to-Many (Encounter can have multiple prescriptions)
5. **Encounter → Vitals**: One-to-Many (Multiple vital readings per encounter)
6. **Encounter → LabOrder**: One-to-Many (Multiple lab orders per encounter)

### Data Integrity Constraints

```sql
-- Example database constraints
ALTER TABLE core_patient ADD CONSTRAINT unique_patient_id UNIQUE (unique_id);
ALTER TABLE core_appointment ADD CONSTRAINT no_double_booking 
    UNIQUE (doctor_id, date, time);
ALTER TABLE core_user ADD CONSTRAINT unique_employee_id UNIQUE (employee_id);

-- Check constraints
ALTER TABLE core_vitals ADD CONSTRAINT valid_temperature 
    CHECK (temperature >= 90 AND temperature <= 110);
ALTER TABLE core_vitals ADD CONSTRAINT valid_blood_pressure 
    CHECK (blood_pressure_systolic >= 60 AND blood_pressure_systolic <= 300);
```

## Database Indexing Strategy

### Performance Indexes

```sql
-- Patient lookup indexes
CREATE INDEX idx_patient_unique_id ON core_patient(unique_id);
CREATE INDEX idx_patient_name ON core_patient(last_name, first_name);
CREATE INDEX idx_patient_contact ON core_patient(contact_info);

-- Appointment scheduling indexes
CREATE INDEX idx_appointment_date_time ON core_appointment(date, time);
CREATE INDEX idx_appointment_doctor_date ON core_appointment(doctor_id, date);
CREATE INDEX idx_appointment_patient ON core_appointment(patient_id);

-- Clinical data indexes
CREATE INDEX idx_encounter_patient ON core_encounter(patient_id);
CREATE INDEX idx_encounter_date ON core_encounter(start_time);
CREATE INDEX idx_prescription_encounter ON core_prescription(encounter_id);

-- Laboratory indexes
CREATE INDEX idx_lab_order_encounter ON core_laborder(encounter_id);
CREATE INDEX idx_lab_order_status ON core_laborder(status);
CREATE INDEX idx_lab_order_date ON core_laborder(ordered_at);

-- Billing indexes
CREATE INDEX idx_bill_patient ON core_bill(patient_id);
CREATE INDEX idx_bill_date ON core_bill(bill_date);
CREATE INDEX idx_bill_status ON core_bill(status);

-- Audit log indexes
CREATE INDEX idx_audit_user_timestamp ON core_auditlog(user_id, timestamp);
CREATE INDEX idx_audit_model_object ON core_auditlog(model_name, object_id);
```

### Composite Indexes for Complex Queries

```sql
-- Multi-column indexes for common query patterns
CREATE INDEX idx_appointment_doctor_date_status ON core_appointment(doctor_id, date, status);
CREATE INDEX idx_stock_batch_med_expiry ON core_stockbatch(medication_item_id, expiry_date);
CREATE INDEX idx_encounter_patient_date ON core_encounter(patient_id, start_time);
```

## Data Validation Rules

### Model-Level Validation

```python
from django.core.exceptions import ValidationError
from django.utils import timezone

class Patient(models.Model):
    # ... fields ...
    
    def clean(self):
        """Custom validation for patient data."""
        # Validate date of birth
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError('Date of birth cannot be in the future')
        
        # Validate age (must be reasonable)
        if self.date_of_birth:
            age = (timezone.now().date() - self.date_of_birth).days / 365.25
            if age > 150:
                raise ValidationError('Age cannot exceed 150 years')
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)

class Appointment(models.Model):
    # ... fields ...
    
    def clean(self):
        """Validate appointment data."""
        # Check for double booking
        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
            time=self.time
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            raise ValidationError('Doctor already has an appointment at this time')
        
        # Validate appointment is in the future
        appointment_datetime = timezone.datetime.combine(self.date, self.time)
        if appointment_datetime <= timezone.now():
            raise ValidationError('Appointment must be in the future')
```

### Database-Level Constraints

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['doctor', 'date', 'time'],
            name='unique_doctor_appointment'
        ),
        models.CheckConstraint(
            check=models.Q(amount_paid__lte=models.F('total_amount')),
            name='payment_not_exceed_bill'
        ),
        models.CheckConstraint(
            check=models.Q(expiry_date__gt=models.F('manufacture_date')),
            name='expiry_after_manufacture'
        )
    ]
```

## Data Migration Strategies

### Schema Changes

```python
# Example migration for adding new field
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Add new field with default value
        migrations.AddField(
            model_name='patient',
            name='blood_type',
            field=models.CharField(max_length=5, blank=True, default=''),
        ),
        
        # Create index for performance
        migrations.RunSQL(
            "CREATE INDEX idx_patient_blood_type ON core_patient(blood_type);"
        ),
    ]
```

### Data Migrations

```python
# Example data migration
def populate_patient_ages(apps, schema_editor):
    """Populate age field based on date of birth."""
    Patient = apps.get_model('core', 'Patient')
    from django.utils import timezone
    
    for patient in Patient.objects.filter(date_of_birth__isnull=False):
        today = timezone.now().date()
        age = today.year - patient.date_of_birth.year
        if today.month < patient.date_of_birth.month or \
           (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
            age -= 1
        
        # Update without triggering signals
        Patient.objects.filter(pk=patient.pk).update(age=age)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_add_age_field'),
    ]

    operations = [
        migrations.RunPython(populate_patient_ages),
    ]
```

## Query Optimization Patterns

### Efficient Queries

```python
# Good: Use select_related for foreign keys
patients_with_roles = Patient.objects.select_related('created_by__role').all()

# Good: Use prefetch_related for reverse foreign keys
patients_with_appointments = Patient.objects.prefetch_related('appointments').all()

# Good: Use annotations for calculated fields
from django.db.models import Count, Avg
patients_with_stats = Patient.objects.annotate(
    appointment_count=Count('appointments'),
    avg_age=Avg('age')
)

# Good: Use database functions
from django.db.models.functions import Upper
patients_upper_names = Patient.objects.annotate(
    upper_name=Upper('last_name')
).order_by('upper_name')

# Avoid: N+1 queries
# Bad
for patient in patients:
    print(patient.appointments.count())  # Hits database each time

# Good
patients = patients.annotate(appointment_count=Count('appointments'))
for patient in patients:
    print(patient.appointment_count)
```

### Complex Queries

```python
# Find patients with upcoming appointments
from django.utils import timezone
patients_with_upcoming = Patient.objects.filter(
    appointments__date__gte=timezone.now().date(),
    appointments__status='Scheduled'
).distinct()

# Find overdue bills
overdue_bills = Bill.objects.filter(
    due_date__lt=timezone.now().date(),
    status='Pending'
).select_related('patient')

# Find medications expiring soon
expiring_soon = StockBatch.objects.filter(
    expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30),
    quantity_available__gt=0
).select_related('medication_item')
```

---

For database administration and backup procedures, see the [Deployment Guide](../deployment/README.md).
For API usage with these models, see the [API Reference](../api/README.md).