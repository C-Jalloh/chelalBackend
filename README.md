# Chelal Hospital Management System Backend

## API Endpoints

### Authentication

- `POST /api/auth/` — Obtain JWT token
- `POST /api/auth/refresh/` — Refresh JWT token

### Patients

- `GET /api/patients/` — List patients
- `POST /api/patients/` — Create patient
- `GET /api/patients/{id}/` — Retrieve patient
- `PUT/PATCH /api/patients/{id}/` — Update patient
- `DELETE /api/patients/{id}/` — Delete patient

### Appointments

- `GET /api/appointments/` — List appointments (filter by patient, doctor, date)
- `POST /api/appointments/` — Create appointment
- `GET /api/appointments/{id}/` — Retrieve appointment
- `PUT/PATCH /api/appointments/{id}/` — Update appointment
- `DELETE /api/appointments/{id}/` — Delete appointment

### Encounters

- `GET /api/encounters/` — List encounters
- `POST /api/encounters/` — Create encounter
- `GET /api/encounters/{id}/` — Retrieve encounter
- `PUT/PATCH /api/encounters/{id}/` — Update encounter
- `DELETE /api/encounters/{id}/` — Delete encounter

### Prescriptions

- `GET /api/prescriptions/` — List prescriptions
- `POST /api/prescriptions/` — Create prescription
- `GET /api/prescriptions/{id}/` — Retrieve prescription
- `PUT/PATCH /api/prescriptions/{id}/` — Update prescription
- `DELETE /api/prescriptions/{id}/` — Delete prescription
- `POST /api/prescriptions/check_drug_allergy/` — Check for drug allergy (fields: patient_id, medication_name)

### Offline Sync

- `POST /api/sync_offline_data/` — Sync offline data (batch upserts, conflict resolution: last write wins)

### Reporting

- `GET /api/report/patient_count/` — Get total patient count
- `GET /api/report/appointments_today/` — Get today's appointments
- `GET /api/report/appointments_by_doctor/` — Get appointment counts grouped by doctor
- `GET /api/report/top_prescribed_medications/` — Get top prescribed medications

### Inventory

- `GET /api/inventory/` — List inventory items
- `POST /api/inventory/` — Add new inventory item
- `GET /api/inventory/{id}/` — Retrieve inventory item
- `PUT/PATCH /api/inventory/{id}/` — Update inventory item
- `DELETE /api/inventory/{id}/` — Delete inventory item
- `GET /api/prescriptions/available_medicines/` — List available medicines (quantity > 0)

## Advanced Clinical & Document Management Endpoints

### Vitals
- `POST /api/encounters/{id}/vitals/` — Add vital signs for an encounter
- `GET /api/encounters/{id}/vitals/` — List vitals for an encounter
- `GET /api/patients/{id}/vitals_history/` — List all vitals for a patient

### Medical History
- `POST /api/patients/{id}/medical_conditions/` — Add a chronic condition or past illness
- `GET|POST /api/patients/{id}/medical_conditions/` — List or add medical conditions
- `POST /api/patients/{id}/surgical_history/` — Add past surgeries
- `GET|POST /api/patients/{id}/surgical_history/` — List or add surgical history
- `POST /api/patients/{id}/family_history/` — Add relevant family medical history
- `GET|POST /api/patients/{id}/family_history/` — List or add family history

### Vaccination Records
- `POST /api/patients/{id}/vaccinations/` — Add a vaccination record
- `GET|POST /api/patients/{id}/vaccinations/` — List or add vaccinations

### Lab Orders
- `POST /api/encounters/{id}/lab_orders/` — Create a lab test order
- `GET /api/lab_orders/{order_id}/` — Retrieve lab order
- `PUT /api/lab_orders/{order_id}/results/` — Add results

### Document Management
- `POST /api/patients/{id}/documents/` — Upload a document related to a patient
- `GET|POST /api/patients/{id}/documents/` — List or add patient documents
- `GET /api/documents/{doc_id}/` — Download a document

- All endpoints require authentication and are permission-protected.
- File uploads require Django media configuration (see Django docs for MEDIA_ROOT and MEDIA_URL).

## Permissions

- Role-based access control (Admin, Doctor, Receptionist) enforced on all endpoints.

## Business Logic

- Drug allergy check: Alerts if prescribed medication matches known allergies.
- Sync: Batch upserts with basic conflict resolution (last write wins by updated_at).
- Appointment filtering: By patient, doctor, or date for reporting.
- Reporting: Patient count, today's appointments, appointments by doctor, top medications.

## Inventory Logic

- Pharmacists can manage inventory (CRUD).
- Doctors and pharmacists can view available medicines before prescribing.
- When prescribing, the frontend should call `/api/prescriptions/available_medicines/` to show up-to-date stock.

## Testing

- Automated tests for patient, encounter, prescription, sync, and allergy logic in `core/tests.py`.

## Requirements

- Python 3.8+
- Django 4.x
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure your PostgreSQL database in `Backend/settings.py`.
4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

## Docker

A `Dockerfile` and `docker-compose.yml` will be provided for containerized deployment.

## Docker Usage

### Build and Run with Docker Compose

```bash
docker-compose up --build
```

- The backend will be available at `http://localhost:8000/`
- The PostgreSQL database will be available at `localhost:5432` (internal to Docker network as `db:5432`)

### Environment Variables
- Database settings are configured in `docker-compose.yml` and should match your `Backend/settings.py`.

### Stopping and Removing Containers
```bash
docker-compose down
```

### Running Migrations in Docker
```bash
docker-compose run web python manage.py migrate
```

### Creating a Superuser in Docker
```bash
docker-compose run web python manage.py createsuperuser
```

## License

MIT



<!-- sudo -u postgres psql -c "CREATE USER chelal_user WITH PASSWORD 'chelal_password';" && sudo -u postgres psql -c "CREATE DATABASE chelal_db OWNER chelal_user;" && sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE chelal_db TO chelal_user;"
CREATE ROLE
CREATE DATABASE
GRANT -->