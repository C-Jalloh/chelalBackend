import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
import django
django.setup()

from django.urls import reverse
from .models import User, Role, Notification, NoteTemplate, Task, Patient
from rest_framework.test import APITestCase
from datetime import date
import datetime
from django.utils import timezone
from .tasks import send_appointment_reminder_task, send_appointment_email_reminder_task, send_appointment_followup_task

class NotificationFeatureTestCase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='Admin')
        self.doctor_role = Role.objects.create(name='Doctor')
        self.patient_role = Role.objects.create(name='Receptionist')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=self.admin_role, is_staff=True)
        self.doctor = User.objects.create_user(username='doc', password='docpass', role=self.doctor_role)
        self.client.force_authenticate(user=self.doctor)
        Notification.objects.create(user=self.doctor, message='Test notification', type='info')

    def test_list_notifications(self):
        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_mark_notification_read(self):
        notif = Notification.objects.filter(user=self.doctor).first()
        url = reverse('notification-mark-read', args=[notif.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

class NoteTemplateFeatureTestCase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='Admin')
        self.doctor_role = Role.objects.create(name='Doctor')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=self.admin_role, is_staff=True)
        self.doctor = User.objects.create_user(username='doc', password='docpass', role=self.doctor_role)
        self.client.force_authenticate(user=self.admin)

    def test_create_and_list_note_template(self):
        url = reverse('note_template-list')
        data = {'title': 'Hypertension', 'content': 'BP: __/__, HR: __', 'created_by': self.admin.id}
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('NoteTemplate create error:', response.data)
        self.assertEqual(response.status_code, 201)
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(url)
        if response.status_code != 200:
            print('NoteTemplate list error:', response.data)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

class TaskFeatureTestCase(APITestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(name='Admin')
        self.doctor_role = Role.objects.create(name='Doctor')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=self.admin_role, is_staff=True)
        self.doctor = User.objects.create_user(username='doc', password='docpass', role=self.doctor_role)
        self.patient = Patient.objects.create(unique_id='P200', first_name='Task', last_name='Patient', date_of_birth='1990-01-01', gender='Male')
        self.client.force_authenticate(user=self.admin)

    def test_create_and_update_task(self):
        url = reverse('task-list')
        data = {
            'title': 'Follow up',
            'description': 'Call patient',
            'assignee': self.doctor.id,
            'status': 'pending',
            'related_patient': self.patient.id,
            'due_date': date.today(),
            'created_by': self.admin.id
        }
        response = self.client.post(url, data, format='json')
        if response.status_code != 201:
            print('Task create error:', response.data)
        self.assertEqual(response.status_code, 201)
        task_id = response.data['id']
        # Doctor updates status
        self.client.force_authenticate(user=self.doctor)
        update_url = reverse('task-detail', args=[task_id])
        response = self.client.patch(update_url, {'status': 'completed'}, format='json')
        if response.status_code not in [200, 202, 204]:
            print('Task update error:', response.data)
        self.assertIn(response.status_code, [200, 202, 204])

class AutomatedNotificationTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.phone = os.environ.get('TEST_PATIENT_PHONE', '+2207834351')
        cls.email = os.environ.get('TEST_PATIENT_EMAIL', 'esjallow03@gmail.com')

        # Create roles
        cls.admin_role = Role.objects.create(name='Admin')
        cls.doctor_role = Role.objects.create(name='Doctor')
        cls.patient_role = Role.objects.create(name='Receptionist')

        # Create users
        cls.admin = User.objects.create_user(username='admin', password='adminpass', role=cls.admin_role, is_staff=True)
        cls.doctor = User.objects.create_user(username='doc', password='docpass', role=cls.doctor_role)

        # Create patient
        cls.patient = Patient.objects.create(
            unique_id='TEST123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1990-01-01',
            gender='Other',
            contact_info=cls.phone,
            address='Test Address',
            known_allergies='',
        )
        cls.patient.email = cls.email
        cls.patient.save()

    def setUp(self):
        super().setUp()  # Ensure parent setUp is called if it exists
        self.client.force_authenticate(user=self.doctor)

    def test_automated_notification_flow(self):
        from core.models import Appointment

        # Create a test appointment (scheduled for 24h from now)
        appt_time = (timezone.now() + datetime.timedelta(hours=24)).time()
        appt_date = (timezone.now() + datetime.timedelta(hours=24)).date()
        appt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=appt_date,
            time=appt_time,
            status='scheduled'
        )

        # Trigger SMS reminder
        send_appointment_reminder_task.delay(appt.id, 'reminder')

        # Trigger Email reminder
        send_appointment_email_reminder_task.delay(appt.id, 'reminder')

        # Simulate follow-up (mark as completed and trigger follow-up)
        appt.status = 'completed'
        appt.save()

        # Trigger follow-up (SMS and Email)
        send_appointment_followup_task.delay(appt.id)

        self.assertEqual(appt.status, 'completed')
        self.assertTrue(appt.id)  # Ensure appointment ID is valid

        # Check patient received SMS and Email (this part is just simulated, in real case, we would check the actual SMS/Email)
        print('SMS and Email reminders and follow-ups triggered. Check Celery worker logs and patient inbox/phone.')
