from rest_framework import serializers
from .models import (
    Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem,
    Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument,
    Notification, NoteTemplate, Task, AuditLog, Bed,
    Supplier, MedicationCategory, MedicationItem, StockBatch, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, GRNItem, DispensingLog, StockAdjustment,
    ServiceCatalog, InsuranceDetail, Bill, BillItem, Payment, AppointmentNotification,
    TelemedicineSession, SyncConflict, SyncQueueStatus, Consent,
    Referral, SchedulableResource, ResourceBooking, SecureMessage, LabTestCatalog, LabOrderItem, LabResultValue
)

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

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
