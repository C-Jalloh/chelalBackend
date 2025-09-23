import os
import django
import sys

# Add the project path to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()

def create_test_users():
    """
    Creates users for testing purposes with different roles.
    """
    print("--- Starting to create test users ---")

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

if __name__ == '__main__':
    create_test_users()
