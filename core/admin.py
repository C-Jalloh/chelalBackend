from django.contrib import admin
from .models import (
    Role, User, Patient, Appointment, Encounter, Prescription, InventoryItem,
    Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument,
    Notification, NoteTemplate, Task, AuditLog, Bed
)

admin.site.register(Role)
admin.site.register(User)
admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(Encounter)
admin.site.register(Prescription)
admin.site.register(InventoryItem)
admin.site.register(Vitals)
admin.site.register(MedicalCondition)
admin.site.register(SurgicalHistory)
admin.site.register(FamilyHistory)
admin.site.register(Vaccination)
admin.site.register(LabOrder)
admin.site.register(PatientDocument)
admin.site.register(Notification)
admin.site.register(NoteTemplate)
admin.site.register(Task)
admin.site.register(AuditLog)
admin.site.register(Bed)
