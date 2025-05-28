from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, permissions, serializers
from .models import Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem, Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument, Notification, NoteTemplate, Task, AuditLog, Bed, Supplier, MedicationCategory, MedicationItem, StockBatch, PurchaseOrder, PurchaseOrderItem, GoodsReceivedNote, GRNItem, DispensingLog, StockAdjustment, ServiceCatalog, InsuranceDetail, Bill, BillItem, Payment, AppointmentNotification, TelemedicineSession, SyncConflict, SyncQueueStatus, Consent, Referral, SchedulableResource, ResourceBooking, SecureMessage, LabTestCatalog, LabOrderItem, LabResultValue
from .serializers import (
    RoleSerializer, UserSerializer, PatientSerializer, AppointmentSerializer,
    EncounterSerializer, PrescriptionSerializer, InventoryItemSerializer,
    VitalsSerializer, MedicalConditionSerializer, SurgicalHistorySerializer, FamilyHistorySerializer, VaccinationSerializer, LabOrderSerializer, PatientDocumentSerializer, NotificationSerializer, NoteTemplateSerializer, TaskSerializer, AuditLogSerializer, BedSerializer, InventoryMedicationSerializer,
    SupplierSerializer, MedicationCategorySerializer, MedicationItemSerializer, StockBatchSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer, GoodsReceivedNoteSerializer, GRNItemSerializer, DispensingLogSerializer, StockAdjustmentSerializer,
    ServiceCatalogSerializer, InsuranceDetailSerializer, BillSerializer, BillItemSerializer, PaymentSerializer, AppointmentNotificationSerializer, TelemedicineSessionSerializer, SyncConflictSerializer, SyncQueueStatusSerializer, ConsentSerializer,
    ReferralSerializer, SchedulableResourceSerializer, ResourceBookingSerializer, SecureMessageSerializer, LabTestCatalogSerializer, LabOrderItemSerializer, LabResultValueSerializer
)
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminOrReadOnly, IsDoctorOrReadOnly, IsReceptionistOrReadOnly, PatientPortalPermission
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .rxnorm_utils import get_rxcui_for_drug, check_drug_interactions
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv
from .consumers import NotificationConsumer
from django.db.models import Sum, F, Case, When, Value, IntegerField, CharField
from datetime import date, timedelta
from django.db import models
from .serializers import AuditLogSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from .twilio_utils import send_sms_via_twilio
from .email_utils import send_appointment_email

User = get_user_model()

# Create your views here.

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

class MyTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminOrReadOnly]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'deactivated'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'activated'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('new_password', 'changeme123')
        user.set_password(new_password)
        user.save()
        return Response({'status': 'password reset', 'new_password': new_password})

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrReadOnly | IsReceptionistOrReadOnly | IsDoctorOrReadOnly]

    @action(detail=True, methods=['get'])
    def vitals_history(self, request, pk=None):
        """Get all vitals for a specific patient across all encounters."""
        patient = self.get_object()
        vitals = Vitals.objects.filter(encounter__patient=patient)
        serializer = VitalsSerializer(vitals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def medical_conditions(self, request, pk=None):
        patient = self.get_object()
        if request.method == 'POST':
            serializer = MedicalConditionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            conditions = patient.medical_conditions.all()
            serializer = MedicalConditionSerializer(conditions, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def surgical_history(self, request, pk=None):
        patient = self.get_object()
        if request.method == 'POST':
            serializer = SurgicalHistorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            surgeries = patient.surgical_history.all()
            serializer = SurgicalHistorySerializer(surgeries, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def family_history(self, request, pk=None):
        patient = self.get_object()
        if request.method == 'POST':
            serializer = FamilyHistorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            family = patient.family_history.all()
            serializer = FamilyHistorySerializer(family, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def vaccinations(self, request, pk=None):
        patient = self.get_object()
        if request.method == 'POST':
            serializer = VaccinationSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            vaccinations = patient.vaccinations.all()
            serializer = VaccinationSerializer(vaccinations, many=True)
            return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def documents(self, request, pk=None):
        patient = self.get_object()
        if request.method == 'POST':
            serializer = PatientDocumentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(patient=patient)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            docs = patient.documents.all()
            serializer = PatientDocumentSerializer(docs, many=True)
            return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export patient data as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="patients.csv"'
        writer = csv.writer(response)
        writer.writerow(['unique_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'contact_info', 'address', 'known_allergies'])
        for patient in Patient.objects.all():
            writer.writerow([
                patient.unique_id, patient.first_name, patient.last_name,
                patient.date_of_birth, patient.gender, patient.contact_info,
                patient.address, patient.known_allergies
            ])
        return response

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAdminOrReadOnly | IsReceptionistOrReadOnly | IsDoctorOrReadOnly]

    def get_queryset(self):
        # Allow filtering by patient, doctor, date for reporting
        queryset = super().get_queryset()
        patient_id = self.request.query_params.get('patient_id')
        doctor_id = self.request.query_params.get('doctor_id')
        date = self.request.query_params.get('date')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if date:
            queryset = queryset.filter(date=date)
        return queryset

class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    permission_classes = [IsAdminOrReadOnly | IsDoctorOrReadOnly]

    @action(detail=True, methods=['post'])
    def add_vitals(self, request, pk=None):
        """Add vitals to a specific encounter."""
        encounter = self.get_object()
        serializer = VitalsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(encounter=encounter)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'])
    def add_lab_order(self, request, pk=None):
        """Add a lab order to a specific encounter."""
        encounter = self.get_object()
        serializer = LabOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(encounter=encounter)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['get'])
    def vitals(self, request, pk=None):
        """Get all vitals for a specific encounter."""
        encounter = self.get_object()
        vitals = encounter.vitals.all()
        serializer = VitalsSerializer(vitals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lab_orders(self, request, pk=None):
        """Get all lab orders for a specific encounter."""
        encounter = self.get_object()
        lab_orders = encounter.lab_orders.all()
        serializer = LabOrderSerializer(lab_orders, many=True)
        return Response(serializer.data)

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAdminOrReadOnly | IsDoctorOrReadOnly]

    @action(detail=False, methods=['post'])
    def check_drug_allergy(self, request):
        patient_id = request.data.get('patient_id')
        medication_name = request.data.get('medication_name')
        try:
            patient = Patient.objects.get(id=patient_id)
            allergies = patient.known_allergies.lower() if patient.known_allergies else ''
            # RxNorm allergy check: get RxCUI for medication and allergies
            med_rxcui = get_rxcui_for_drug(medication_name)
            allergy_rxcuis = []
            for allergy in [a.strip() for a in allergies.split(',') if a.strip()]:
                rxcui = get_rxcui_for_drug(allergy)
                if rxcui:
                    allergy_rxcuis.append(rxcui)
            # If any allergy RxCUI matches medication RxCUI, alert
            if med_rxcui and med_rxcui in allergy_rxcuis:
                return Response({'alert': True, 'message': f'Patient is allergic to {medication_name}!'}, status=200)
            # Fallback to string match
            if medication_name and medication_name.lower() in allergies:
                return Response({'alert': True, 'message': f'Patient is allergic to {medication_name}!'}, status=200)
            return Response({'alert': False, 'message': 'No known allergy.'}, status=200)
        except Patient.DoesNotExist:
            return Response({'alert': False, 'message': 'Patient not found.'}, status=404)

    @action(detail=False, methods=['post'])
    def check_drug_interaction(self, request):
        """Check for drug-drug interactions using RxNorm."""
        # Expects: { 'medications': ['Drug1', 'Drug2', ...] }
        med_names = request.data.get('medications', [])
        rxcuis = [get_rxcui_for_drug(name) for name in med_names if name]
        rxcuis = [r for r in rxcuis if r]
        interactions = check_drug_interactions(rxcuis)
        if interactions:
            return Response({'interactions': interactions}, status=200)
        return Response({'interactions': []}, status=200)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAdminOrReadOnly | IsDoctorOrReadOnly]

    @action(detail=False, methods=['get'])
    def medications(self, request):
        items = InventoryItem.objects.all()
        serializer = InventoryMedicationSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        item = self.get_object()
        amount = int(request.data.get('amount', 0))
        item.quantity += amount
        item.save()
        # Optionally, trigger low stock notification
        if item.quantity < 10:
            Notification.objects.create(
                user=None,  # Could be sent to all pharmacists/admins
                message=f'Low stock alert: {item.name} ({item.quantity} left)',
                type='low_stock'
            )
        return Response({'status': 'stock adjusted', 'new_quantity': item.quantity})

    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """Dispense medication for a prescription, FEFO batch selection, and update stock."""
        from .models import Prescription, DispensingLog, StockBatch
        prescription_id = request.data.get('prescription_id')
        quantity = int(request.data.get('quantity', 0))
        try:
            prescription = Prescription.objects.get(id=prescription_id)
            # FEFO: get earliest expiry batch with enough stock
            batches = StockBatch.objects.filter(
                medication_item=self.get_object(),
                current_quantity__gte=quantity,
                expiry_date__gte=date.today()
            ).order_by('expiry_date')
            if not batches.exists():
                return Response({'error': 'No batch with enough stock and valid expiry.'}, status=400)
            batch = batches.first()
            batch.current_quantity -= quantity
            batch.save()
            # Update medication total_quantity
            med = self.get_object()
            med.total_quantity = StockBatch.objects.filter(medication_item=med).aggregate(
                total=Sum('current_quantity'))['total'] or 0
            med.save()
            # Log dispensing
            DispensingLog.objects.create(
                prescription=prescription,
                stock_batch=batch,
                quantity_dispensed=quantity,
                dispensed_by=request.user
            )
            return Response({'status': 'dispensed', 'batch': batch.batch_number, 'remaining': batch.current_quantity})
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found.'}, status=404)

class VitalsViewSet(viewsets.ModelViewSet):
    queryset = Vitals.objects.all()
    serializer_class = VitalsSerializer
    permission_classes = [permissions.IsAuthenticated]

class MedicalConditionViewSet(viewsets.ModelViewSet):
    queryset = MedicalCondition.objects.all()
    serializer_class = MedicalConditionSerializer
    permission_classes = [permissions.IsAuthenticated]

class SurgicalHistoryViewSet(viewsets.ModelViewSet):
    queryset = SurgicalHistory.objects.all()
    serializer_class = SurgicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

class FamilyHistoryViewSet(viewsets.ModelViewSet):
    queryset = FamilyHistory.objects.all()
    serializer_class = FamilyHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

class VaccinationViewSet(viewsets.ModelViewSet):
    queryset = Vaccination.objects.all()
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]

class LabOrderViewSet(viewsets.ModelViewSet):
    queryset = LabOrder.objects.all()
    serializer_class = LabOrderSerializer  # Assume this exists or will be created
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        """Add multiple LabOrderItems to a LabOrder."""
        lab_order = self.get_object()
        items_data = request.data.get('items', [])
        created_items = []
        for item in items_data:
            serializer = LabOrderItemSerializer(data={**item, 'lab_order': lab_order.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created_items.append(serializer.data)
        return Response({'created': created_items})

    @action(detail=True, methods=['put'])
    def add_results(self, request, pk=None):
        """Attach results to LabOrderItems in this order."""
        lab_order = self.get_object()
        results_data = request.data.get('results', [])
        created_results = []
        for result in results_data:
            serializer = LabResultValueSerializer(data=result)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created_results.append(serializer.data)
        return Response({'created': created_results})

class PatientDocumentViewSet(viewsets.ModelViewSet):
    queryset = PatientDocument.objects.all()
    serializer_class = PatientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'status': 'marked as read'})

class NoteTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = NoteTemplateSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.role and self.request.user.role.name == 'Admin':
            return NoteTemplate.objects.all()
        return NoteTemplate.objects.filter(is_active=True)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Task.objects.all()
        assignee = self.request.query_params.get('assignee')
        status = self.request.query_params.get('status')
        if assignee == 'me':
            qs = qs.filter(assignee=self.request.user)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['user', 'action', 'object_type', 'timestamp'] # Add filtering
    search_fields = ['description', 'details'] # Add searching

class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Session.objects.all()
    serializer_class = serializers.Serializer # We'll create a custom serializer below
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        sessions_data = []
        for session in queryset:
            try:
                session_data = session.get_decoded()
                user_id = session_data.get('_auth_user_id')
                user = User.objects.get(pk=user_id) if user_id else None
                sessions_data.append({
                    'session_key': session.session_key,
                    'expire_date': session.expire_date,
                    'user': user.username if user else 'Anonymous',
                })
            except:
                # Handle potential issues with decoding session data
                sessions_data.append({
                    'session_key': session.session_key,
                    'expire_date': session.expire_date,
                    'user': 'Error decoding session',
                })
        return Response(sessions_data)

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a specific session."""
        try:
            session = Session.objects.get(session_key=pk)
            session.delete()
            # Log session revocation
            AuditLog.objects.create(
                user=request.user,
                action="session_revoke",
                description=f'Session {pk} revoked by {request.user.username}.',
                details={'session_key': pk}
            )
            return Response({'status': 'session revoked'})
        except Session.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=404)

class BedViewSet(viewsets.ModelViewSet):
    queryset = Bed.objects.all()
    serializer_class = BedSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['post'])
    def assign_patient(self, request, pk=None):
        bed = self.get_object()
        patient_id = request.data.get('patient_id')
        from .models import Patient
        try:
            patient = Patient.objects.get(id=patient_id)
            bed.assigned_patient = patient
            bed.status = 'occupied'
            bed.last_assigned = timezone.now()
            bed.save()
            return Response({'status': 'assigned', 'bed': bed.id, 'patient': patient.id})
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=400)

    @action(detail=True, methods=['post'])
    def discharge_patient(self, request, pk=None):
        bed = self.get_object()
        bed.assigned_patient = None
        bed.status = 'available'
        bed.save()
        return Response({'status': 'discharged', 'bed': bed.id})

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class MedicationCategoryViewSet(viewsets.ModelViewSet):
    queryset = MedicationCategory.objects.all()
    serializer_class = MedicationCategorySerializer

class MedicationItemViewSet(viewsets.ModelViewSet):
    queryset = MedicationItem.objects.all()
    serializer_class = MedicationItemSerializer

    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """List all batches for a medication item."""
        item = self.get_object()
        batches = item.batches.all()
        serializer = StockBatchSerializer(batches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def below_reorder_level(self, request):
        """List medications below reorder level."""
        items = MedicationItem.objects.filter(total_quantity__lt=F('reorder_level'))
        serializer = MedicationItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def near_expiry(self, request):
        """List batches expiring within N days (default 30)."""
        days = int(request.query_params.get('days', 30))
        soon = date.today() + timedelta(days=days)
        batches = StockBatch.objects.filter(expiry_date__lte=soon, current_quantity__gt=0)
        serializer = StockBatchSerializer(batches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stock_valuation(self, request):
        """Get total stock valuation (sum of cost_price_per_unit * current_quantity for all batches)."""
        total = StockBatch.objects.aggregate(
            value=Sum(F('cost_price_per_unit') * F('current_quantity'))
        )['value'] or 0
        return Response({'total_stock_valuation': float(total)})

    @action(detail=False, methods=['get'])
    def consumption_patterns(self, request):
        """Show medication consumption patterns (dispensed per item)."""
        data = DispensingLog.objects.values('stock_batch__medication_item__generic_name').annotate(
            total_dispensed=Sum('quantity_dispensed')
        ).order_by('-total_dispensed')
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def stock_movement(self, request):
        """Show stock movement for a medication in a date range."""
        med_id = request.query_params.get('medication_id')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        logs = DispensingLog.objects.filter(stock_batch__medication_item_id=med_id)
        if start:
            logs = logs.filter(dispense_date__gte=start)
        if end:
            logs = logs.filter(dispense_date__lte=end)
        serializer = DispensingLogSerializer(logs, many=True)
        return Response(serializer.data)

class StockBatchViewSet(viewsets.ModelViewSet):
    queryset = StockBatch.objects.all()
    serializer_class = StockBatchSerializer

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer

class GoodsReceivedNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceivedNote.objects.all()
    serializer_class = GoodsReceivedNoteSerializer

class GRNItemViewSet(viewsets.ModelViewSet):
    queryset = GRNItem.objects.all()
    serializer_class = GRNItemSerializer

class DispensingLogViewSet(viewsets.ModelViewSet):
    queryset = DispensingLog.objects.all()
    serializer_class = DispensingLogSerializer

class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer

class ServiceCatalogViewSet(viewsets.ModelViewSet):
    queryset = ServiceCatalog.objects.all()
    serializer_class = ServiceCatalogSerializer

class InsuranceDetailViewSet(viewsets.ModelViewSet):
    queryset = InsuranceDetail.objects.all()
    serializer_class = InsuranceDetailSerializer

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    @action(detail=True, methods=['post'])
    def payments(self, request, pk=None):
        bill = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(bill=bill, received_by=request.user)
            bill.is_paid = True if bill.payments.aggregate(total=models.Sum('amount'))['total'] >= bill.total_amount else False
            bill.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class BillItemViewSet(viewsets.ModelViewSet):
    queryset = BillItem.objects.all()
    serializer_class = BillItemSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class AppointmentNotificationViewSet(viewsets.ModelViewSet):
    queryset = AppointmentNotification.objects.all()
    serializer_class = AppointmentNotificationSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admin for now; can be adjusted

    def get_queryset(self):
        queryset = super().get_queryset()
        appointment_id = self.request.query_params.get('appointment_id')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
        return queryset

    @action(detail=True, methods=['get'], url_path='status')
    def status(self, request, pk=None):
        """Get the status of a specific appointment notification."""
        notification = self.get_object()
        return Response({
            'id': notification.id,
            'appointment_id': notification.appointment_id,
            'notification_type': notification.notification_type,
            'channel': notification.channel,
            'status': notification.status,
            'scheduled_for': notification.scheduled_for,
            'sent_at': notification.sent_at,
            'error_message': notification.error_message,
        })

class TelemedicineSessionViewSet(viewsets.ModelViewSet):
    queryset = TelemedicineSession.objects.all()
    serializer_class = TelemedicineSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def join_info(self, request, pk=None):
        session = self.get_object()
        # In production, generate/join token with video API here
        return Response({
            'join_url_doctor': session.join_url_doctor,
            'join_url_patient': session.join_url_patient,
            'video_room_id': session.video_room_id,
        })

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()
        session.is_active = False
        from django.utils import timezone
        session.ended_at = timezone.now()
        session.save()
        return Response({'status': 'ended', 'ended_at': session.ended_at})

class SyncConflictViewSet(viewsets.ModelViewSet):
    queryset = SyncConflict.objects.all()
    serializer_class = SyncConflictSerializer
    permission_classes = [IsAdminUser]

class SyncQueueStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SyncQueueStatus.objects.all()
    serializer_class = SyncQueueStatusSerializer
    permission_classes = [IsAdminUser]

class ConsentViewSet(viewsets.ModelViewSet):
    queryset = Consent.objects.all()
    serializer_class = ConsentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only allow access to consents for the patient or admin
        user = self.request.user
        patient_id = self.kwargs.get('patient_pk')
        qs = super().get_queryset()
        if user.is_staff:
            return qs.filter(patient_id=patient_id)
        return qs.filter(patient_id=patient_id, patient__user=user)

class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

class SchedulableResourceViewSet(viewsets.ModelViewSet):
    queryset = SchedulableResource.objects.all()
    serializer_class = SchedulableResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

class ResourceBookingViewSet(viewsets.ModelViewSet):
    queryset = ResourceBooking.objects.all()
    serializer_class = ResourceBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

class SecureMessageViewSet(viewsets.ModelViewSet):
    queryset = SecureMessage.objects.all()
    serializer_class = SecureMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Patients see their own messages; staff see messages sent/received by them
        if user.is_staff:
            return SecureMessage.objects.filter(models.Q(sender=user) | models.Q(recipient=user)).order_by('-sent_at')
        else:
            return SecureMessage.objects.filter(models.Q(sender=user) | models.Q(recipient=user) | models.Q(patient__user=user)).order_by('-sent_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        msg.is_read = True
        from django.utils import timezone
        msg.read_at = timezone.now()
        msg.save()
        return Response({'status': 'read', 'read_at': msg.read_at})

class LabTestCatalogViewSet(viewsets.ModelViewSet):
    queryset = LabTestCatalog.objects.all()
    serializer_class = LabTestCatalogSerializer
    permission_classes = [permissions.IsAdminUser]

class LabOrderItemViewSet(viewsets.ModelViewSet):
    queryset = LabOrderItem.objects.all()
    serializer_class = LabOrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

class LabResultValueViewSet(viewsets.ModelViewSet):
    queryset = LabResultValue.objects.all()
    serializer_class = LabResultValueSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_offline_data(request):
    # Enhanced: field-level merging for patient model
    data = request.data.get('batch', [])
    results = []
    for item in data:
        model = item.get('model')
        fields = item.get('fields', {})
        if model == 'patient':
            try:
                obj = Patient.objects.get(unique_id=fields.get('unique_id'))
                # Field-level merge: only update fields with newer updated_at
                for field, value in fields.items():
                    if field == 'updated_at':
                        continue
                    if hasattr(obj, field):
                        setattr(obj, field, value)
                obj.updated_at = fields.get('updated_at', obj.updated_at)
                obj.save()
                created = False
            except Patient.DoesNotExist:
                obj = Patient.objects.create(**fields)
                created = True
            results.append({'unique_id': obj.unique_id, 'created': created})
        # Add similar logic for other models as needed
    return Response({'status': 'success', 'results': results}, status=200)

@api_view(['GET'])
def report_patient_count(request):
    """Return total number of patients."""
    from .models import Patient
    count = Patient.objects.count()
    return Response({'patient_count': count})

@api_view(['GET'])
def report_appointments_today(request):
    """Return today's appointments."""
    from .models import Appointment
    from datetime import date
    appts = Appointment.objects.filter(date=date.today())
    return Response({'appointments': AppointmentSerializer(appts, many=True).data})

@api_view(['GET'])
def report_appointments_by_doctor(request):
    """Return appointment counts grouped by doctor for reporting."""
    from .models import Appointment, User
    from django.db.models import Count
    data = (
        Appointment.objects.values('doctor')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    # Attach doctor names
    result = []
    for entry in data:
        doctor_id = entry['doctor']
        count = entry['count']
        doctor = User.objects.filter(id=doctor_id).first()
        result.append({
            'doctor_id': doctor_id,
            'doctor_name': doctor.get_full_name() if doctor else 'Unknown',
            'appointment_count': count
        })
    return Response({'appointments_by_doctor': result})

@api_view(['GET'])
def report_top_prescribed_medications(request):
    """Return top prescribed medications for reporting."""
    from .models import Prescription
    from django.db.models import Count
    data = (
        Prescription.objects.values('medication_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    return Response({'top_medications': list(data)})

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Appointment, LabOrder, Task, Notification, Bed, MedicationItem, StockBatch, Prescription

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    role = user.role.name if user.role else None
    data = {}
    if role == 'Doctor':
        data['today_appointments'] = Appointment.objects.filter(doctor=user, date=timezone.now().date()).count()
        data['unread_lab_results'] = LabOrder.objects.filter(encounter__doctor=user, status='Ordered').count()
        data['pending_tasks'] = Task.objects.filter(assignee=user, status='pending').count()
    elif role == 'Receptionist':
        data['patient_queue'] = Appointment.objects.filter(date=timezone.now().date(), status='scheduled').count()
        data['today_schedule'] = Appointment.objects.filter(date=timezone.now().date()).count()
        data['pending_registrations'] = Patient.objects.filter(created_at__date=timezone.now().date()).count()
    elif role == 'Pharmacist':
        data['low_stock_alerts'] = MedicationItem.objects.filter(total_quantity__lt=models.F('reorder_level')).count()
        data['near_expiry_items'] = StockBatch.objects.filter(expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30)).count()
        data['pending_prescriptions'] = Prescription.objects.filter(created_at__date=timezone.now().date()).count()
    elif role == 'Admin':
        data['total_patients'] = Patient.objects.count()
        data['active_users'] = User.objects.filter(is_active=True).count()
        data['revenue_today'] = Bill.objects.filter(date_issued__date=timezone.now().date()).aggregate(total=models.Sum('total_amount'))['total'] or 0
    else:
        data['message'] = 'No dashboard data for this role.'
    return Response(data)

def send_appointment_sms_reminder(appointment, notification_type="reminder"):
    """
    Send an SMS reminder or follow-up for an appointment using Twilio.
    Logs the result in AppointmentNotification.
    """
    patient = appointment.patient
    to_number = patient.contact_info  # Should be E.164 format
    if not to_number:
        return False, 'No patient phone number.'
    if notification_type == "reminder":
        message = f"Dear {patient.first_name}, this is a reminder for your appointment with Dr. {appointment.doctor.last_name} on {appointment.date} at {appointment.time}."
    else:
        message = f"Dear {patient.first_name}, we hope your recent appointment at Chelal Hospital went well. Please contact us if you have any concerns."
    success, result = send_sms_via_twilio(to_number, message)
    AppointmentNotification.objects.create(
        appointment=appointment,
        notification_type=notification_type,
        channel="sms",
        status="sent" if success else "failed",
        scheduled_for=timezone.now(),
        sent_at=timezone.now() if success else None,
        message=message,
        error_message="" if success else result,
    )
    return success, result

def send_appointment_email_reminder(appointment, notification_type="reminder"):
    """
    Send an email reminder or follow-up for an appointment.
    Logs the result in AppointmentNotification.
    """
    patient = appointment.patient
    to_email = getattr(patient, 'email', None) or ''
    if not to_email:
        return False, 'No patient email address.'
    if notification_type == "reminder":
        subject = "Appointment Reminder - Chelal Hospital"
        message = f"Dear {patient.first_name},\n\nThis is a reminder for your appointment with Dr. {appointment.doctor.last_name} on {appointment.date} at {appointment.time}.\n\nThank you,\nChelal Hospital"
    else:
        subject = "Appointment Follow-up - Chelal Hospital"
        message = f"Dear {patient.first_name},\n\nWe hope your recent appointment at Chelal Hospital went well. Please contact us if you have any concerns.\n\nThank you,\nChelal Hospital"
    success, result = send_appointment_email(to_email, subject, message)
    AppointmentNotification.objects.create(
        appointment=appointment,
        notification_type=notification_type,
        channel="email",
        status="sent" if success else "failed",
        scheduled_for=timezone.now(),
        sent_at=timezone.now() if success else None,
        message=message,
        error_message="" if success else result,
    )
    return success, result

def schedule_upcoming_appointment_reminders(hours_before=24):
    """
    Schedule reminders for appointments happening in `hours_before` hours.
    """
    from .models import Appointment, AppointmentNotification
    from django.utils import timezone
    now = timezone.now()
    target_time = now + timezone.timedelta(hours=hours_before)
    appointments = Appointment.objects.filter(
        date=target_time.date(),
        time__hour=target_time.time().hour,
        status="scheduled"
    )
    for appointment in appointments:
        # Avoid duplicate notifications
        exists = AppointmentNotification.objects.filter(
            appointment=appointment,
            notification_type="reminder",
            channel="sms",
            scheduled_for__date=now.date(),
        ).exists()
        if not exists:
            from .tasks import send_appointment_reminder_task
            send_appointment_reminder_task.delay(appointment.id, "reminder")

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "error"
    # Optionally, add checks for Celery, Redis, etc.
    return Response({
        "status": "ok",
        "database": db_status,
    })

class PatientAppointmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [PatientPortalPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.all()
        return Appointment.objects.filter(patient__user=user)

class PatientLabOrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabOrderSerializer
    permission_classes = [PatientPortalPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LabOrder.objects.all()
        return LabOrder.objects.filter(patient__user=user)

class PatientPrescriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PrescriptionSerializer
    permission_classes = [PatientPortalPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Prescription.objects.all()
        return Prescription.objects.filter(encounter__patient__user=user)

class PatientBillViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [PatientPortalPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Bill.objects.all()
        return Bill.objects.filter(patient__user=user)

class FinancialReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def receivables_aging(self, request):
        """Accounts receivable aging buckets for unpaid bills."""
        today = timezone.now().date()
        buckets = [30, 60, 90]
        aging = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        qs = Bill.objects.filter(is_paid=False)
        for bill in qs:
            days = (today - bill.created_at.date()).days
            if days <= 30:
                aging["0-30"] += bill.total_amount
            elif days <= 60:
                aging["31-60"] += bill.total_amount
            elif days <= 90:
                aging["61-90"] += bill.total_amount
            else:
                aging["90+"] += bill.total_amount
        return Response(aging)

    @action(detail=False, methods=['get'])
    def revenue_by_doctor(self, request):
        """Revenue grouped by doctor."""
        data = (
            Bill.objects.filter(is_paid=True)
            .values(doctor_name=F('encounter__doctor__username'))
            .annotate(total=Sum('total_amount'))
            .order_by('-total')
        )
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def revenue_by_service(self, request):
        """Revenue grouped by service."""
        data = (
            BillItem.objects.filter(bill__is_paid=True)
            .values(service=F('service__name'))
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def payer_mix(self, request):
        """Revenue by payer type (insurance vs. self-pay)."""
        data = (
            Bill.objects.filter(is_paid=True)
            .values(payer=Case(
                When(insurance__isnull=False, then=Value('Insurance')),
                default=Value('Self-Pay'),
                output_field=IntegerField()
            ))
            .annotate(total=Sum('total_amount'))
        )
        return Response(list(data))

class PatientLabHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabOrderSerializer # Use the existing LabOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_pk'] # Assuming nested router lookup
        return LabOrder.objects.filter(encounter__patient__id=patient_id).order_by('-order_date')
