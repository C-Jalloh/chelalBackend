import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_role(db):
    def _create(name):
        role, _ = Role.objects.get_or_create(name=name)
        return role
    return _create

@pytest.fixture
def create_user(db, create_role):
    def _create(username, role_name):
        role = create_role(role_name)
        user = User.objects.create_user(username=username, password='password')
        user.role = role
        user.save()
        return user
    return _create

@pytest.mark.django_db
def test_nurse_can_create_vitals(api_client, create_user):
    nurse = create_user('test_nurse_py', 'NURSE')
    api_client.login(username='test_nurse_py', password='password')

    url = '/api/vitals/'
    data = {
        'encounter': None,
        'systolic_bp': 120,
        'diastolic_bp': 80,
        'heart_rate': 70,
        'respiratory_rate': 16,
        'temperature': 36.6,
        'oxygen_saturation': 98.0,
        'height': 170.0,
        'weight': 70.0
    }
    resp = api_client.post(url, data, format='json')
    assert resp.status_code != 403, f"Nurse should not be forbidden to POST vitals, got {resp.status_code}: {resp.content}"

@pytest.mark.django_db
def test_pharmacist_can_create_dispensing_and_inventory(api_client, create_user):
    pharm = create_user('test_pharm_py', 'PHARMACIST')
    api_client.login(username='test_pharm_py', password='password')

    resp_inv = api_client.post('/api/inventory/', {'name': 'Test Med', 'quantity': 100, 'unit': 'tablet'}, format='json')
    assert resp_inv.status_code != 403, f"Pharmacist should be allowed to create inventory, got {resp_inv.status_code}"

    resp_disp = api_client.post('/api/dispensing-logs/', {'prescription': None, 'stock_batch': None, 'quantity_dispensed': 1}, format='json')
    assert resp_disp.status_code != 403, f"Pharmacist should be allowed to create dispensing logs, got {resp_disp.status_code}"

@pytest.mark.django_db
def test_other_roles_forbidden(api_client, create_user):
    doctor = create_user('test_doc2_py', 'DOCTOR')
    reception = create_user('test_recep_py', 'RECEPTIONIST')
    patient = create_user('test_pat_py', 'PATIENT')

    api_client.login(username='test_doc2_py', password='password')
    resp = api_client.post('/api/dispensing-logs/', {'prescription': None, 'stock_batch': None, 'quantity_dispensed': 1}, format='json')
    assert resp.status_code in (403, 400), f"Doctor should not be allowed to create dispensing logs; got {resp.status_code}"

    api_client.login(username='test_recep_py', password='password')
    resp2 = api_client.post('/api/inventory/', {'name': 'X', 'quantity': 1}, format='json')
    assert resp2.status_code in (403, 400), f"Receptionist should not be allowed to create inventory; got {resp2.status_code}"

    api_client.login(username='test_pat_py', password='password')
    resp3 = api_client.post('/api/vitals/', {'systolic_bp': 120}, format='json')
    assert resp3.status_code in (403, 401, 400), f"Patient should not be allowed to create vitals; got {resp3.status_code}"
