from rest_framework.test import APITestCase
from django.urls import reverse
from .models import User, Role, Notification, NoteTemplate, Task, Patient
from datetime import date

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
