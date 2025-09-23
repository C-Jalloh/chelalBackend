#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
sys.path.append('/home/c_jalloh/Documents/School/Second Semester/ITCA Week/code/chelalBackend')
django.setup()

from core.models import Patient, User, Role, Appointment

print('Patients:', Patient.objects.count())
print('Users:', User.objects.count())

doctors = User.objects.filter(role__name='Doctor')
print('Doctors:', doctors.count())

if doctors.exists():
    print('Doctor IDs:', [d.id for d in doctors])

patients = Patient.objects.all()[:3]
print('Sample Patients:', [(p.id, p.first_name, p.last_name) for p in patients])

# If no patients or doctors exist, create some test data
if Patient.objects.count() == 0:
    print('Creating test patient...')
    patient = Patient.objects.create(
        first_name='John',
        last_name='Doe',
        date_of_birth='1990-01-01',
        gender='Male',
        contact_info='john@example.com',
        address='123 Main St'
    )
    print(f'Created patient: {patient.id} - {patient.first_name} {patient.last_name}')

if doctors.count() == 0:
    print('Creating test doctor...')
    # First create Doctor role if it doesn't exist
    doctor_role, created = Role.objects.get_or_create(name='Doctor', defaults={'description': 'Medical Doctor'})
    if created:
        print('Created Doctor role')

    doctor = User.objects.create_user(
        username='cjalloh',
        email='cjalloh@example.com',
        password='password123',
        first_name='Dr',
        last_name='Jalloh'
    )
    doctor.role = doctor_role
    doctor.save()
    print(f'Created doctor: {doctor.id} - {doctor.first_name} {doctor.last_name}')

# Now create a test appointment
if Patient.objects.exists() and doctors.exists():
    patient = Patient.objects.first()
    doctor = doctors.first()

    from datetime import date, time
    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=date.today(),
        time=time(10, 0)  # 10:00 AM
    )
    print(f'Created appointment: {appointment.id} - {appointment.patient.first_name} with {appointment.doctor.first_name} on {appointment.date}')
