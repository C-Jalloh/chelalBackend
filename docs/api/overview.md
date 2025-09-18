# API Overview

The Chelal Hospital Management System provides a comprehensive REST API for managing all aspects of hospital operations.

## Base URL

```
https://your-domain.com/api/
```

For local development:
```
http://localhost:8000/api/
```

## API Versioning

Currently, the API is version 1 and all endpoints are prefixed with `/api/`.

## Authentication

The API uses JWT (JSON Web Token) authentication. See [Authentication Guide](../authentication/README.md) for details.

### Quick Start
```bash
# Login to get tokens
POST /api/auth/login/
{
    "username": "your-username",
    "password": "your-password"
}

# Use access token in headers
Authorization: Bearer <access_token>
```

## Content Type

All API requests and responses use `application/json` content type.

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no content returned |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

## Core Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/register/` - User registration

### User Management
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

### Patient Management
- `GET /api/patients/` - List patients
- `POST /api/patients/` - Create patient
- `GET /api/patients/{id}/` - Get patient details
- `PUT /api/patients/{id}/` - Update patient
- `DELETE /api/patients/{id}/` - Delete patient

### Appointment Management
- `GET /api/appointments/` - List appointments
- `POST /api/appointments/` - Create appointment
- `GET /api/appointments/{id}/` - Get appointment details
- `PUT /api/appointments/{id}/` - Update appointment
- `DELETE /api/appointments/{id}/` - Cancel appointment

### Medical Records
- `GET /api/encounters/` - List encounters
- `POST /api/encounters/` - Create encounter
- `GET /api/encounters/{id}/` - Get encounter details
- `PUT /api/encounters/{id}/` - Update encounter

### Pharmacy Management
- `GET /api/medications/` - List medications
- `POST /api/medications/` - Add medication
- `GET /api/prescriptions/` - List prescriptions
- `POST /api/prescriptions/` - Create prescription

### Billing
- `GET /api/bills/` - List bills
- `POST /api/bills/` - Create bill
- `GET /api/bills/{id}/` - Get bill details
- `POST /api/payments/` - Record payment

## Pagination

List endpoints support pagination using query parameters:

```bash
GET /api/patients/?page=1&page_size=20
```

Response format:
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/patients/?page=2",
    "previous": null,
    "results": [...]
}
```

## Filtering and Search

Most list endpoints support filtering:

```bash
# Filter patients by name
GET /api/patients/?search=john

# Filter appointments by date
GET /api/appointments/?date=2024-01-15

# Filter by status
GET /api/appointments/?status=scheduled
```

## Ordering

Use the `ordering` parameter to sort results:

```bash
# Order by creation date (descending)
GET /api/patients/?ordering=-created_at

# Order by name (ascending)
GET /api/patients/?ordering=first_name
```

## Error Handling

The API returns consistent error responses:

```json
{
    "error": "Validation failed",
    "details": {
        "field_name": ["Error message for this field"]
    },
    "code": "validation_error"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated users

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## WebSocket Support

Real-time features are available via WebSocket connections:

```javascript
// Connect to notifications
const ws = new WebSocket('ws://localhost:8000/ws/notifications/{user_id}/');
```

## API Clients

### Python
```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login/', {
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access']

# Use token
headers = {'Authorization': f'Bearer {token}'}
patients = requests.get('http://localhost:8000/api/patients/', headers=headers)
```

### JavaScript
```javascript
// Login
const loginResponse = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'password'})
});
const {access} = await loginResponse.json();

// Use token
const patientsResponse = await fetch('/api/patients/', {
    headers: {'Authorization': `Bearer ${access}`}
});
```

## Next Steps

1. [Authentication Setup](../authentication/README.md)
2. [Endpoint Reference](../endpoints/README.md)
3. [Code Examples](../tutorials/api-examples.md)
4. [Testing the API](../testing/api-testing.md)

## Support

- [API Status Page](../operations/status.md)
- [Troubleshooting](../troubleshooting/api-issues.md)
- [FAQ](../faq/api-faq.md)