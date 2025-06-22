from rest_framework import serializers
from .models import (
    Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem,
    Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument,
    Notification, NoteTemplate, Task, AuditLog, Bed,
    Supplier, MedicationCategory, MedicationItem, StockBatch, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, GRNItem, DispensingLog, StockAdjustment,
    ServiceCatalog, InsuranceDetail, Bill, BillItem, Payment, AppointmentNotification,
    TelemedicineSession, SyncConflict, SyncQueueStatus, Consent,
    Referral, SchedulableResource, ResourceBooking, SecureMessage, LabTestCatalog, LabOrderItem, LabResultValue,
    RoleChangeRequest, LoginActivity, ApiKey, Feedback, DelegateAccess, Organization, OrganizationMembership
)
from datetime import date, timedelta
from django.contrib.auth import get_user_model

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'language_preference', 'preferences', 'profile_image', 'two_factor_enabled']

class PatientSerializer(serializers.ModelSerializer):
    has_recent_appointment = serializers.SerializerMethodField()
    class Meta:
        model = Patient
        fields = '__all__'
        extra_kwargs = {
            'unique_id': {'required': False, 'read_only': True},
        }

    def get_has_recent_appointment(self, obj):
        recent_cutoff = date.today() - timedelta(days=30)
        return Appointment.objects.filter(
            patient=obj,
            date__gte=recent_cutoff
        ).exists()

    def create(self, validated_data):
        # Auto-generate unique_id if not provided
        if 'unique_id' not in validated_data or not validated_data['unique_id']:
            from django.utils.crypto import get_random_string
            validated_data['unique_id'] = get_random_string(8).upper()
        return super().create(validated_data)

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class VitalsSerializer(serializers.ModelSerializer):
    encounter = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Vitals
        fields = '__all__'

class MedicalConditionSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = MedicalCondition
        fields = '__all__'

class SurgicalHistorySerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = SurgicalHistory
        fields = '__all__'

class FamilyHistorySerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = FamilyHistory
        fields = '__all__'

class VaccinationSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Vaccination
        fields = '__all__'

class LabTestCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestCatalog
        fields = '__all__'

class LabOrderItemSerializer(serializers.ModelSerializer):
    lab_test = LabTestCatalogSerializer(read_only=True)
    lab_test_id = serializers.PrimaryKeyRelatedField(queryset=LabTestCatalog.objects.all(), source='lab_test', write_only=True)
    class Meta:
        model = LabOrderItem
        fields = ['id', 'lab_order', 'lab_test', 'lab_test_id', 'notes_for_lab']

class LabOrderSerializer(serializers.ModelSerializer):
    items = LabOrderItemSerializer(many=True, read_only=True)
    encounter = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LabOrder
        fields = '__all__'

class PatientDocumentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = PatientDocument
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class NoteTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteTemplate
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username') # Display username instead of ID
    class Meta:
        model = AuditLog
        fields = '__all__'

class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bed
        fields = '__all__'

class InventoryMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class MedicationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationCategory
        fields = '__all__'

class MedicationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationItem
        fields = '__all__'

class StockBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBatch
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsReceivedNote
        fields = '__all__'

class GRNItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GRNItem
        fields = '__all__'

class DispensingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispensingLog
        fields = '__all__'

class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = '__all__'

class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = '__all__'

class InsuranceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceDetail
        fields = '__all__'

class BillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillItem
        fields = '__all__'

class BillSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True, read_only=True)
    payments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Bill
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class AppointmentNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentNotification
        fields = '__all__'

class TelemedicineSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemedicineSession
        fields = '__all__'

class SyncConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncConflict
        fields = '__all__'

class SyncQueueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncQueueStatus
        fields = '__all__'

class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = '__all__'

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'

class SchedulableResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulableResource
        fields = '__all__'

class ResourceBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceBooking
        fields = '__all__'

class SecureMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')
    recipient_username = serializers.ReadOnlyField(source='recipient.username')
    class Meta:
        model = SecureMessage
        fields = '__all__'

class LabResultValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResultValue
        fields = '__all__'

    def create(self, validated_data):
        lab_result_value = super().create(validated_data)
        lab_order_item = lab_result_value.lab_order_item
        lab_test = lab_order_item.lab_test

        if lab_result_value.value_numeric is not None and lab_test.critical_range_low is not None and lab_test.critical_range_high is not None:
            if lab_result_value.value_numeric < lab_test.critical_range_low or lab_result_value.value_numeric > lab_test.critical_range_high:
                lab_result_value.abnormal_flag = 'critical'
                lab_result_value.save()

                # Create a notification for critical result
                from .models import Notification
                message = f"Critical Lab Result: {lab_test.test_name} for Patient {lab_order_item.lab_order.encounter.patient.unique_id}. Value: {lab_result_value.value_numeric} {lab_result_value.units}"
                # Assuming there's a way to determine which user/role should receive the notification (e.g., the ordering doctor)
                # For now, let's assume we notify the doctor associated with the encounter
                doctor = lab_order_item.lab_order.encounter.doctor
                if doctor:
                     Notification.objects.create(
                        user=doctor,
                        message=message,
                        type='critical_lab_result'
                    )

        return lab_result_value

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class RoleChangeRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    requested_role = RoleSerializer(read_only=True)
    requested_role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source='requested_role', write_only=True)

    class Meta:
        model = RoleChangeRequest
        fields = ['id', 'user', 'requested_role', 'requested_role_id', 'reason', 'status', 'admin_response', 'created_at', 'reviewed_at']
        read_only_fields = ['status', 'admin_response', 'created_at', 'reviewed_at', 'user', 'requested_role']

class UserPreferencesSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ['preferences', 'language_preference', 'profile_image', 'two_factor_enabled']

    def update(self, instance, validated_data):
        # Handle profile image update
        profile_image = validated_data.pop('profile_image', None)
        if profile_image:
            instance.profile_image = profile_image
        # Update preferences and other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class LoginActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginActivity
        fields = ['id', 'user', 'timestamp', 'ip_address', 'user_agent', 'status']
        read_only_fields = ['id', 'user', 'timestamp', 'ip_address', 'user_agent', 'status']

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'user', 'name', 'key', 'created_at', 'last_used_at', 'is_active']
        read_only_fields = ['id', 'user', 'key', 'created_at', 'last_used_at']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'user', 'message', 'contact_email', 'created_at', 'resolved', 'resolution_notes']
        read_only_fields = ['id', 'user', 'created_at', 'resolved', 'resolution_notes']

class DelegateAccessSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    delegate_username = serializers.CharField(source='delegate.username', read_only=True)
    class Meta:
        model = DelegateAccess
        fields = ['id', 'user', 'user_username', 'delegate', 'delegate_username', 'can_manage_schedule', 'can_view_data', 'can_act_as_user', 'created_at', 'revoked', 'revoked_at']
        read_only_fields = ['id', 'user', 'user_username', 'delegate_username', 'created_at', 'revoked_at']

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'address', 'contact_email', 'created_at', 'is_active']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = OrganizationMembership
        fields = ['id', 'user', 'user_username', 'organization', 'organization_name', 'role', 'is_active', 'joined_at', 'left_at']
        read_only_fields = ['id', 'user', 'user_username', 'organization_name', 'joined_at', 'left_at']
