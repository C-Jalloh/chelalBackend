# Quick Start Guide - Chelal Hospital Management System

## Overview

This guide will help you get the Chelal HMS up and running quickly using Docker. You'll have a fully functional hospital management system in under 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- 4GB+ RAM available
- Internet connection for downloading dependencies

## Quick Setup (5 Minutes)

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/C-Jalloh/chelalBackend.git
cd chelalBackend

# Copy environment configuration
cp .env.example .env
```

### 2. Start the System
```bash
# Build and start all services
docker-compose up -d --build

# Wait for services to start (about 30 seconds)
docker-compose logs -f web
```

### 3. Initialize Database
```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py createsuperuser
```

### 4. Access the System
- **API Base**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/ (if enabled)

## First Steps Tutorial

### Step 1: Login and Get Access Token

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-admin-email@example.com",
    "password": "your-admin-password"
  }'
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "Admin"
  }
}
```

**Save the access token** - you'll need it for all API requests.

### Step 2: Create Your First Patient

```bash
curl -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "unique_id": "P001",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-15",
    "gender": "Male",
    "contact_info": "+2207834351",
    "address": "123 Main St, Banjul",
    "known_allergies": "None",
    "emergency_contact": "+2207834352"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "unique_id": "P001",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "gender": "Male",
  "contact_info": "+2207834351",
  "address": "123 Main St, Banjul",
  "known_allergies": "None",
  "emergency_contact": "+2207834352",
  "created_at": "2024-09-17T10:30:00Z",
  "updated_at": "2024-09-17T10:30:00Z"
}
```

### Step 3: Create a Doctor User

First, access the Django admin panel to create user roles and a doctor user:

1. Go to http://localhost:8000/admin/
2. Login with your superuser credentials
3. Click on "Roles" and create a new role:
   - Name: "Doctor"
   - Description: "Medical Doctor"
4. Click on "Users" and create a new user:
   - Email: doctor@hospital.com
   - First name: Dr. Jane
   - Last name: Smith
   - Role: Doctor (select from dropdown)
   - Is active: checked

### Step 4: Schedule an Appointment

```bash
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient": 1,
    "doctor": 2,
    "date": "2024-09-25",
    "time": "10:00:00",
    "appointment_type": "Consultation",
    "notes": "Regular checkup appointment"
  }'
```

### Step 5: Create a Clinical Encounter

```bash
curl -X POST http://localhost:8000/api/encounters/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient": 1,
    "doctor": 2,
    "encounter_type": "Consultation",
    "chief_complaint": "Annual physical exam",
    "history_present_illness": "Patient feels well, no acute complaints",
    "physical_examination": "Vital signs stable, no abnormalities noted",
    "assessment": "Healthy adult",
    "plan": "Continue current lifestyle, return in 1 year"
  }'
```

### Step 6: Add Patient Vitals

```bash
curl -X POST http://localhost:8000/api/vitals/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encounter": 1,
    "temperature": 98.6,
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "heart_rate": 72,
    "respiratory_rate": 16,
    "weight": 75.5,
    "height": 180,
    "bmi": 23.3
  }'
```

## Exploring the Admin Interface

### 1. Access Admin Panel
Navigate to http://localhost:8000/admin/ and login with your superuser credentials.

### 2. Key Admin Sections

#### User Management
- **Users**: Manage system users (doctors, nurses, admin staff)
- **Roles**: Define user roles and permissions
- **Groups**: Organize users into groups

#### Patient Management
- **Patients**: View and edit patient records
- **Appointments**: Manage appointment schedules
- **Encounters**: Review clinical encounters
- **Prescriptions**: Manage medication prescriptions

#### Clinical Data
- **Vitals**: Patient vital signs
- **Lab Orders**: Laboratory test orders and results
- **Medical Conditions**: Patient chronic conditions
- **Vaccination Records**: Immunization history

#### Pharmacy Management
- **Medication Items**: Medication catalog
- **Stock Batches**: Inventory management
- **Purchase Orders**: Procurement management
- **Dispensing Logs**: Medication dispensing records

#### Billing
- **Bills**: Patient billing records
- **Payments**: Payment transactions
- **Service Catalog**: Billable services
- **Insurance Details**: Insurance information

## Common Tasks

### Creating Sample Data

Use the Django admin to create sample data for testing:

1. **Create Roles**:
   - Doctor
   - Nurse
   - Pharmacist
   - Receptionist
   - Admin

2. **Create Users** for each role

3. **Create Patients** (at least 5-10 for testing)

4. **Create Service Catalog** entries:
   - Consultation: $50
   - Blood Test: $25
   - X-Ray: $75
   - Prescription Fee: $10

5. **Create Medication Items**:
   - Paracetamol 500mg
   - Amoxicillin 250mg
   - Ibuprofen 400mg

### Testing API Endpoints

#### List All Patients
```bash
curl -X GET http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Get Specific Patient
```bash
curl -X GET http://localhost:8000/api/patients/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### List Patient's Appointments
```bash
curl -X GET http://localhost:8000/api/patients/1/appointments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Create a Lab Order
```bash
curl -X POST http://localhost:8000/api/lab-orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encounter": 1,
    "test_name": "Complete Blood Count",
    "specimen_type": "Blood",
    "urgency": "Routine",
    "instructions": "Fasting not required"
  }'
```

## Testing Background Tasks

### 1. Start Celery Services
```bash
# Start Celery worker (in a new terminal)
docker-compose exec web celery -A Backend worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
docker-compose exec web celery -A Backend beat --loglevel=info
```

### 2. Test Appointment Reminders
```bash
# Trigger appointment reminders manually
docker-compose exec web python manage.py send_appointment_reminders --hours 24
```

## Real-time Features

### WebSocket Notifications

Test real-time notifications using a WebSocket client:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/notifications/1/');

ws.onopen = function(event) {
    console.log('Connected to notifications');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Notification received:', data);
};
```

## Data Export Testing

### Export Patient Data
```bash
curl -X GET "http://localhost:8000/api/patients/export/?format=csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o patients.csv
```

### Export Appointment Data
```bash
curl -X GET "http://localhost:8000/api/appointments/export/?format=csv&date_from=2024-09-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o appointments.csv
```

## Performance Testing

### Load Testing with Apache Bench
```bash
# Test login endpoint
ab -n 100 -c 10 -p login_data.json -T application/json http://localhost:8000/api/auth/login/

# Test patient list endpoint (requires valid token in headers)
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/patients/
```

## Troubleshooting Quick Issues

### Services Not Starting
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs web
docker-compose logs db
docker-compose logs redis
```

### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

### Port Conflicts
If port 8000 is in use, modify `docker-compose.yml`:
```yaml
services:
  web:
    ports:
      - "8001:8000"  # Change to port 8001
```

### Clear Cache Issues
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

## Next Steps

After completing this quick start:

1. **Explore the [API Documentation](../api/README.md)** for complete endpoint reference
2. **Read the [User Guides](../user-guides/README.md)** for detailed usage instructions
3. **Review [Security Configuration](../security/README.md)** before production deployment
4. **Set up [Monitoring](../deployment/monitoring.md)** for production environments
5. **Configure [Backup Procedures](../deployment/backup-recovery.md)** for data protection

## Sample Postman Collection

Import the provided Postman collection `chelal_backend_api.postman_collection.json` for easy API testing:

1. Open Postman
2. Click Import
3. Select the JSON file from the project root
4. Configure environment variables:
   - `base_url`: http://localhost:8000
   - `access_token`: (set after login)

---

**Congratulations!** You now have a working Chelal HMS installation. The system is ready for development, testing, or evaluation.