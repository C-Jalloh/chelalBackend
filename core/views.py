from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import viewsets, permissions
from .models import Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem, Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument, Notification, NoteTemplate, Task, AuditLog, Bed
from .serializers import (
    RoleSerializer, UserSerializer, PatientSerializer, AppointmentSerializer,
    EncounterSerializer, PrescriptionSerializer, InventoryItemSerializer,
    VitalsSerializer, MedicalConditionSerializer, SurgicalHistorySerializer, FamilyHistorySerializer, VaccinationSerializer, LabOrderSerializer, PatientDocumentSerializer, NotificationSerializer, NoteTemplateSerializer, TaskSerializer, AuditLogSerializer, BedSerializer, InventoryMedicationSerializer
)
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminOrReadOnly, IsDoctorOrReadOnly, IsReceptionistOrReadOnly
from rest_framework.permissions import IsAdminUser
from django.utils import timezone

# Create your views here.

class MyTokenObtainPairView(TokenObtainPairView):
    pass

class MyTokenRefreshView(TokenRefreshView):
    pass

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
            if medication_name and medication_name.lower() in allergies:
                return Response({'alert': True, 'message': f'Patient is allergic to {medication_name}!'}, status=200)
            return Response({'alert': False, 'message': 'No known allergy.'}, status=200)
        except Patient.DoesNotExist:
            return Response({'alert': False, 'message': 'Patient not found.'}, status=404)

    @action(detail=False, methods=['get'])
    def available_medicines(self, request):
        """Return a list of available medicines in inventory (quantity > 0)."""
        items = InventoryItem.objects.filter(quantity__gt=0)
        serializer = InventoryItemSerializer(items, many=True)
        return Response(serializer.data)

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
    serializer_class = LabOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

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
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    def get_queryset(self):
        qs = AuditLog.objects.all()
        user = self.request.query_params.get('user')
        action = self.request.query_params.get('action')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if user:
            qs = qs.filter(user_id=user)
        if action:
            qs = qs.filter(action=action)
        if date_from:
            qs = qs.filter(timestamp__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__lte=date_to)
        return qs.order_by('-timestamp')

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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_offline_data(request):
    # Example: last write wins based on updated_at
    data = request.data.get('batch', [])
    results = []
    for item in data:
        model = item.get('model')
        fields = item.get('fields', {})
        if model == 'patient':
            obj, created = Patient.objects.update_or_create(
                unique_id=fields.get('unique_id'),
                defaults=fields
            )
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
