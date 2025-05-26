from django.urls import path, include
from rest_framework import routers
from .views import (
    RoleViewSet, UserViewSet, PatientViewSet, AppointmentViewSet,
    EncounterViewSet, PrescriptionViewSet, MyTokenObtainPairView, MyTokenRefreshView, sync_offline_data,
    report_patient_count, report_appointments_today, report_appointments_by_doctor, report_top_prescribed_medications,
    InventoryItemViewSet, VitalsViewSet, MedicalConditionViewSet, SurgicalHistoryViewSet, FamilyHistoryViewSet, VaccinationViewSet, LabOrderViewSet, PatientDocumentViewSet,
    NotificationViewSet, NoteTemplateViewSet, TaskViewSet, AuditLogViewSet, BedViewSet
)

router = routers.DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'users', UserViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'encounters', EncounterViewSet)
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'vitals', VitalsViewSet)
router.register(r'medical_conditions', MedicalConditionViewSet)
router.register(r'surgical_history', SurgicalHistoryViewSet)
router.register(r'family_history', FamilyHistoryViewSet)
router.register(r'vaccinations', VaccinationViewSet)
router.register(r'lab_orders', LabOrderViewSet)
router.register(r'documents', PatientDocumentViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'note_templates', NoteTemplateViewSet, basename='note_template')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'audit_logs', AuditLogViewSet, basename='auditlog')
router.register(r'beds', BedViewSet, basename='bed')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('sync_offline_data/', sync_offline_data, name='sync_offline_data'),
    path('report/patient_count/', report_patient_count, name='report_patient_count'),
    path('report/appointments_today/', report_appointments_today, name='report_appointments_today'),
    path('report/appointments_by_doctor/', report_appointments_by_doctor, name='report_appointments_by_doctor'),
    path('report/top_prescribed_medications/', report_top_prescribed_medications, name='report_top_prescribed_medications'),
]
