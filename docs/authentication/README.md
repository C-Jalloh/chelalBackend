# Authentication Guide

This guide covers authentication and authorization mechanisms for the Chelal Hospital Management System API.

## Overview

The Chelal HMS uses JWT (JSON Web Token) based authentication with role-based access control (RBAC) to secure API endpoints and protect patient data.

## Authentication Flow

### 1. User Login
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "doctor1",
    "password": "secure_password"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "doctor1",
        "email": "doctor1@hospital.com",
        "role": {
            "name": "Doctor",
            "permissions": ["view_patient", "create_prescription"]
        }
    }
}
```

### 2. Using Access Token
Include the access token in the Authorization header:

```http
GET /api/patients/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 3. Token Refresh
When the access token expires (60 minutes), use the refresh token:

```http
POST /api/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## JWT Token Structure

### Access Token Payload
```json
{
    "token_type": "access",
    "exp": 1640995200,
    "iat": 1640991600,
    "jti": "abc123",
    "user_id": 1,
    "username": "doctor1",
    "role": "Doctor"
}
```

### Token Expiration
- **Access Token**: 60 minutes
- **Refresh Token**: 7 days

## Role-Based Access Control

### User Roles

#### Admin
- **Description**: System administrators with full access
- **Permissions**: All system operations
- **Typical Users**: IT administrators, system managers

```json
{
    "role": "Admin",
    "permissions": [
        "view_all", "create_all", "update_all", "delete_all",
        "manage_users", "manage_roles", "system_configuration"
    ]
}
```

#### Doctor
- **Description**: Medical professionals providing patient care
- **Permissions**: Patient records, prescriptions, medical procedures
- **Typical Users**: Physicians, specialists

```json
{
    "role": "Doctor",
    "permissions": [
        "view_patient", "create_patient", "update_patient",
        "view_encounter", "create_encounter", "update_encounter",
        "create_prescription", "view_prescription",
        "create_lab_order", "view_lab_results"
    ]
}
```

#### Nurse
- **Description**: Nursing staff providing patient care
- **Permissions**: Basic patient care, vitals, medication administration
- **Typical Users**: Registered nurses, nurse practitioners

```json
{
    "role": "Nurse",
    "permissions": [
        "view_patient", "update_patient_vitals",
        "view_encounter", "update_encounter_notes",
        "view_prescription", "record_medication_administration",
        "create_vitals", "view_vitals"
    ]
}
```

#### Receptionist
- **Description**: Front desk staff managing appointments and registration
- **Permissions**: Patient registration, appointment scheduling
- **Typical Users**: Front desk clerks, administrative staff

```json
{
    "role": "Receptionist",
    "permissions": [
        "view_patient", "create_patient", "update_patient_demographics",
        "view_appointment", "create_appointment", "update_appointment",
        "cancel_appointment", "check_in_patient"
    ]
}
```

#### Pharmacist
- **Description**: Pharmacy staff managing medications
- **Permissions**: Medication dispensing, inventory management
- **Typical Users**: Pharmacists, pharmacy technicians

```json
{
    "role": "Pharmacist",
    "permissions": [
        "view_prescription", "update_prescription_status",
        "create_dispensing_log", "view_medication_inventory",
        "update_medication_inventory", "create_stock_adjustment"
    ]
}
```

#### Lab Technician
- **Description**: Laboratory staff processing tests
- **Permissions**: Lab order processing, result entry
- **Typical Users**: Lab technicians, pathologists

```json
{
    "role": "Lab Technician",
    "permissions": [
        "view_lab_order", "update_lab_order_status",
        "create_lab_results", "update_lab_results",
        "view_lab_catalog"
    ]
}
```

## Permission-Based Endpoint Access

### Patient Endpoints
```python
# View patient list - Doctors, Nurses, Receptionists
GET /api/patients/
Required: view_patient

# Create patient - Doctors, Receptionists
POST /api/patients/
Required: create_patient

# Update patient - Role-specific permissions
PUT /api/patients/{id}/
Required: update_patient (Doctors), update_patient_demographics (Receptionists)
```

### Prescription Endpoints
```python
# View prescriptions - Doctors, Nurses, Pharmacists
GET /api/prescriptions/
Required: view_prescription

# Create prescription - Doctors only
POST /api/prescriptions/
Required: create_prescription

# Update prescription status - Pharmacists
PUT /api/prescriptions/{id}/status/
Required: update_prescription_status
```

## API Client Implementation

### Python Example
```python
import requests
from datetime import datetime, timedelta

class HMSClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def login(self, username, password):
        """Login and store tokens."""
        response = requests.post(f"{self.base_url}/api/auth/login/", {
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.refresh_token = data['refresh']
            # JWT expires in 60 minutes
            self.token_expiry = datetime.now() + timedelta(minutes=58)
            return True
        return False
    
    def refresh_access_token(self):
        """Refresh the access token."""
        if not self.refresh_token:
            return False
        
        response = requests.post(f"{self.base_url}/api/auth/refresh/", {
            "refresh": self.refresh_token
        })
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access']
            self.token_expiry = datetime.now() + timedelta(minutes=58)
            return True
        return False
    
    def get_headers(self):
        """Get authorization headers with token refresh if needed."""
        if self.token_expiry and datetime.now() >= self.token_expiry:
            self.refresh_access_token()
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_patients(self):
        """Get patient list."""
        response = requests.get(
            f"{self.base_url}/api/patients/",
            headers=self.get_headers()
        )
        return response.json()

# Usage
client = HMSClient('https://api.chelalhms.com')
if client.login('doctor1', 'password'):
    patients = client.get_patients()
```

### JavaScript Example
```javascript
class HMSClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.tokenExpiry = localStorage.getItem('token_expiry');
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access;
            this.refreshToken = data.refresh;
            this.tokenExpiry = Date.now() + (58 * 60 * 1000); // 58 minutes
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('refresh_token', this.refreshToken);
            localStorage.setItem('token_expiry', this.tokenExpiry);
            
            return true;
        }
        return false;
    }
    
    async refreshAccessToken() {
        if (!this.refreshToken) return false;
        
        const response = await fetch(`${this.baseUrl}/api/auth/refresh/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh: this.refreshToken})
        });
        
        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access;
            this.tokenExpiry = Date.now() + (58 * 60 * 1000);
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('token_expiry', this.tokenExpiry);
            
            return true;
        }
        return false;
    }
    
    async getAuthHeaders() {
        if (Date.now() >= this.tokenExpiry) {
            await this.refreshAccessToken();
        }
        
        return {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
        };
    }
    
    async apiCall(endpoint, options = {}) {
        const headers = await this.getAuthHeaders();
        
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {...headers, ...options.headers}
        });
        
        if (response.status === 401) {
            // Token expired, try refresh
            if (await this.refreshAccessToken()) {
                const newHeaders = await this.getAuthHeaders();
                return fetch(`${this.baseUrl}${endpoint}`, {
                    ...options,
                    headers: {...newHeaders, ...options.headers}
                });
            }
        }
        
        return response;
    }
    
    async getPatients() {
        const response = await this.apiCall('/api/patients/');
        return response.json();
    }
}

// Usage
const client = new HMSClient('https://api.chelalhms.com');
await client.login('doctor1', 'password');
const patients = await client.getPatients();
```

## Error Handling

### Authentication Errors

#### Invalid Credentials (401)
```json
{
    "detail": "No active account found with the given credentials"
}
```

#### Token Expired (401)
```json
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

#### Insufficient Permissions (403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

## Security Best Practices

### Token Storage
- **Frontend**: Store tokens in memory or httpOnly cookies
- **Mobile**: Use secure keychain/keystore
- **Never**: Store tokens in localStorage for sensitive applications

### Token Refresh Strategy
```javascript
// Automatic token refresh
setInterval(async () => {
    if (tokenExpiresIn(5 * 60 * 1000)) { // 5 minutes before expiry
        await refreshToken();
    }
}, 60000); // Check every minute
```

### Logout Implementation
```python
# Server-side token blacklisting
POST /api/auth/logout/
{
    "refresh": "refresh_token_here"
}
```

### Session Management
- Implement proper logout functionality
- Clear tokens on logout
- Handle token expiration gracefully
- Monitor for concurrent sessions

## Development and Testing

### Test Authentication
```python
class AuthTestCase(APITestCase):
    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
    
    def test_protected_endpoint_requires_auth(self):
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, 401)
    
    def test_role_based_access(self):
        # Test that receptionist cannot create prescriptions
        self.client.force_authenticate(user=self.receptionist_user)
        response = self.client.post('/api/prescriptions/', {...})
        self.assertEqual(response.status_code, 403)
```

### Mock Authentication for Development
```python
# settings.py for development
if DEBUG:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
        'rest_framework.authentication.SessionAuthentication'
    )
```

## Troubleshooting

### Common Issues

#### "Token is invalid or expired"
- Check token expiration time
- Verify token format
- Ensure correct authentication header format

#### "You do not have permission"
- Verify user role and permissions
- Check endpoint permission requirements
- Confirm user account is active

#### Login fails with correct credentials
- Check user account status
- Verify password hasn't expired
- Check for account lockout

### Debug Tools
```python
# Decode JWT token for debugging
import jwt

def decode_token(token):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        return None
```

## Migration from Other Auth Systems

### From Session-Based Auth
1. Implement JWT alongside sessions
2. Gradually migrate endpoints
3. Update client applications
4. Remove session authentication

### From API Keys
1. Create user accounts for API key holders
2. Map API keys to user roles
3. Update client authentication
4. Deprecate API key system

---

For more information, see:
- [API Overview](../api/overview.md)
- [Security Documentation](../security/README.md)
- [Development Guidelines](../development/guidelines.md)