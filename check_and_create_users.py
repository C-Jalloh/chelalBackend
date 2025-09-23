#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

def check_test_users():
    """
    Checks if the test users exist in the database and prints their details.
    """
    print("--- Checking for test users in the database ---")

    test_usernames = ['test_admin', 'test_doctor', 'test_receptionist', 'test_patient']

    found_users = User.objects.filter(username__in=test_usernames)

    if not found_users.exists():
        print("No test users found in the database.")
        print("Creating test users now...")

        # Define roles and users
        roles_to_create = {
            'ADMIN': {'description': 'System Administrator'},
            'DOCTOR': {'description': 'Medical Doctor'},
            'RECEPTIONIST': {'description': 'Reception Staff'},
            'PATIENT': {'description': 'Patient User'},
        }

        users_to_create = [
            {'username': 'test_admin', 'password': 'password', 'email': 'admin@test.com', 'role': 'ADMIN', 'first_name': 'Test', 'last_name': 'Admin'},
            {'username': 'test_doctor', 'password': 'password', 'email': 'doctor@test.com', 'role': 'DOCTOR', 'first_name': 'Test', 'last_name': 'Doctor'},
            {'username': 'test_receptionist', 'password': 'password', 'email': 'receptionist@test.com', 'role': 'RECEPTIONIST', 'first_name': 'Test', 'last_name': 'Receptionist'},
            {'username': 'test_patient', 'password': 'password', 'email': 'patient@test.com', 'role': 'PATIENT', 'first_name': 'Test', 'last_name': 'Patient'},
        ]

        # Create roles if they don't exist
        for role_name, role_details in roles_to_create.items():
            role, created = Role.objects.get_or_create(name=role_name, defaults=role_details)
            if created:
                print(f"Role '{role.name}' created.")
            else:
                print(f"Role '{role.name}' already exists.")

        # Create users
        for user_data in users_to_create:
            try:
                if User.objects.filter(username=user_data['username']).exists():
                    print(f"User '{user_data['username']}' already exists. Skipping.")
                    continue

                role = Role.objects.get(name=user_data['role'])
                user = User.objects.create_user(
                    username=user_data['username'],
                    password=user_data['password'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=role
                )
                print(f"Successfully created user: {user.username} with role: {user.role.name}")
                print(f"  Login with: username='{user_data['username']}', password='{user_data['password']}'")

            except Role.DoesNotExist:
                print(f"Error: Role '{user_data['role']}' not found. Cannot create user '{user_data['username']}'.")
            except Exception as e:
                print(f"An error occurred while creating user '{user_data['username']}': {e}")

        print("--- Test user creation process finished ---")
        return

    print(f"Found {found_users.count()} test user(s):")
    for user in found_users:
        role_name = user.role.name if user.role else 'No Role Assigned'
        print(f"  - Username: {user.username}, Email: {user.email}, Role: {role_name}")

    print("\n--- Finished checking for test users ---")

if __name__ == '__main__':
    check_test_users()
