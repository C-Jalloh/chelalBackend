from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from .models import Role, User, Patient, Encounter, Vitals, MedicalCondition, SurgicalHistory, FamilyHistory, Vaccination, LabOrder, PatientDocument

class PatientAPITestCase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='Admin')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=self.admin_role)
        self.client.force_authenticate(user=self.admin)

    def test_create_patient(self):
        url = reverse('patient-list')
        data = {
            'unique_id': 'P001',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'Male',
            'contact_info': '123456789',
            'address': '123 Main St',
            'known_allergies': 'None'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Patient.objects.get().first_name, 'John')

    def test_create_encounter_and_prescription(self):
        # Create patient and doctor
        patient = Patient.objects.create(
            unique_id='P002', first_name='Jane', last_name='Smith',
            date_of_birth='1985-05-05', gender='Female'
        )
        doctor_role = Role.objects.create(name='Doctor')
        doctor = User.objects.create_user(username='doc', password='docpass', role=doctor_role)
        # Create appointment
        from datetime import date, time
        from core.models import Appointment
        appointment = Appointment.objects.create(
            patient=patient, doctor=doctor, date=date.today(), time=time(10,0)
        )
        # Create encounter
        from core.models import Encounter, Prescription
        encounter_url = reverse('encounter-list')
        encounter_data = {
            'patient': patient.id,
            'appointment': appointment.id,
            'doctor': doctor.id,
            'notes': 'Routine checkup',
            'diagnosis': 'Healthy'
        }
        self.client.force_authenticate(user=doctor)
        enc_response = self.client.post(encounter_url, encounter_data, format='json')
        self.assertEqual(enc_response.status_code, 201)
        encounter_id = enc_response.data['id']
        # Create prescription
        prescription_url = reverse('prescription-list')
        prescription_data = {
            'encounter': encounter_id,
            'medication_name': 'Paracetamol',
            'dosage': '500mg',
            'frequency': 'Twice a day'
        }
        presc_response = self.client.post(prescription_url, prescription_data, format='json')
        self.assertEqual(presc_response.status_code, 201)
        self.assertEqual(Prescription.objects.count(), 1)
        self.assertEqual(Prescription.objects.get().medication_name, 'Paracetamol')

    def test_sync_offline_data_stub(self):
        url = reverse('sync_offline_data')
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.data)

    def test_check_drug_allergy(self):
        # Ensure Doctor role exists
        doctor_role, _ = Role.objects.get_or_create(name='Doctor')
        patient = Patient.objects.create(
            unique_id='P003', first_name='Allergy', last_name='Test',
            date_of_birth='2000-01-01', gender='Other', known_allergies='Penicillin, Aspirin'
        )
        doctor = User.objects.create_user(username='doc2', password='docpass', role=doctor_role)
        self.client.force_authenticate(user=doctor)
        url = reverse('prescription-check-drug-allergy')
        response = self.client.post(url, {'patient_id': patient.id, 'medication_name': 'Aspirin'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['alert'])
        response2 = self.client.post(url, {'patient_id': patient.id, 'medication_name': 'Ibuprofen'}, format='json')
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(response2.data['alert'])

    def test_sync_conflict_resolution(self):
        # Create a patient
        patient = Patient.objects.create(
            unique_id='P004', first_name='Old', last_name='Name',
            date_of_birth='1995-01-01', gender='Male'
        )
        # Simulate offline update with newer updated_at
        from django.utils import timezone
        import datetime
        new_data = {
            'batch': [
                {
                    'model': 'patient',
                    'fields': {
                        'unique_id': 'P004',
                        'first_name': 'New',
                        'last_name': 'Name',
                        'date_of_birth': '1995-01-01',
                        'gender': 'Male',
                        'updated_at': (timezone.now() + datetime.timedelta(days=1)).isoformat()
                    }
                }
            ]
        }
        url = reverse('sync_offline_data')
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, new_data, format='json')
        self.assertEqual(response.status_code, 200)
        patient.refresh_from_db()
        self.assertEqual(patient.first_name, 'New')

class AdvancedEndpointsTestCase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='Admin')
        self.doctor_role = Role.objects.create(name='Doctor')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=self.admin_role)
        self.doctor = User.objects.create_user(username='doc', password='docpass', role=self.doctor_role)
        self.patient = Patient.objects.create(unique_id='P100', first_name='Test', last_name='Patient', date_of_birth='1990-01-01', gender='Male')
        self.encounter = Encounter.objects.create(patient=self.patient, doctor=self.doctor, notes='Test', diagnosis='Test')
        self.client.force_authenticate(user=self.doctor)

    def test_add_vitals_to_encounter(self):
        url = reverse('encounter-add-vitals', args=[self.encounter.id])
        data = {
            'systolic_bp': 120,
            'diastolic_bp': 80,
            'heart_rate': 70,
            'respiratory_rate': 16,
            'temperature': 36.7,
            'oxygen_saturation': 98,
            'height': 175,
            'weight': 70
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('Vitals add error:', response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Vitals.objects.filter(encounter=self.encounter).count(), 1)

    def test_add_lab_order_to_encounter(self):
        url = reverse('encounter-add-lab-order', args=[self.encounter.id])
        data = {
            'test_name': 'CBC',
            'specimen_type': 'Blood',
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('Lab order add error:', response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LabOrder.objects.filter(encounter=self.encounter).count(), 1)

    def test_patient_vitals_history(self):
        Vitals.objects.create(encounter=self.encounter, systolic_bp=120, diastolic_bp=80, heart_rate=70, respiratory_rate=16, temperature=36.7, oxygen_saturation=98, height=175, weight=70)
        url = reverse('patient-vitals-history', args=[self.patient.id])
        response = self.client.get(url)
        if response.status_code != 200:
            print('Vitals history error:', response.data)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_patient_medical_conditions(self):
        url = reverse('patient-medical-conditions', args=[self.patient.id])
        data = {'name': 'Hypertension', 'notes': 'Chronic', 'diagnosed_at': '2020-01-01'}
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('Medical condition add error:', response.data)
        self.assertEqual(response.status_code, 201)
        response = self.client.get(url)
        if response.status_code != 200:
            print('Medical condition get error:', response.data)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_patient_vaccinations(self):
        url = reverse('patient-vaccinations', args=[self.patient.id])
        data = {'vaccine_name': 'COVID-19', 'date_administered': '2021-01-01', 'dose_number': '1', 'administered_by': 'Nurse'}
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('Vaccination add error:', response.data)
        self.assertEqual(response.status_code, 201)
        response = self.client.get(url)
        if response.status_code != 200:
            print('Vaccination get error:', response.data)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_patient_documents(self):
        url = reverse('patient-documents', args=[self.patient.id])
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile('test.txt', b'hello world', content_type='text/plain')
        data = {'file': file, 'description': 'Test doc'}
        response = self.client.post(url, data, format='multipart')
        if response.status_code != 201:
            print('Document add error:', response.data)
        self.assertEqual(response.status_code, 201)
        response = self.client.get(url)
        if response.status_code != 200:
            print('Document get error:', response.data)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
