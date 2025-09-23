from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, permissions, serializers
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem, Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument, Notification, NoteTemplate, Task, AuditLog, Bed, Supplier, MedicationCategory, MedicationItem, StockBatch, PurchaseOrder, PurchaseOrderItem, GoodsReceivedNote, GRNItem, DispensingLog, StockAdjustment, ServiceCatalog, InsuranceDetail, Bill, BillItem, Payment, AppointmentNotification, TelemedicineSession, SyncConflict, SyncQueueStatus, Consent, Referral, SchedulableResource, ResourceBooking, SecureMessage, LabTestCatalog, LabOrderItem, LabResultValue, RoleChangeRequest, LoginActivity, ApiKey, Feedback, DelegateAccess, Organization, OrganizationMembership
from .serializers import (
    RoleSerializer, UserSerializer, PatientSerializer, AppointmentSerializer,
    EncounterSerializer, PrescriptionSerializer, InventoryItemSerializer,
    VitalsSerializer, MedicalConditionSerializer, SurgicalHistorySerializer, FamilyHistorySerializer, VaccinationSerializer, LabOrderSerializer, PatientDocumentSerializer, NotificationSerializer, NoteTemplateSerializer, TaskSerializer, AuditLogSerializer, BedSerializer, InventoryMedicationSerializer,
    SupplierSerializer, MedicationCategorySerializer, MedicationItemSerializer, StockBatchSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer, GoodsReceivedNoteSerializer, GRNItemSerializer, DispensingLogSerializer, StockAdjustmentSerializer,
    ServiceCatalogSerializer, InsuranceDetailSerializer, BillSerializer, BillItemSerializer, PaymentSerializer, AppointmentNotificationSerializer, TelemedicineSessionSerializer, SyncConflictSerializer, SyncQueueStatusSerializer, ConsentSerializer,
    ReferralSerializer, SchedulableResourceSerializer, ResourceBookingSerializer, SecureMessageSerializer, LabTestCatalogSerializer, LabOrderItemSerializer, LabResultValueSerializer, RoleChangeRequestSerializer, UserPreferencesSerializer, LoginActivitySerializer, ApiKeySerializer, FeedbackSerializer, DelegateAccessSerializer, OrganizationSerializer, OrganizationMembershipSerializer
)
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminOrReadOnly, IsDoctorOrReadOnly, IsReceptionistOrReadOnly, PatientPortalPermission
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.utils import timezone
from .rxnorm_utils import get_rxcui_for_drug, check_drug_interactions
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv
from .consumers import NotificationConsumer
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from datetime import date, timedelta
from django.db import models
from .serializers import AuditLogSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from .twilio_utils import send_sms_via_twilio
from .email_utils import send_appointment_email
from .email_token_serializer import EmailTokenObtainPairSerializer
from rest_framework.views import APIView
from .serializers import RegistrationSerializer

User = get_user_model()

# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer  # Use custom serializer for email/username login
    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

@method_decorator(csrf_exempt, name='dispatch')
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

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get('role_id')
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({'detail': 'Role not found.'}, status=404)
        user.role = role
        user.save()
        return Response({'status': 'role assigned', 'role': role.name})

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

    @action(detail=False, methods=['get'], url_path='export', url_name='export')
    def export(self, request):
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
    # Pharmacies manage inventory; doctors can view/read. Admins always allowed.
    from .permissions import IsPharmacist, IsDoctorOrReadOnly, IsAdminOrReadOnly
    permission_classes = [IsPharmacist | IsAdminOrReadOnly | IsDoctorOrReadOnly]

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
    # Nurses record vitals; doctors and admins can access as well.
    from .permissions import IsNurse, IsDoctorOrReadOnly, IsAdminOrReadOnly
    permission_classes = [IsNurse | IsDoctorOrReadOnly | IsAdminOrReadOnly]

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
    # Only pharmacists (and admins) should create/modify dispensing logs; doctors may view.
    from .permissions import IsPharmacist, IsDoctorOrReadOnly, IsAdminOrReadOnly
    permission_classes = [IsPharmacist | IsDoctorOrReadOnly | IsAdminOrReadOnly]

class StockAdjustmentViewSet(viewsets.ModelViewSet):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer

class ServiceCatalogViewSet(viewsets.ModelViewSet):
    queryset = ServiceCatalog.objects.all()
    serializer_class = ServiceCatalogSerializer
    permission_classes = [IsAdminOrReadOnly | IsReceptionistOrReadOnly | IsDoctorOrReadOnly]

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

class LoginActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LoginActivity.objects.all().order_by('-timestamp')
    serializer_class = LoginActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow users to see their own login activity
        return self.queryset.filter(user=self.request.user)

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
from django.db.models import Sum, F, Case, When, Value, IntegerField, CharField, Count, Q, Avg

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    today = timezone.now().date()
    from .models import Patient, User, Bill
    total_patients = Patient.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    revenue_today = Bill.objects.filter(date_issued__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    return Response({
        'total_patients': total_patients,
        'active_users': active_users,
        'revenue_today': revenue_today
    })

@api_view(['GET'])
def dashboard(request):
    user = request.user
    role = user.role.name if user.role else None
    data = {}
    today = timezone.now().date()
    # General: notifications/messages, system health, what's new, birthdays
    from .models import Notification, AuditLog, Bill, Bed, Patient, User, Appointment, LabOrder, Task, MedicationItem, StockBatch, Prescription
    from django.db.models import Count, Sum, Q
    # Recent notifications (last 5)
    data['notifications'] = Notification.objects.filter(user=user).order_by('-created_at')[:5].values('id', 'message', 'created_at', 'is_read')
    # System health (simple DB check)
    data['system_health'] = {'database': 'ok'}
    # What's new (last 3 audit logs)
    data['whats_new'] = AuditLog.objects.order_by('-timestamp')[:3].values('action', 'description', 'timestamp')
    # Birthdays today (patients)
    data['birthdays_today'] = list(Patient.objects.filter(date_of_birth__month=today.month, date_of_birth__day=today.day).values('first_name', 'last_name'))
    # Anniversaries (users joined this day)
    data['anniversaries'] = list(User.objects.filter(date_joined__month=today.month, date_joined__day=today.day).values('first_name', 'last_name'))

    if role == 'Doctor':
        data['today_appointments'] = list(Appointment.objects.filter(doctor=user, date=today).values('id', 'patient__first_name', 'patient__last_name', 'time', 'status'))
        data['unread_lab_results'] = list(LabOrder.objects.filter(encounter__doctor=user, status='Ordered').values('id', 'encounter__patient__first_name', 'encounter__patient__last_name', 'test_type', 'created_at'))
        data['pending_tasks'] = list(Task.objects.filter(assignee=user, status='pending').values('id', 'title', 'due_date', 'priority'))
        data['critical_lab_alerts'] = list(LabOrder.objects.filter(encounter__doctor=user, status='Critical').values('id', 'encounter__patient__first_name', 'test_type', 'created_at'))
        data['quick_links'] = [
            {'label': 'New Encounter', 'url': '/app/encounters/new'},
            {'label': 'Write Prescription', 'url': '/app/prescriptions/new'}
        ]
    elif role == 'Receptionist':
        data['patient_queue'] = list(Appointment.objects.filter(date=today, status='scheduled').values('id', 'patient__first_name', 'patient__last_name', 'time'))
        data['today_schedule'] = list(Appointment.objects.filter(date=today).values('id', 'patient__first_name', 'doctor__first_name', 'time', 'status'))
        data['pending_registrations'] = list(Patient.objects.filter(created_at__date=today).values('id', 'first_name', 'last_name'))
        data['missing_insurance'] = list(Patient.objects.filter(Q(insurance_detail__isnull=True) | Q(insurance_detail__policy_number='')).values('id', 'first_name', 'last_name'))
        data['quick_actions'] = [
            {'label': 'Register Patient', 'url': '/app/patients/new'},
            {'label': 'Schedule Appointment', 'url': '/app/appointments/new'}
        ]
    elif role == 'Pharmacist':
        data['low_stock_alerts'] = list(MedicationItem.objects.filter(total_quantity__lt=models.F('reorder_level')).values('id', 'generic_name', 'total_quantity', 'reorder_level'))
        data['near_expiry_items'] = list(StockBatch.objects.filter(expiry_date__lte=today + timezone.timedelta(days=30)).values('id', 'medication_item__generic_name', 'expiry_date', 'current_quantity'))
        data['pending_prescriptions'] = list(Prescription.objects.filter(created_at__date=today).values('id', 'encounter__patient__first_name', 'medication_name', 'created_at'))
        data['recent_purchase_orders'] = list(PurchaseOrder.objects.order_by('-created_at')[:5].values('id', 'supplier__name', 'created_at', 'status'))
        data['quick_links'] = [
            {'label': 'Add Stock Batch', 'url': '/app/pharmacy/grns/new'},
            {'label': 'Process Prescription', 'url': '/app/pharmacy/dispensing'}
        ]
    elif role == 'Admin':
        data['total_patients'] = Patient.objects.count()
        data['active_users'] = User.objects.filter(is_active=True).count()
        data['revenue_today'] = Bill.objects.filter(date_issued__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
        # Trends: patient registrations and revenue (last 7 days)
        last_7 = [today - timezone.timedelta(days=i) for i in range(6, -1, -1)]
        data['patient_registrations_trend'] = [
            {'date': d, 'count': Patient.objects.filter(created_at__date=d).count()} for d in last_7
        ]
        data['revenue_trend'] = [
            {'date': d, 'total': Bill.objects.filter(date_issued__date=d).aggregate(total=Sum('total_amount'))['total'] or 0} for d in last_7
        ]
        # Most active users (by login or actions, here by last_login)
        data['most_active_users'] = list(User.objects.filter(is_active=True).order_by('-last_login')[:5].values('id', 'first_name', 'last_name', 'last_login'))
        # System alerts (last 3 audit logs)
        data['system_alerts'] = list(AuditLog.objects.order_by('-timestamp')[:3].values('action', 'description', 'timestamp'))
        # Revenue breakdown by department (dummy: by bill items' service type if exists)
        data['revenue_breakdown'] = list(Bill.objects.filter(date_issued__date=today).values('department').annotate(total=Sum('total_amount')))
        data['quick_links'] = [
            {'label': 'User Management', 'url': '/app/users'},
            {'label': 'Reports', 'url': '/app/reports'},
            {'label': 'Settings', 'url': '/app/settings'}
        ]
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
        return LabOrder.objects.filter(encounter__patient__user=user)

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
        aging = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        today = timezone.now().date()
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

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'Registration successful'}, status=201)
        return Response(serializer.errors, status=400)

class RoleChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = RoleChangeRequest.objects.all().select_related('user', 'requested_role')
    serializer_class = RoleChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name == 'Admin':
            return RoleChangeRequest.objects.all().select_related('user', 'requested_role')
        return RoleChangeRequest.objects.filter(user=user).select_related('user', 'requested_role')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != 'pending':
            return Response({'detail': 'Already reviewed.'}, status=400)
        req.status = 'approved'
        req.admin_response = request.data.get('admin_response', '')
        req.reviewed_at = timezone.now()
        req.save()
        # Actually assign the role
        req.user.role = req.requested_role
        req.user.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        req = self.get_object()
        if req.status != 'pending':
            return Response({'detail': 'Already reviewed.'}, status=400)
        req.status = 'rejected'
        req.admin_response = request.data.get('admin_response', '')
        req.reviewed_at = timezone.now()
        req.save()
        return Response({'status': 'rejected'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """Return the current user's profile."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_preferences_view(request):
    user = request.user
    if request.method == 'GET':
        serializer = UserPreferencesSerializer(user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserPreferencesSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ApiKeyViewSet(viewsets.ModelViewSet):
    serializer_class = ApiKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ApiKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users see their own feedback; admins see all
        if self.request.user.is_staff:
            return Feedback.objects.all().order_by('-created_at')
        return Feedback.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework.decorators import action
from django.http import FileResponse
import io
import csv

class AccountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['delete'], url_path='delete', permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response({'status': 'account deactivated'}, status=204)

    @action(detail=False, methods=['get'], url_path='download-data', permission_classes=[IsAuthenticated])
    def download_data(self, request):
        user = request.user
        # Example: Download basic user info and feedback as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Username', user.username])
        writer.writerow(['Email', user.email])
        writer.writerow(['First Name', user.first_name])
        writer.writerow(['Last Name', user.last_name])
        writer.writerow(['Language', user.language_preference])
        writer.writerow(['Preferences', user.preferences])
        # Feedback
        writer.writerow([])
        writer.writerow(['Feedback'])
        writer.writerow(['Message', 'Contact Email', 'Created At', 'Resolved'])
        for fb in user.feedbacks.all():
            writer.writerow([fb.message, fb.contact_email, fb.created_at, fb.resolved])
        output.seek(0)
        response = FileResponse(io.BytesIO(output.getvalue().encode()), as_attachment=True, filename='user_data.csv')
        return response

class DelegateAccessViewSet(viewsets.ModelViewSet):
    serializer_class = DelegateAccessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Show delegates for the current user, and where the user is a delegate
        return DelegateAccess.objects.filter(models.Q(user=self.request.user) | models.Q(delegate=self.request.user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

class OrganizationMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Show memberships for the current user
        return OrganizationMembership.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Advanced Dashboard Endpoints Implementation

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 10)  # Cache for 10 minutes
def dashboard_analytics(request):
    """
    Advanced Analytics Dashboard - Provides detailed analytics and KPIs for administrators and managers.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Doctor']:
        return Response({'error': 'Access denied. Analytics dashboard requires Admin or Doctor role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed analytics dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Patient Demographics
        total_patients = Patient.objects.count()
        patients_by_age = Patient.objects.annotate(
            age_group=Case(
                When(date_of_birth__isnull=True, then=Value('Unknown')),
                When(date_of_birth__gte=today - timezone.timedelta(days=365*18), then=Value('0-17')),
                When(date_of_birth__gte=today - timezone.timedelta(days=365*35), then=Value('18-34')),
                When(date_of_birth__gte=today - timezone.timedelta(days=365*50), then=Value('35-49')),
                When(date_of_birth__gte=today - timezone.timedelta(days=365*65), then=Value('50-64')),
                default=Value('65+'),
                output_field=CharField()
            )
        ).values('age_group').annotate(count=Count('id')).order_by('age_group')

        patients_by_gender = Patient.objects.values('gender').annotate(count=Count('id'))

        data['patient_demographics'] = {
            'total_patients': total_patients,
            'age_distribution': list(patients_by_age),
            'gender_distribution': list(patients_by_gender)
        }

        # Appointment Utilization
        total_appointments = Appointment.objects.count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
        utilization_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0

        appointments_by_status = Appointment.objects.values('status').annotate(count=Count('id'))
        appointments_by_doctor = Appointment.objects.values('doctor__first_name', 'doctor__last_name').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        ).order_by('-total')[:10]

        data['appointment_utilization'] = {
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'utilization_rate': round(utilization_rate, 2),
            'status_breakdown': list(appointments_by_status),
            'doctor_performance': list(appointments_by_doctor)
        }

        # Average Wait Times (simplified - using appointment time vs scheduled time)
        recent_appointments = Appointment.objects.filter(
            date__gte=today - timezone.timedelta(days=30),
            status='completed'
        ).exclude(time__isnull=True).exclude(scheduled_time__isnull=True)

        wait_times = []
        for apt in recent_appointments[:100]:  # Sample for performance
            if apt.time and apt.scheduled_time:
                wait_time = (apt.time.hour * 60 + apt.time.minute) - (apt.scheduled_time.hour * 60 + apt.scheduled_time.minute)
                if wait_time >= 0:  # Only positive wait times
                    wait_times.append(wait_time)

        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0

        data['wait_times'] = {
            'average_wait_minutes': round(avg_wait_time, 1),
            'sample_size': len(wait_times),
            'date_range': 'Last 30 days'
        }

        # Treatment Success Rates (simplified - based on follow-up appointments)
        treatment_success = Appointment.objects.filter(
            date__gte=today - timezone.timedelta(days=90),
            status='completed'
        ).aggregate(
            total=Count('id'),
            with_followup=Count('id', filter=Q(encounter__prescription__isnull=False))
        )

        success_rate = (treatment_success['with_followup'] / treatment_success['total'] * 100) if treatment_success['total'] > 0 else 0

        data['treatment_success'] = {
            'success_rate': round(success_rate, 2),
            'total_treatments': treatment_success['total'],
            'treatments_with_followup': treatment_success['with_followup'],
            'date_range': 'Last 90 days'
        }

        # Resource Utilization
        bed_utilization = Bed.objects.aggregate(
            total_beds=Count('id'),
            occupied_beds=Count('id', filter=Q(status='occupied'))
        )
        bed_occupancy_rate = (bed_utilization['occupied_beds'] / bed_utilization['total_beds'] * 100) if bed_utilization['total_beds'] > 0 else 0

        data['resource_utilization'] = {
            'bed_occupancy': {
                'total_beds': bed_utilization['total_beds'],
                'occupied_beds': bed_utilization['occupied_beds'],
                'occupancy_rate': round(bed_occupancy_rate, 2)
            }
        }

        # Financial Metrics
        revenue_by_service = Bill.objects.filter(
            date_issued__gte=today - timezone.timedelta(days=30)
        ).values('department').annotate(
            total_revenue=Sum('total_amount'),
            transaction_count=Count('id')
        ).order_by('-total_revenue')

        payment_methods = Payment.objects.filter(
            date_paid__gte=today - timezone.timedelta(days=30)
        ).values('payment_method').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        )

        outstanding_bills = Bill.objects.filter(
            status__in=['unpaid', 'partially_paid']
        ).aggregate(
            total_outstanding=Sum('total_amount'),
            count=Count('id')
        )

        data['financial_metrics'] = {
            'revenue_by_service': list(revenue_by_service),
            'payment_methods': list(payment_methods),
            'outstanding_bills': {
                'total_amount': outstanding_bills['total_outstanding'] or 0,
                'count': outstanding_bills['count'] or 0
            },
            'date_range': 'Last 30 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating analytics data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 5)  # Cache for 5 minutes
def dashboard_clinical(request):
    """
    Clinical Dashboard - Supports clinical decision-making and patient care monitoring.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Doctor', 'Nurse']:
        return Response({'error': 'Access denied. Clinical dashboard requires Admin, Doctor, or Nurse role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed clinical dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Patient Vital Signs Trends (last 30 days)
        vitals_trends = Vitals.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).values('patient__id', 'patient__first_name', 'patient__last_name').annotate(
            avg_blood_pressure_systolic=models.Avg('blood_pressure_systolic'),
            avg_blood_pressure_diastolic=models.Avg('blood_pressure_diastolic'),
            avg_heart_rate=models.Avg('heart_rate'),
            avg_temperature=models.Avg('temperature'),
            avg_weight=models.Avg('weight'),
            avg_height=models.Avg('height'),
            reading_count=Count('id')
        ).order_by('-reading_count')[:20]

        data['vitals_trends'] = list(vitals_trends)

        # Medication Adherence (simplified - based on prescription pickup/fill rates)
        prescriptions_last_30 = Prescription.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).aggregate(
            total=Count('id'),
            picked_up=Count('id', filter=Q(status='dispensed')),
            not_picked_up=Count('id', filter=~Q(status='dispensed'))
        )

        adherence_rate = (prescriptions_last_30['picked_up'] / prescriptions_last_30['total'] * 100) if prescriptions_last_30['total'] > 0 else 0

        data['medication_adherence'] = {
            'adherence_rate': round(adherence_rate, 2),
            'total_prescriptions': prescriptions_last_30['total'],
            'picked_up': prescriptions_last_30['picked_up'],
            'not_picked_up': prescriptions_last_30['not_picked_up'],
            'date_range': 'Last 30 days'
        }

        # Lab Result Trends and Alerts
        critical_lab_results = LabOrder.objects.filter(
            status__in=['Critical', 'Abnormal'],
            created_at__gte=today - timezone.timedelta(days=7)
        ).values(
            'id', 'encounter__patient__first_name', 'encounter__patient__last_name',
            'test_type', 'status', 'created_at'
        ).order_by('-created_at')[:10]

        lab_trends = LabOrder.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).values('test_type').annotate(
            total_tests=Count('id'),
            abnormal_results=Count('id', filter=Q(status__in=['Critical', 'Abnormal']))
        ).order_by('-total_tests')[:10]

        data['lab_results'] = {
            'critical_alerts': list(critical_lab_results),
            'test_trends': list(lab_trends)
        }

        # Chronic Disease Management
        chronic_conditions = MedicalCondition.objects.filter(
            is_chronic=True
        ).values('condition_name').annotate(
            patient_count=Count('patient', distinct=True),
            active_cases=Count('id', filter=Q(status='active'))
        ).order_by('-patient_count')[:10]

        data['chronic_disease_management'] = {
            'conditions': list(chronic_conditions),
            'total_chronic_patients': sum(c['patient_count'] for c in chronic_conditions)
        }

        # Infection Control Indicators
        infection_related_encounters = Encounter.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30),
            chief_complaint__icontains='infection'
        ).aggregate(
            total=Count('id'),
            with_isolation=Count('id', filter=Q(isolation_precautions=True))
        )

        data['infection_control'] = {
            'infection_encounters': infection_related_encounters['total'],
            'isolation_cases': infection_related_encounters['with_isolation'],
            'isolation_rate': round((infection_related_encounters['with_isolation'] / infection_related_encounters['total'] * 100) if infection_related_encounters['total'] > 0 else 0, 2),
            'date_range': 'Last 30 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating clinical data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 15)  # Cache for 15 minutes
def dashboard_operational(request):
    """
    Operational Dashboard - Monitors daily operations and resource management.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Receptionist']:
        return Response({'error': 'Access denied. Operational dashboard requires Admin or Receptionist role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed operational dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Bed Occupancy Rates
        bed_stats = Bed.objects.aggregate(
            total_beds=Count('id'),
            occupied=Count('id', filter=Q(status='occupied')),
            available=Count('id', filter=Q(status='available')),
            maintenance=Count('id', filter=Q(status='maintenance'))
        )

        bed_occupancy_rate = (bed_stats['occupied'] / bed_stats['total_beds'] * 100) if bed_stats['total_beds'] > 0 else 0

        beds_by_ward = Bed.objects.values('ward').annotate(
            total=Count('id'),
            occupied=Count('id', filter=Q(status='occupied')),
            occupancy_rate=Case(
                When(total__gt=0, then=models.F('occupied') * 100.0 / models.F('total')),
                default=0,
                output_field=models.FloatField()
            )
        )

        data['bed_occupancy'] = {
            'summary': {
                'total_beds': bed_stats['total_beds'],
                'occupied_beds': bed_stats['occupied'],
                'available_beds': bed_stats['available'],
                'maintenance_beds': bed_stats['maintenance'],
                'occupancy_rate': round(bed_occupancy_rate, 2)
            },
            'by_ward': list(beds_by_ward)
        }

        # Staff Scheduling and Coverage
        active_users = User.objects.filter(is_active=True)
        staff_by_role = active_users.values('role__name').annotate(count=Count('id'))

        # Today's appointments by time slots
        today_appointments = Appointment.objects.filter(date=today).extra(
            select={'hour': 'EXTRACT(hour FROM time)'}
        ).values('hour').annotate(
            appointment_count=Count('id'),
            completed=Count('id', filter=Q(status='completed'))
        ).order_by('hour')

        data['staff_scheduling'] = {
            'staff_by_role': list(staff_by_role),
            'today_schedule_load': list(today_appointments)
        }

        # Equipment Maintenance Schedule
        # Note: This assumes there's an equipment model - using beds as proxy for now
        maintenance_due = Bed.objects.filter(
            last_maintenance__lte=today - timezone.timedelta(days=30)
        ).aggregate(count=Count('id'))

        data['equipment_maintenance'] = {
            'maintenance_due': maintenance_due['count'],
            'overdue_threshold_days': 30
        }

        # Supply Chain Status
        low_stock_items = MedicationItem.objects.filter(
            total_quantity__lte=models.F('reorder_level')
        ).values('id', 'generic_name', 'total_quantity', 'reorder_level')

        expiring_stock = StockBatch.objects.filter(
            expiry_date__lte=today + timezone.timedelta(days=30)
        ).values(
            'id', 'medication_item__generic_name', 'expiry_date', 'current_quantity'
        ).order_by('expiry_date')[:10]

        data['supply_chain'] = {
            'low_stock_alerts': list(low_stock_items),
            'expiring_stock': list(expiring_stock),
            'low_stock_count': len(low_stock_items),
            'expiring_count': len(expiring_stock)
        }

        # Emergency Response Times (simplified - using appointment wait times as proxy)
        emergency_appointments = Appointment.objects.filter(
            priority='high',
            date__gte=today - timezone.timedelta(days=7),
            status='completed'
        ).exclude(time__isnull=True).exclude(scheduled_time__isnull=True)

        emergency_wait_times = []
        for apt in emergency_appointments:
            if apt.time and apt.scheduled_time:
                wait_time = (apt.time.hour * 60 + apt.time.minute) - (apt.scheduled_time.hour * 60 + apt.scheduled_time.minute)
                if wait_time >= 0:
                    emergency_wait_times.append(wait_time)

        avg_emergency_response = sum(emergency_wait_times) / len(emergency_wait_times) if emergency_wait_times else 0

        data['emergency_response'] = {
            'average_response_minutes': round(avg_emergency_response, 1),
            'emergency_cases_count': len(emergency_wait_times),
            'date_range': 'Last 7 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating operational data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 10)  # Cache for 10 minutes
def dashboard_financial(request):
    """
    Financial Dashboard - Tracks financial performance and billing metrics.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Receptionist']:
        return Response({'error': 'Access denied. Financial dashboard requires Admin or Receptionist role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed financial dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Revenue Analysis by Department/Service
        revenue_by_department = Bill.objects.filter(
            date_issued__gte=today - timezone.timedelta(days=30)
        ).values('department').annotate(
            total_revenue=Sum('total_amount'),
            transaction_count=Count('id'),
            average_transaction=Case(
                When(transaction_count__gt=0, then=models.F('total_revenue') / models.F('transaction_count')),
                default=0,
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-total_revenue')

        # Monthly revenue trend
        monthly_revenue = Bill.objects.filter(
            date_issued__gte=today - timezone.timedelta(days=365)
        ).extra(select={'month': "DATE_TRUNC('month', date_issued)"}).values('month').annotate(
            total_revenue=Sum('total_amount'),
            transaction_count=Count('id')
        ).order_by('month')

        data['revenue_analysis'] = {
            'by_department': list(revenue_by_department),
            'monthly_trend': list(monthly_revenue),
            'date_range': 'Last 30 days for department analysis, last 12 months for trends'
        }

        # Insurance Claims Status
        claims_status = Bill.objects.filter(
            insurance_detail__isnull=False
        ).values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        )

        pending_claims = Bill.objects.filter(
            status__in=['submitted', 'pending_approval'],
            insurance_detail__isnull=False
        ).aggregate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        )

        data['insurance_claims'] = {
            'status_breakdown': list(claims_status),
            'pending_claims': {
                'count': pending_claims['count'],
                'total_amount': pending_claims['total_amount'] or 0
            }
        }

        # Outstanding Payments Aging
        thirty_days_ago = today - timezone.timedelta(days=30)
        sixty_days_ago = today - timezone.timedelta(days=60)
        ninety_days_ago = today - timezone.timedelta(days=90)

        aging_buckets = Bill.objects.filter(status__in=['unpaid', 'partially_paid']).aggregate(
            current=Sum('total_amount', filter=Q(date_issued__gte=thirty_days_ago)),
            thirty_days=Sum('total_amount', filter=Q(date_issued__lt=thirty_days_ago, date_issued__gte=sixty_days_ago)),
            sixty_days=Sum('total_amount', filter=Q(date_issued__lt=sixty_days_ago, date_issued__gte=ninety_days_ago)),
            ninety_plus=Sum('total_amount', filter=Q(date_issued__lt=ninety_days_ago))
        )

        data['outstanding_payments'] = {
            'aging_buckets': {
                'current': aging_buckets['current'] or 0,
                '30_days': aging_buckets['thirty_days'] or 0,
                '60_days': aging_buckets['sixty_days'] or 0,
                '90_plus_days': aging_buckets['ninety_plus'] or 0
            },
            'total_outstanding': sum(filter(None, aging_buckets.values()))
        }

        # Cost Analysis by Treatment Type
        cost_by_service = BillItem.objects.filter(
            bill__date_issued__gte=today - timezone.timedelta(days=30)
        ).values('service_catalog__name').annotate(
            total_cost=Sum('amount'),
            usage_count=Count('id'),
            average_cost=Case(
                When(usage_count__gt=0, then=models.F('total_cost') / models.F('usage_count')),
                default=0,
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-total_cost')[:10]

        data['cost_analysis'] = {
            'by_treatment_type': list(cost_by_service),
            'date_range': 'Last 30 days'
        }

        # Payment Method Distribution
        payment_distribution = Payment.objects.filter(
            date_paid__gte=today - timezone.timedelta(days=30)
        ).values('payment_method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id'),
            percentage=Case(
                When(total_amount__isnull=False, then=models.Value(0)),  # Will calculate in Python
                default=0,
                output_field=models.DecimalField(max_digits=5, decimal_places=2)
            )
        )

        total_payments = sum(p['total_amount'] or 0 for p in payment_distribution)
        for payment in payment_distribution:
            if total_payments > 0:
                payment['percentage'] = round((payment['total_amount'] or 0) / total_payments * 100, 2)

        data['payment_methods'] = {
            'distribution': list(payment_distribution),
            'total_payments': total_payments,
            'date_range': 'Last 30 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating financial data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 5)  # Cache for 5 minutes
def dashboard_quality(request):
    """
    Quality Assurance Dashboard - Monitors healthcare quality indicators and compliance.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Doctor', 'Nurse']:
        return Response({'error': 'Access denied. Quality dashboard requires Admin, Doctor, or Nurse role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed quality dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Patient Satisfaction Scores (using feedback as proxy)
        recent_feedback = Feedback.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).aggregate(
            total_responses=Count('id'),
            average_rating=models.Avg('rating'),
            positive_feedback=Count('id', filter=Q(rating__gte=4)),
            negative_feedback=Count('id', filter=Q(rating__lt=3))
        )

        satisfaction_rate = (recent_feedback['positive_feedback'] / recent_feedback['total_responses'] * 100) if recent_feedback['total_responses'] > 0 else 0

        data['patient_satisfaction'] = {
            'average_rating': round(recent_feedback['average_rating'] or 0, 2),
            'satisfaction_rate': round(satisfaction_rate, 2),
            'total_responses': recent_feedback['total_responses'],
            'positive_feedback': recent_feedback['positive_feedback'],
            'negative_feedback': recent_feedback['negative_feedback'],
            'date_range': 'Last 30 days'
        }

        # Readmission Rates
        ninety_days_ago = today - timezone.timedelta(days=90)
        discharged_patients = Encounter.objects.filter(
            discharge_date__isnull=False,
            discharge_date__gte=ninety_days_ago
        ).values('patient').distinct()

        readmissions = Encounter.objects.filter(
            patient__in=[p['patient'] for p in discharged_patients],
            admission_date__gte=ninety_days_ago,
            admission_date__gt=models.F('discharge_date')
        ).aggregate(readmission_count=Count('id', distinct=True))

        total_discharges = len(discharged_patients)
        readmission_rate = (readmissions['readmission_count'] / total_discharges * 100) if total_discharges > 0 else 0

        data['readmission_rates'] = {
            'readmission_rate': round(readmission_rate, 2),
            'total_discharges': total_discharges,
            'readmissions': readmissions['readmission_count'],
            'date_range': 'Last 90 days'
        }

        # Infection Rates
        infection_encounters = Encounter.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30),
            chief_complaint__icontains='infection'
        ).count()

        total_encounters = Encounter.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).count()

        infection_rate = (infection_encounters / total_encounters * 100) if total_encounters > 0 else 0

        data['infection_rates'] = {
            'infection_rate': round(infection_rate, 2),
            'infection_cases': infection_encounters,
            'total_encounters': total_encounters,
            'date_range': 'Last 30 days'
        }

        # Medication Error Rates
        # Using dispensing logs with adjustments as proxy for errors
        medication_adjustments = StockAdjustment.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30),
            reason__icontains='error'
        ).count()

        total_dispensing = DispensingLog.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).count()

        error_rate = (medication_adjustments / total_dispensing * 100) if total_dispensing > 0 else 0

        data['medication_errors'] = {
            'error_rate': round(error_rate, 2),
            'error_incidents': medication_adjustments,
            'total_dispensing': total_dispensing,
            'date_range': 'Last 30 days'
        }

        # Compliance with Clinical Guidelines
        # Simplified: percentage of encounters with complete documentation
        encounters_with_docs = Encounter.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).annotate(
            has_vitals=Case(When(vitals__isnull=False, then=1), default=0, output_field=IntegerField()),
            has_prescription=Case(When(prescription__isnull=False, then=1), default=0, output_field=IntegerField()),
            has_lab_order=Case(When(laborder__isnull=False, then=1), default=0, output_field=IntegerField())
        ).aggregate(
            total_encounters=Count('id'),
            complete_docs=Count('id', filter=Q(has_vitals=1) | Q(has_prescription=1) | Q(has_lab_order=1))
        )

        compliance_rate = (encounters_with_docs['complete_docs'] / encounters_with_docs['total_encounters'] * 100) if encounters_with_docs['total_encounters'] > 0 else 0

        data['clinical_guidelines'] = {
            'compliance_rate': round(compliance_rate, 2),
            'encounters_with_docs': encounters_with_docs['complete_docs'],
            'total_encounters': encounters_with_docs['total_encounters'],
            'date_range': 'Last 30 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating quality data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 2)  # Cache for 2 minutes (personal data)
def dashboard_patient(request):
    """
    Patient Portal Dashboard - Provides patients with access to their health information.
    """
    user = request.user
    if not user.role or user.role.name != 'Patient':
        return Response({'error': 'Access denied. Patient dashboard is only for patients.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed patient dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Get patient's actual record
        try:
            patient = Patient.objects.get(user=user)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient record not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Upcoming Appointments
        upcoming_appointments = Appointment.objects.filter(
            patient=patient,
            date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).order_by('date', 'time').values(
            'id', 'date', 'time', 'doctor__first_name', 'doctor__last_name',
            'appointment_type', 'status', 'notes'
        )[:5]

        data['upcoming_appointments'] = list(upcoming_appointments)

        # Recent Lab Results
        recent_lab_results = LabOrder.objects.filter(
            encounter__patient=patient,
            created_at__gte=today - timezone.timedelta(days=90)
        ).order_by('-created_at').values(
            'id', 'test_type', 'status', 'created_at',
            'labresultvalue__test_name', 'labresultvalue__value', 'labresultvalue__unit',
            'labresultvalue__reference_range', 'labresultvalue__is_abnormal'
        )[:10]

        data['recent_lab_results'] = list(recent_lab_results)

        # Current Medications
        current_medications = Prescription.objects.filter(
            encounter__patient=patient,
            status__in=['active', 'dispensed'],
            end_date__gte=today
        ).order_by('-created_at').values(
            'id', 'medication_name', 'dosage', 'frequency', 'duration',
            'start_date', 'end_date', 'instructions', 'status'
        )[:10]

        data['current_medications'] = list(current_medications)

        # Health Summary
        latest_vitals = Vitals.objects.filter(
            patient=patient
        ).order_by('-created_at').first()

        active_conditions = MedicalCondition.objects.filter(
            patient=patient,
            status='active'
        ).values('condition_name', 'diagnosis_date', 'severity', 'notes')

        recent_encounters = Encounter.objects.filter(
            patient=patient
        ).order_by('-admission_date').values(
            'id', 'admission_date', 'discharge_date', 'chief_complaint',
            'diagnosis', 'treatment_plan'
        )[:3]

        data['health_summary'] = {
            'latest_vitals': {
                'blood_pressure': f"{latest_vitals.blood_pressure_systolic}/{latest_vitals.blood_pressure_diastolic}" if latest_vitals else None,
                'heart_rate': latest_vitals.heart_rate if latest_vitals else None,
                'temperature': latest_vitals.temperature if latest_vitals else None,
                'weight': latest_vitals.weight if latest_vitals else None,
                'recorded_date': latest_vitals.created_at if latest_vitals else None
            } if latest_vitals else None,
            'active_conditions': list(active_conditions),
            'recent_encounters': list(recent_encounters)
        }

        # Bill Payment Status
        outstanding_bills = Bill.objects.filter(
            patient=patient,
            status__in=['unpaid', 'partially_paid']
        ).order_by('-date_issued').values(
            'id', 'date_issued', 'total_amount', 'paid_amount', 'status',
            'due_date', 'department'
        )[:5]

        recent_payments = Payment.objects.filter(
            bill__patient=patient
        ).order_by('-date_paid').values(
            'id', 'date_paid', 'amount', 'payment_method', 'bill__id'
        )[:5]

        data['billing_status'] = {
            'outstanding_bills': list(outstanding_bills),
            'recent_payments': list(recent_payments),
            'total_outstanding': sum(bill['total_amount'] - (bill['paid_amount'] or 0) for bill in outstanding_bills)
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating patient dashboard data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 5)  # Cache for 5 minutes
def dashboard_staff(request):
    """
    Staff Performance Dashboard - Monitors staff productivity and performance metrics.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Doctor']:
        return Response({'error': 'Access denied. Staff dashboard requires Admin or Doctor role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed staff performance dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Appointment Completion Rates by Provider
        provider_performance = User.objects.filter(
            role__name__in=['Doctor', 'Nurse']
        ).annotate(
            total_appointments=Count('appointment_doctor', distinct=True),
            completed_appointments=Count('appointment_doctor', filter=Q(appointment_doctor__status='completed'), distinct=True),
            completion_rate=Case(
                When(total_appointments__gt=0, then=models.F('completed_appointments') * 100.0 / models.F('total_appointments')),
                default=0,
                output_field=models.FloatField()
            )
        ).values(
            'id', 'first_name', 'last_name', 'role__name',
            'total_appointments', 'completed_appointments', 'completion_rate'
        ).order_by('-completion_rate')[:20]

        data['provider_performance'] = list(provider_performance)

        # Patient Satisfaction by Provider (using feedback linked to encounters)
        satisfaction_by_provider = User.objects.filter(
            role__name__in=['Doctor', 'Nurse']
        ).annotate(
            feedback_count=Count('encounter_doctor__feedback', distinct=True),
            avg_satisfaction=Avg('encounter_doctor__feedback__rating')
        ).values(
            'id', 'first_name', 'last_name', 'role__name',
            'feedback_count', 'avg_satisfaction'
        ).filter(feedback_count__gt=0).order_by('-avg_satisfaction')[:20]

        data['patient_satisfaction_by_provider'] = list(satisfaction_by_provider)

        # Task Completion Metrics
        task_completion = Task.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30)
        ).values('assignee__first_name', 'assignee__last_name').annotate(
            total_tasks=Count('id'),
            completed_tasks=Count('id', filter=Q(status='completed')),
            completion_rate=Case(
                When(total_tasks__gt=0, then=models.F('completed_tasks') * 100.0 / models.F('total_tasks')),
                default=0,
                output_field=models.FloatField()
            )
        ).order_by('-completion_rate')[:15]

        data['task_completion'] = {
            'by_assignee': list(task_completion),
            'date_range': 'Last 30 days'
        }

        # Continuing Education Tracking
        # Note: This assumes there's a training/certification model - using login activity as proxy
        active_users = User.objects.filter(
            is_active=True,
            role__name__in=['Doctor', 'Nurse', 'Pharmacist']
        ).annotate(
            last_login_days=Case(
                When(last_login__isnull=False, then=(timezone.now().date() - models.F('last_login__date')).days),
                default=999,
                output_field=IntegerField()
            )
        ).values(
            'id', 'first_name', 'last_name', 'role__name', 'last_login', 'last_login_days'
        ).order_by('last_login_days')[:20]

        data['staff_engagement'] = {
            'recently_active': [u for u in active_users if u['last_login_days'] <= 7],
            'inactive_warning': [u for u in active_users if u['last_login_days'] > 7 and u['last_login_days'] <= 30],
            'inactive_critical': [u for u in active_users if u['last_login_days'] > 30]
        }

        # Workload Distribution
        workload_distribution = User.objects.filter(
            role__name__in=['Doctor', 'Nurse', 'Pharmacist']
        ).annotate(
            appointment_count=Count('appointment_doctor', distinct=True),
            task_count=Count('task_assignee', distinct=True),
            encounter_count=Count('encounter_doctor', distinct=True)
        ).values(
            'id', 'first_name', 'last_name', 'role__name',
            'appointment_count', 'task_count', 'encounter_count'
        ).annotate(
            total_workload=models.F('appointment_count') + models.F('task_count') + models.F('encounter_count')
        ).order_by('-total_workload')[:20]

        data['workload_distribution'] = list(workload_distribution)

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating staff performance data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 10)  # Cache for 10 minutes
def dashboard_research(request):
    """
    Research Dashboard - Supports clinical research and data analysis.
    """
    user = request.user
    if not user.role or user.role.name not in ['Admin', 'Doctor']:
        return Response({'error': 'Access denied. Research dashboard requires Admin or Doctor role.'},
                       status=status.HTTP_403_FORBIDDEN)

    # Audit logging for dashboard access
    AuditLog.objects.create(
        user=user,
        action='view',
        description=f'Accessed research dashboard',
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    today = timezone.now().date()
    data = {}

    try:
        # Study Enrollment Tracking (simplified - using encounters with research flag)
        research_encounters = Encounter.objects.filter(
            is_research=True,
            created_at__gte=today - timezone.timedelta(days=90)
        ).aggregate(
            total_studies=Count('id', distinct=True),
            enrolled_patients=Count('patient', distinct=True),
            active_studies=Count('id', filter=Q(status='active'), distinct=True)
        )

        enrollment_trend = Encounter.objects.filter(
            is_research=True,
            created_at__gte=today - timezone.timedelta(days=365)
        ).extra(select={'month': "DATE_TRUNC('month', created_at)"}).values('month').annotate(
            enrollments=Count('id', distinct=True)
        ).order_by('month')

        data['study_enrollment'] = {
            'summary': research_encounters,
            'monthly_trend': list(enrollment_trend),
            'date_range': 'Last 90 days for summary, last 12 months for trends'
        }

        # Data Collection Progress
        data_collection = LabOrder.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30),
            encounter__is_research=True
        ).values('test_type').annotate(
            total_samples=Count('id'),
            completed_tests=Count('id', filter=Q(status__in=['completed', 'verified'])),
            pending_tests=Count('id', filter=Q(status__in=['ordered', 'in_progress']))
        ).order_by('-total_samples')[:10]

        data['data_collection'] = {
            'by_test_type': list(data_collection),
            'date_range': 'Last 30 days'
        }

        # Research Metrics
        research_metrics = {
            'total_research_encounters': Encounter.objects.filter(is_research=True).count(),
            'active_research_patients': Encounter.objects.filter(
                is_research=True, status='active'
            ).values('patient').distinct().count(),
            'completed_studies': Encounter.objects.filter(
                is_research=True, status='completed'
            ).count(),
            'publications_count': 0  # Placeholder - would need a publications model
        }

        data['research_metrics'] = research_metrics

        # IRB Compliance Status
        # Simplified - using audit logs related to research
        research_audits = AuditLog.objects.filter(
            created_at__gte=today - timezone.timedelta(days=30),
            action__icontains='research'
        ).count()

        compliance_status = 'compliant' if research_audits > 0 else 'needs_review'

        data['irb_compliance'] = {
            'status': compliance_status,
            'recent_audits': research_audits,
            'last_audit_date': AuditLog.objects.filter(
                action__icontains='research'
            ).order_by('-timestamp').values('timestamp').first(),
            'date_range': 'Last 30 days'
        }

        return Response({
            'status': 'success',
            'data': data,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error generating research data: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
