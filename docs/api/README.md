# API Reference - Chelal Hospital Management System

## Overview

The Chelal HMS provides a comprehensive RESTful API for all hospital management operations. All endpoints follow REST conventions and return JSON responses.

## Base Configuration

### Base URL
```
Production: https://your-domain.com/api/
Development: http://localhost:8000/api/
```

### Authentication
All API endpoints require authentication via JWT tokens.

```http
Authorization: Bearer <your-jwt-token>
```

### Content Type
```http
Content-Type: application/json
Accept: application/json
```

### Standard Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-09-17T10:30:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2024-09-17T10:30:00Z"
}
```

## Authentication Endpoints

### Login
```http
POST /api/auth/login/
```

**Request:**
```json
{
  "email": "doctor@hospital.com",
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
    "email": "doctor@hospital.com",
    "first_name": "Dr. John",
    "last_name": "Smith",
    "role": "Doctor"
  }
}
```

### Token Refresh
```http
POST /api/auth/token/refresh/
```

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Logout
```http
POST /api/auth/logout/
```

## Patient Management

### List Patients
```http
GET /api/patients/
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `search`: Search by name or unique_id
- `gender`: Filter by gender (Male/Female)
- `age_min`: Minimum age
- `age_max`: Maximum age

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/patients/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "unique_id": "P12345",
      "first_name": "Jane",
      "last_name": "Doe",
      "date_of_birth": "1990-01-01",
      "gender": "Female",
      "contact_info": "+2207834351",
      "address": "Banjul",
      "known_allergies": "Penicillin",
      "emergency_contact": "+2207834352",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Create Patient
```http
POST /api/patients/
```

**Request:**
```json
{
  "unique_id": "P12346",
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "1985-05-15",
  "gender": "Male",
  "contact_info": "+2207834353",
  "address": "Serrekunda",
  "known_allergies": "None",
  "emergency_contact": "+2207834354"
}
```

### Get Patient
```http
GET /api/patients/{id}/
```

### Update Patient
```http
PUT /api/patients/{id}/
```

```http
PATCH /api/patients/{id}/
```

### Delete Patient
```http
DELETE /api/patients/{id}/
```

### Patient Appointments
```http
GET /api/patients/{id}/appointments/
```

### Patient Lab History
```http
GET /api/patients/{id}/lab_history/
```

### Patient Prescriptions
```http
GET /api/patients/{id}/prescriptions/
```

### Patient Bills
```http
GET /api/patients/{id}/bills/
```

## Appointment Management

### List Appointments
```http
GET /api/appointments/
```

**Query Parameters:**
- `date`: Filter by specific date (YYYY-MM-DD)
- `date_from`: Start date range
- `date_to`: End date range
- `doctor`: Filter by doctor ID
- `patient`: Filter by patient ID
- `status`: Filter by status (Scheduled/Confirmed/Completed/Cancelled)

### Create Appointment
```http
POST /api/appointments/
```

**Request:**
```json
{
  "patient": 1,
  "doctor": 2,
  "date": "2024-09-20",
  "time": "10:00:00",
  "appointment_type": "Consultation",
  "notes": "Regular checkup"
}
```

### Update Appointment
```http
PUT /api/appointments/{id}/
```

### Cancel Appointment
```http
PATCH /api/appointments/{id}/
```

**Request:**
```json
{
  "status": "Cancelled",
  "cancellation_reason": "Patient unavailable"
}
```

## Clinical Management

### Create Encounter
```http
POST /api/encounters/
```

**Request:**
```json
{
  "patient": 1,
  "doctor": 2,
  "encounter_type": "Consultation",
  "chief_complaint": "Headache",
  "history_present_illness": "Patient reports severe headache for 2 days",
  "physical_examination": "Normal vital signs, no focal neurological deficits",
  "assessment": "Tension headache",
  "plan": "Rest, hydration, follow-up in 1 week"
}
```

### Add Vitals
```http
POST /api/vitals/
```

**Request:**
```json
{
  "encounter": 1,
  "temperature": 98.6,
  "blood_pressure_systolic": 120,
  "blood_pressure_diastolic": 80,
  "heart_rate": 72,
  "respiratory_rate": 16,
  "weight": 70.5,
  "height": 175
}
```

### Create Prescription
```http
POST /api/prescriptions/
```

**Request:**
```json
{
  "encounter": 1,
  "medication": "Ibuprofen",
  "dosage": "400mg",
  "frequency": "Every 6 hours",
  "duration": "3 days",
  "instructions": "Take with food"
}
```

## Laboratory Management

### Create Lab Order
```http
POST /api/lab-orders/
```

**Request:**
```json
{
  "encounter": 1,
  "test_name": "Complete Blood Count",
  "specimen_type": "Blood",
  "urgency": "Routine",
  "instructions": "Fasting required"
}
```

### Add Lab Order Items
```http
POST /api/lab-orders/{order_id}/items/
```

**Request:**
```json
{
  "test_catalog": 1,
  "quantity": 1,
  "special_instructions": "Handle with care"
}
```

### Add Lab Results
```http
POST /api/lab-orders/{order_id}/results/
```

**Request:**
```json
{
  "lab_order_item": 1,
  "parameter_name": "Hemoglobin",
  "value": "14.5",
  "unit": "g/dL",
  "reference_range": "12.0-16.0",
  "status": "Normal"
}
```

## Pharmacy Management

### Medication Inventory
```http
GET /api/pharmacy/medications/
```

### Stock Adjustment
```http
POST /api/pharmacy/stock-adjustments/
```

**Request:**
```json
{
  "medication_item": 1,
  "adjustment_type": "Addition",
  "quantity": 100,
  "reason": "New stock received",
  "batch_number": "BATCH001",
  "expiry_date": "2025-12-31"
}
```

### Dispense Medication
```http
POST /api/pharmacy/dispense/
```

**Request:**
```json
{
  "prescription": 1,
  "medication_item": 1,
  "quantity_dispensed": 30,
  "batch_number": "BATCH001",
  "dispensed_by": 1
}
```

### Purchase Orders
```http
GET /api/pharmacy/purchase-orders/
POST /api/pharmacy/purchase-orders/
```

## Billing Management

### Service Catalog
```http
GET /api/billing/services/
```

### Create Bill
```http
POST /api/bills/
```

**Request:**
```json
{
  "patient": 1,
  "encounter": 1,
  "bill_type": "Consultation",
  "items": [
    {
      "service": 1,
      "quantity": 1,
      "unit_price": 50.00
    }
  ]
}
```

### Record Payment
```http
POST /api/payments/
```

**Request:**
```json
{
  "bill": 1,
  "amount": 50.00,
  "payment_method": "Cash",
  "payment_date": "2024-09-17",
  "reference_number": "PAY001"
}
```

## Notification System

### Send Appointment Reminder
```http
POST /api/appointments/{id}/send-reminder/
```

### Real-time Notifications (WebSocket)
```
ws://your-domain/ws/notifications/{user_id}/
```

**Message Format:**
```json
{
  "type": "notification",
  "data": {
    "id": 1,
    "title": "New Lab Result",
    "message": "Lab results are ready for Patient P12345",
    "timestamp": "2024-09-17T10:30:00Z",
    "read": false
  }
}
```

## Data Export

### Export Patients
```http
GET /api/patients/export/?format=csv
```

### Export Appointments
```http
GET /api/appointments/export/?format=csv&date_from=2024-09-01&date_to=2024-09-30
```

## Financial Reporting

### Receivables Aging
```http
GET /api/financial-reports/receivables_aging/
```

**Response:**
```json
{
  "0-30": 1200.0,
  "31-60": 800.0,
  "61-90": 500.0,
  "90+": 200.0
}
```

### Revenue by Doctor
```http
GET /api/financial-reports/revenue_by_doctor/
```

**Response:**
```json
[
  {"doctor_name": "Dr. Smith", "total": 5000.0},
  {"doctor_name": "Dr. Jones", "total": 3200.0}
]
```

### Revenue by Service
```http
GET /api/financial-reports/revenue_by_service/
```

### Payer Mix Report
```http
GET /api/financial-reports/payer_mix/
```

## Advanced Features

### Drug Allergy Check
```http
POST /api/prescriptions/check_drug_allergy/
```

**Request:**
```json
{
  "patient_id": 1,
  "medication": "Penicillin"
}
```

### Drug Interaction Check
```http
POST /api/prescriptions/check_drug_interaction/
```

**Request:**
```json
{
  "medications": ["Warfarin", "Aspirin"]
}
```

### Offline Data Sync
```http
POST /api/sync_offline_data/
```

**Request:**
```json
{
  "patients": [
    {
      "local_id": "temp_1",
      "unique_id": "P12347",
      "first_name": "Alice",
      "last_name": "Johnson",
      "updated_at": "2024-09-17T10:30:00Z"
    }
  ],
  "appointments": [ ... ]
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Authentication**: 10 login attempts per hour per IP
- **Export**: 5 export requests per hour per user

## Pagination

All list endpoints support pagination:

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/patients/?page=3",
  "previous": "http://localhost:8000/api/patients/?page=1",
  "results": [ ... ]
}
```

---

*For more detailed examples and integration guides, see the [User Guides](../user-guides/README.md).*