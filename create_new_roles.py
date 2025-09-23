#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from core.models import Role

def create_new_roles():
    """
    Creates NURSE and PHARMACIST roles in the database.
    """
    print("Creating new roles...")

    roles_to_create = [
        {'name': 'NURSE', 'description': 'Nursing staff responsible for patient care and vitals monitoring'},
        {'name': 'PHARMACIST', 'description': 'Pharmacy staff responsible for medication management and dispensing'},
    ]

    for role_data in roles_to_create:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'description': role_data['description']}
        )
        if created:
            print(f"✅ Created role: {role.name}")
        else:
            print(f"ℹ️  Role {role.name} already exists")

    print("Role creation completed!")

if __name__ == '__main__':
    create_new_roles()
