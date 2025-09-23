#!/usr/bin/env python3
import requests
import json

# Test the frontend-backend connection
def test_frontend_connection():
    print("Testing frontend-backend connection...")

    # Test basic health check (should return auth error, which means it's reachable)
    try:
        response = requests.get('http://localhost:8000/api/health/')
        print(f"Health check: {response.status_code}")
        if response.status_code == 401:
            print("✅ Backend is reachable")
        else:
            print(f"❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return False

    # Test Google Calendar endpoint without auth (should return 401)
    try:
        response = requests.post(
            'http://localhost:8000/api/google-calendar/sync/',
            json={'appointment_id': 1}
        )
        print(f"Sync endpoint (no auth): {response.status_code}")
        if response.status_code == 401:
            print("✅ Sync endpoint is reachable")
        else:
            print(f"❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Sync endpoint not reachable: {e}")
        return False

    return True

def test_with_auth():
    print("\nTesting with authentication...")

    # Login first
    login_data = {
        'username': 'cjalloh',
        'password': 'password123'
    }

    try:
        response = requests.post('http://localhost:8000/api/auth/', json=login_data)
        if response.status_code == 200:
            token = response.json()['access']
            print("✅ Authentication successful")

            # Test sync with auth
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                'http://localhost:8000/api/google-calendar/sync/',
                json={'appointment_id': 1},
                headers=headers
            )

            print(f"Sync with auth: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                print("✅ Sync working correctly!")
                return True
            else:
                print("❌ Sync failed")
                return False
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

if __name__ == '__main__':
    if test_frontend_connection():
        test_with_auth()
    else:
        print("❌ Cannot proceed without backend connection")
