from django.urls import path, include
from rest_framework import routers
from .views import (
    RoleViewSet, UserViewSet, PatientViewSet, AppointmentViewSet,
    EncounterViewSet, PrescriptionViewSet, MyTokenObtainPairView, MyTokenRefreshView, sync_offline_data,
    report_patient_count, report_appointments_today, report_appointments_by_doctor, report_top_prescribed_medications,
    InventoryItemViewSet, VitalsViewSet, MedicalConditionViewSet, SurgicalHistoryViewSet, FamilyHistoryViewSet, VaccinationViewSet, LabOrderViewSet, PatientDocumentViewSet,
    NotificationViewSet, NoteTemplateViewSet, TaskViewSet, AuditLogViewSet, BedViewSet,
    SupplierViewSet, MedicationCategoryViewSet, MedicationItemViewSet, StockBatchViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet, GoodsReceivedNoteViewSet, GRNItemViewSet, DispensingLogViewSet, StockAdjustmentViewSet,
    ServiceCatalogViewSet, InsuranceDetailViewSet, BillViewSet, BillItemViewSet, PaymentViewSet,
    AppointmentNotificationViewSet, TelemedicineSessionViewSet, SyncConflictViewSet, SyncQueueStatusViewSet, dashboard, health_check,
    ConsentViewSet, ReferralViewSet, SchedulableResourceViewSet, ResourceBookingViewSet,
    PatientAppointmentViewSet,
    PatientLabOrderViewSet,
    PatientPrescriptionViewSet,
    PatientBillViewSet,
    SecureMessageViewSet, FinancialReportViewSet, LabTestCatalogViewSet, LabOrderItemViewSet, LabResultValueViewSet,
    LabOrderViewSet, PatientLabHistoryViewSet
)
from .views import RegisterView, RoleChangeRequestViewSet, dashboard_stats
from .views import profile_view, user_preferences_view
from .views import LoginActivityViewSet, ApiKeyViewSet, FeedbackViewSet, AccountViewSet, DelegateAccessViewSet
from .views import OrganizationViewSet, OrganizationMembershipViewSet

router = routers.DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'users', UserViewSet, basename='user')
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'appointments', AppointmentViewSet)
router.register(r'encounters', EncounterViewSet)
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'inventory', InventoryItemViewSet)
router.register(r'vitals', VitalsViewSet)
router.register(r'medical_conditions', MedicalConditionViewSet)
router.register(r'surgical_history', SurgicalHistoryViewSet)
router.register(r'family_history', FamilyHistoryViewSet)
router.register(r'vaccinations', VaccinationViewSet)
router.register(r'lab_orders', LabOrderViewSet, basename='laborder')
router.register(r'documents', PatientDocumentViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'note_templates', NoteTemplateViewSet, basename='note_template')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'audit_logs', AuditLogViewSet, basename='auditlog')
router.register(r'beds', BedViewSet, basename='bed')
router.register(r'suppliers', SupplierViewSet)
router.register(r'medication-categories', MedicationCategoryViewSet)
router.register(r'medications', MedicationItemViewSet)
router.register(r'stock-batches', StockBatchViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'purchase-order-items', PurchaseOrderItemViewSet)
router.register(r'goods-received-notes', GoodsReceivedNoteViewSet)
router.register(r'grn-items', GRNItemViewSet)
router.register(r'dispensing-logs', DispensingLogViewSet)
router.register(r'stock-adjustments', StockAdjustmentViewSet)
router.register(r'service-catalog', ServiceCatalogViewSet)
router.register(r'insurance', InsuranceDetailViewSet)
router.register(r'bills', BillViewSet)
router.register(r'bill-items', BillItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'appointment-notifications', AppointmentNotificationViewSet, basename='appointmentnotification')
router.register(r'telemedicine/sessions', TelemedicineSessionViewSet, basename='telemedicinesession')
router.register(r'sync-conflicts', SyncConflictViewSet, basename='syncconflict')
router.register(r'sync-queue-status', SyncQueueStatusViewSet, basename='syncqueuestatus')
router.register(r'referrals', ReferralViewSet, basename='referral')
router.register(r'resources', SchedulableResourceViewSet, basename='schedulableresource')
router.register(r'resource-bookings', ResourceBookingViewSet, basename='resourcebooking')
router.register(r'secure-messages', SecureMessageViewSet, basename='securemessage')
router.register(r'financial-reports', FinancialReportViewSet, basename='financialreport')
router.register(r'lab_tests/catalog', LabTestCatalogViewSet, basename='labtestcatalog')
router.register(r'lab_order_items', LabOrderItemViewSet, basename='laborderitem')
router.register(r'lab_result_values', LabResultValueViewSet, basename='labresultvalue')
router.register(r'role-change-requests', RoleChangeRequestViewSet, basename='rolechangerequest')
router.register(r'login-activity', LoginActivityViewSet, basename='loginactivity')
router.register(r'api-keys', ApiKeyViewSet, basename='apikey')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'account', AccountViewSet, basename='account')
router.register(r'delegates', DelegateAccessViewSet, basename='delegateaccess')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'organization-memberships', OrganizationMembershipViewSet, basename='organizationmembership')

# Patient portal endpoints
router.register(r'patient-portal/appointments', PatientAppointmentViewSet, basename='patient-portal-appointments')
router.register(r'patient-portal/laborders', PatientLabOrderViewSet, basename='patient-portal-laborders')
router.register(r'patient-portal/prescriptions', PatientPrescriptionViewSet, basename='patient-portal-prescriptions')
router.register(r'patient-portal/bills', PatientBillViewSet, basename='patient-portal-bills')

# Nested route for patient consents and lab history
from rest_framework_nested.routers import NestedDefaultRouter
patient_router = NestedDefaultRouter(router, r'patients', lookup='patient')
patient_router.register(r'consents', ConsentViewSet, basename='patient-consents')
patient_router.register(r'lab_history', PatientLabHistoryViewSet, basename='patient-lab-history')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
    path('', include(patient_router.urls)),
    path('auth/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', MyTokenRefreshView.as_view(), name='token_refresh'),
    path('sync_offline_data/', sync_offline_data, name='sync_offline_data'),
    path('report/patient_count/', report_patient_count, name='report_patient_count'),
    path('report/appointments_today/', report_appointments_today, name='report_appointments_today'),
    path('report/appointments_by_doctor/', report_appointments_by_doctor, name='report_appointments_by_doctor'),
    path('report/top_prescribed_medications/', report_top_prescribed_medications, name='report_top_prescribed_medications'),
    path('dashboard/', dashboard, name='dashboard'),
    path('health/', health_check, name='health-check'),
    path('dashboard-stats/', dashboard_stats, name='dashboard-stats'),
    path('profile/', profile_view, name='profile'),
    path('preferences/', user_preferences_view, name='user-preferences'),
]
