from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    language_preference = models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('fr', 'French'), ('sw', 'Swahili')])

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
        ("logout", "Logout"), # Added logout action
        ("other", "Other"),
        ("export", "Export"), # Added export action
        ("2fa_enable", "2FA Enabled"), # Added 2FA actions
        ("2fa_disable", "2FA Disabled"),
        ("2fa_verify", "2FA Verified"),
        ("session_revoke", "Session Revoked"), # Added session action
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=64, blank=True, null=True) # Make nullable
    object_id = models.CharField(max_length=64, blank=True, null=True) # Make nullable
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True) # Add JSONField for details

class Ward(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Bed(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("cleaning", "Cleaning"),
        ("maintenance", "Maintenance"),
    ]
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True, related_name='beds') # Add ForeignKey to Ward
    number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    assigned_patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_bed') # Changed related_name
    last_assigned = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('ward', 'number') # Ensure bed number is unique within a ward

    def __str__(self):
        return f"Bed {self.number} ({self.ward.name if self.ward else 'No Ward'})"

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class MedicationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class MedicationItem(models.Model):
    generic_name = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=255, blank=True)
    formulation = models.CharField(max_length=50, choices=[('Tablet','Tablet'),('Syrup','Syrup'),('Injection','Injection'),('Capsule','Capsule'),('Other','Other')])
    strength = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(MedicationCategory, on_delete=models.SET_NULL, null=True, blank=True)
    unit_of_measure = models.CharField(max_length=50, default='Box')
    reorder_level = models.PositiveIntegerField(default=0)
    reorder_quantity = models.PositiveIntegerField(default=0)
    storage_conditions = models.TextField(blank=True)
    is_controlled_substance = models.BooleanField(default=False)
    total_quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.generic_name} ({self.strength})"

class StockBatch(models.Model):
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity_received = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    received_date = models.DateField(auto_now_add=True)
    cost_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('medication_item', 'batch_number')

    def __str__(self):
        return f"{self.medication_item} - Batch {self.batch_number}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Received', 'Partially Received'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled'),
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"PO#{self.id} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.CASCADE)
    quantity_ordered = models.PositiveIntegerField()

class GoodsReceivedNote(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    grn_date = models.DateField(auto_now_add=True)
    invoice_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"GRN#{self.id} - {self.supplier.name}"

class GRNItem(models.Model):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name='items')
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity_received = models.PositiveIntegerField()

class DispensingLog(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    stock_batch = models.ForeignKey(StockBatch, on_delete=models.CASCADE)
    quantity_dispensed = models.PositiveIntegerField()
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dispense_date = models.DateTimeField(auto_now_add=True)

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ('Damaged', 'Damaged'),
        ('Expired-Discarded', 'Expired-Discarded'),
        ('Stock-Take Variance', 'Stock-Take Variance'),
        ('Internal Transfer', 'Internal Transfer'),
    ]
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.CASCADE)
    stock_batch = models.ForeignKey(StockBatch, on_delete=models.SET_NULL, null=True, blank=True)
    adjustment_type = models.CharField(max_length=50, choices=ADJUSTMENT_TYPE_CHOICES)
    quantity = models.IntegerField()
    reason = models.TextField(blank=True)
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    adjustment_date = models.DateTimeField(auto_now_add=True)

class ServiceCatalog(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class InsuranceDetail(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_details')
    provider = models.CharField(max_length=255)
    policy_number = models.CharField(max_length=100)
    coverage_details = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.provider} - {self.policy_number}"

class Bill(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True)
    date_issued = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    insurance = models.ForeignKey(InsuranceDetail, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Bill #{self.id} for {self.patient}"

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(ServiceCatalog, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.description} x{self.quantity}"

class Payment(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, choices=[('Cash','Cash'),('Card','Card'),('Insurance','Insurance')])
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Payment {self.amount} for Bill #{self.bill.id}"

class AppointmentNotification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ("reminder", "Reminder"),
        ("followup", "Follow-up"),
    ]
    CHANNEL_CHOICES = [
        ("sms", "SMS"),
        ("email", "Email"),
    ]
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, default="pending")  # pending, sent, failed
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.notification_type} for {self.appointment} via {self.channel} ({self.status})"

class TelemedicineSession(models.Model):
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE, related_name='telemedicine_session')
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField(null=True, blank=True)
    video_room_id = models.CharField(max_length=128, blank=True, null=True)
    join_url_doctor = models.URLField(blank=True, null=True)
    join_url_patient = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TelemedicineSession for Appointment {self.appointment_id}"

class SyncConflict(models.Model):
    model_name = models.CharField(max_length=128)
    record_id = models.CharField(max_length=64)
    field = models.CharField(max_length=64)
    device_id = models.CharField(max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    server_value = models.TextField()
    device_value = models.TextField()
    resolved_value = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='resolved_conflicts', blank=True)
    status = models.CharField(max_length=32, default='pending')  # pending, resolved
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Conflict {self.model_name}:{self.record_id} ({self.field})"

class SyncQueueStatus(models.Model):
    device_id = models.CharField(max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    queue_length = models.IntegerField(default=0)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default='idle')  # idle, syncing, error
    error_message = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SyncQueueStatus for {self.device_id} ({self.user})"

class Consent(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=64, choices=[('treatment', 'Treatment'), ('data_processing', 'Data Processing'), ('research', 'Research')])
    given = models.BooleanField(default=True)
    given_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Consent: {self.patient} - {self.consent_type} ({'Given' if self.given else 'Revoked'})"

class Referral(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='referrals')
    referring_doctor_details = models.CharField(max_length=255)
    referred_to_doctor_details = models.CharField(max_length=255)
    reason_for_referral = models.TextField()
    status = models.CharField(max_length=32, choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Declined', 'Declined'), ('Completed', 'Completed')], default='Pending')
    referral_letter_document = models.ForeignKey('PatientDocument', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Referral for {self.patient} to {self.referred_to_doctor_details} ({self.status})"

class SchedulableResource(models.Model):
    name = models.CharField(max_length=128)
    resource_type = models.CharField(max_length=64, choices=[('Operating Room', 'Operating Room'), ('Equipment', 'Equipment'), ('Other', 'Other')])
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

class ResourceBooking(models.Model):
    resource = models.ForeignKey(SchedulableResource, on_delete=models.CASCADE, related_name='bookings')
    booked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey('Patient', on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    purpose = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.resource} booking for {self.patient} ({self.status})"

class SecureMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='secure_message_attachments/', null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} ({'read' if self.is_read else 'unread'})"

class LabTestCatalog(models.Model):
    test_code = models.CharField(max_length=64, unique=True)
    test_name = models.CharField(max_length=255)
    specimen_type = models.CharField(max_length=64)
    department = models.CharField(max_length=64)
    critical_range_low = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    critical_range_high = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    def __str__(self):
        return f"{self.test_name} ({self.test_code})"

class LabOrderItem(models.Model):
    lab_order = models.ForeignKey('LabOrder', on_delete=models.CASCADE, related_name='items')
    lab_test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE)
    notes_for_lab = models.TextField(blank=True)

    def __str__(self):
        return f"{self.lab_test.test_name} for Order {self.lab_order_id}"

class LabResultValue(models.Model):
    ABNORMAL_CHOICES = [
        ('normal', 'Normal'),
        ('low', 'Low'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    lab_order_item = models.ForeignKey(LabOrderItem, on_delete=models.CASCADE, related_name='results')
    parameter_name = models.CharField(max_length=128)
    value_numeric = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    value_text = models.CharField(max_length=128, blank=True)
    units = models.CharField(max_length=32, blank=True)
    reference_range_low = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    reference_range_high = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    abnormal_flag = models.CharField(max_length=16, choices=ABNORMAL_CHOICES, default='normal')
    result_timestamp = models.DateTimeField(auto_now_add=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.parameter_name}: {self.value_numeric or self.value_text} {self.units}"
