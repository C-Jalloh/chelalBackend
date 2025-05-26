from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

class Patient(models.Model):
    unique_id = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10)
    contact_info = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    known_allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.unique_id})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__name': 'Doctor'})
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Encounter(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__name': 'Doctor'})
    notes = models.TextField()
    diagnosis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Prescription(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE)
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InventoryItem(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, default="tablet")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

class Vitals(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='vitals')
    systolic_bp = models.PositiveIntegerField()
    diastolic_bp = models.PositiveIntegerField()
    heart_rate = models.PositiveIntegerField()
    respiratory_rate = models.PositiveIntegerField()
    temperature = models.FloatField()
    oxygen_saturation = models.FloatField()
    height = models.FloatField(help_text="cm")
    weight = models.FloatField(help_text="kg")
    bmi = models.FloatField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.height and self.weight:
            height_m = self.height / 100.0
            self.bmi = round(self.weight / (height_m ** 2), 2)
        super().save(*args, **kwargs)

class MedicalCondition(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_conditions')
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    diagnosed_at = models.DateField(null=True, blank=True)

class SurgicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='surgical_history')
    procedure = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True)

class FamilyHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='family_history')
    relation = models.CharField(max_length=100)
    condition = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

class Vaccination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vaccinations')
    vaccine_name = models.CharField(max_length=255)
    date_administered = models.DateField()
    dose_number = models.CharField(max_length=50, blank=True)
    administered_by = models.CharField(max_length=255, blank=True)

class LabOrder(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='lab_orders')
    test_name = models.CharField(max_length=255)
    specimen_type = models.CharField(max_length=100, blank=True)
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Ordered')
    result_details = models.TextField(blank=True)
    result_file = models.FileField(upload_to='lab_results/', blank=True, null=True)

class PatientDocument(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='patient_documents/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=50, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object = models.CharField(max_length=100, blank=True)  # e.g., 'Appointment:5'

class NoteTemplate(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    related_patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("view", "View"),
        ("edit", "Edit"),
        ("create", "Create"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("other", "Other"),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class Bed(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("cleaning", "Cleaning"),
        ("maintenance", "Maintenance"),
    ]
    number = models.CharField(max_length=10, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    assigned_patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='beds')
    last_assigned = models.DateTimeField(null=True, blank=True)
