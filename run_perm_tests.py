#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
import django
django.setup()

from django.test.utils import get_runner
from django.conf import settings

TestRunner = get_runner(settings)
test_runner = TestRunner()
failures = test_runner.run_tests([
    'core.tests.test_nurse_can_post_vitals',
    'core.tests.test_pharmacist_can_create_inventory_and_dispensing', 
    'core.tests.test_doctor_restricted_from_dispensing'
])
print('Test run complete, failures:', failures)
