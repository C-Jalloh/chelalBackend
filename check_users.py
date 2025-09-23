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

def check_test_users():
    """
    Checks if the test users exist in the database and prints their details.
    """
    print("--- Checking for test users in the database ---")

    test_usernames = ['test_admin', 'test_doctor', 'test_receptionist', 'test_patient']

    found_users = User.objects.filter(username__in=test_usernames)

    if not found_users.exists():
        print("No test users found in the database.")
        print("Please try running the create_test_users.py script again.")
        return

    print(f"Found {found_users.count()} test user(s):")
    for user in found_users:
        role_name = user.role.name if user.role else 'No Role Assigned'
        print(f"  - Username: {user.username}, Email: {user.email}, Role: {role_name}")

    print("\n--- Finished checking for test users ---")

if __name__ == '__main__':
    check_test_users()
