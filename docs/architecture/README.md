# System Architecture - Chelal Hospital Management System

## Architecture Overview

The Chelal HMS follows a modern, layered architecture designed for scalability, maintainability, and security. The system is built using Django REST Framework with a focus on API-first design principles.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Web Frontend  │    │  Mobile Apps    │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       API Gateway       │
                    │   (CORS, Rate Limiting) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Django REST API       │
                    │  (Authentication &      │
                    │   Business Logic)       │
                    └────────────┬────────────┘
                                 │
        ┌────────────┬───────────┼───────────┬────────────┐
        │            │           │           │            │
┌───────▼──────┐ ┌───▼────┐ ┌────▼────┐ ┌───▼────┐ ┌─────▼─────┐
│ PostgreSQL   │ │ Redis  │ │ Celery  │ │ WebSocket│ │  File     │
│ Database     │ │ Cache  │ │ Tasks   │ │ Real-time│ │  Storage  │
└──────────────┘ └────────┘ └─────────┘ └────────┘ └───────────┘
```

## Application Layers

### 1. Presentation Layer
**Location**: External client applications
**Responsibility**: User interface and user experience
**Technologies**: Web browsers, mobile apps, third-party integrations

### 2. API Layer
**Location**: `core/urls.py`, `core/views.py`
**Responsibility**: HTTP request handling, API routing, response formatting
**Components**:
- RESTful endpoints
- Request/response serialization
- API versioning
- CORS handling

### 3. Business Logic Layer
**Location**: `core/views.py`, `core/serializers.py`, `core/services/`
**Responsibility**: Core business rules and domain logic
**Components**:
- Service classes
- Validation logic
- Business rule enforcement
- Data transformation

### 4. Data Access Layer
**Location**: `core/models.py`, Django ORM
**Responsibility**: Data persistence and retrieval
**Components**:
- Django models
- Database queries
- Data relationships
- Migration management

### 5. Infrastructure Layer
**Location**: Settings, configuration files
**Responsibility**: Cross-cutting concerns
**Components**:
- Authentication/Authorization
- Logging and monitoring
- Caching
- Background tasks

## Core Components

### Authentication & Authorization

```python
# Authentication Flow
Client Request → JWT Token Validation → Permission Check → API Access
```

**Components**:
- `core/auth_backends.py`: Custom authentication backends
- `core/permissions.py`: Role-based permission classes
- JWT token management
- Session handling

**Security Features**:
- Token-based authentication
- Role-based access control (RBAC)
- Permission granularity
- Session management
- Brute-force protection

### Data Models

**Core Entities**:
```
User ←→ Role
  ↓
Patient ←→ Appointment ←→ Doctor (User)
  ↓           ↓
Encounter ←→ Prescription
  ↓           ↓
Vitals    Medication
  ↓
LabOrder ←→ LabResults
```

**Key Relationships**:
- One-to-Many: Patient → Appointments
- Many-to-Many: User → Roles
- Foreign Keys: Prescription → Encounter
- Self-referencing: User → Supervisor

### API Design Patterns

**RESTful Conventions**:
```
GET    /api/patients/           # List patients
POST   /api/patients/           # Create patient
GET    /api/patients/{id}/      # Get specific patient
PUT    /api/patients/{id}/      # Update patient
DELETE /api/patients/{id}/      # Delete patient
```

**Nested Resources**:
```
GET    /api/patients/{id}/appointments/     # Patient's appointments
POST   /api/patients/{id}/appointments/     # Create appointment for patient
GET    /api/patients/{id}/prescriptions/    # Patient's prescriptions
```

### Background Processing

**Celery Task Architecture**:
```
Django App → Celery Beat (Scheduler) → Redis Queue → Celery Worker → Database
```

**Task Types**:
- Appointment reminders (SMS/Email)
- Report generation
- Data exports
- Notification delivery
- Cleanup operations

### Real-time Communication

**WebSocket Architecture**:
```
Client ←→ Django Channels ←→ Redis Channel Layer ←→ Background Tasks
```

**Use Cases**:
- Real-time notifications
- Live updates
- Chat functionality
- System alerts

## Database Design

### Schema Organization

**Core Tables**:
- `core_user`: User accounts and authentication
- `core_role`: User roles and permissions
- `core_patient`: Patient demographic data
- `core_appointment`: Appointment scheduling
- `core_encounter`: Clinical encounters
- `core_prescription`: Medication prescriptions

**Pharmacy Tables**:
- `core_medicationitem`: Medication catalog
- `core_stockbatch`: Inventory batches
- `core_purchaseorder`: Procurement orders
- `core_dispensinglog`: Medication dispensing

**Billing Tables**:
- `core_servicecatalog`: Billable services
- `core_bill`: Patient bills
- `core_payment`: Payment transactions
- `core_insurancedetail`: Insurance information

### Database Relationships

**Foreign Key Constraints**:
- Ensure referential integrity
- Cascade delete where appropriate
- Protect critical data relationships

**Indexing Strategy**:
```sql
-- Performance indexes
CREATE INDEX idx_patient_unique_id ON core_patient(unique_id);
CREATE INDEX idx_appointment_date ON core_appointment(date, time);
CREATE INDEX idx_encounter_patient ON core_encounter(patient_id);
```

## Security Architecture

### Authentication Flow

```
1. Client Login → Username/Password
2. Django Authentication → User Validation
3. JWT Token Generation → Signed Token
4. Client Storage → Secure Storage
5. API Requests → Token in Header
6. Token Validation → Signature Verification
7. Permission Check → Role-based Access
8. API Response → Authorized Data
```

### Data Protection

**Encryption**:
- Database encryption at rest
- HTTPS for data in transit
- Sensitive field encryption
- JWT token signing

**Access Control**:
- Role-based permissions
- Object-level permissions
- Field-level access control
- API rate limiting

### Audit Trail

**Logging Components**:
- `core/models.py`: AuditLog model
- `core/signals.py`: Automatic logging triggers
- Request/response logging
- User action tracking

## Performance Considerations

### Caching Strategy

**Redis Caching**:
```python
# Cache frequently accessed data
cache.set('patient_list', patients, timeout=300)
cache.set(f'user_permissions_{user_id}', permissions, timeout=1800)
```

**Database Optimization**:
- Query optimization with `select_related()`
- Prefetch related objects
- Database connection pooling
- Query result caching

### Scalability Patterns

**Horizontal Scaling**:
- Stateless application design
- Load balancer ready
- Database connection pooling
- Background task distribution

**Vertical Scaling**:
- Efficient memory usage
- Optimized database queries
- Proper indexing
- Resource monitoring

## Integration Patterns

### External Service Integration

**Third-party Services**:
- Twilio for SMS notifications
- Email services for notifications
- Payment gateways for billing
- Laboratory information systems

**API Integration**:
```python
# Example external API call
def send_sms_notification(phone, message):
    twilio_client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone
    )
```

### Data Import/Export

**Bulk Operations**:
- CSV import/export
- JSON data exchange
- Database migrations
- Data synchronization

## Deployment Architecture

### Development Environment
```
Developer Machine → Git Repository → Local Testing
```

### Production Environment
```
Git Repository → CI/CD Pipeline → Docker Container → Production Server
```

**Infrastructure Components**:
- Docker containers for application
- PostgreSQL database server
- Redis cache server
- Nginx reverse proxy
- SSL certificate management

## Monitoring & Observability

### Logging Strategy
- Application logs: Django logging framework
- Access logs: Nginx/Apache logs
- Error logs: Sentry/custom error handling
- Audit logs: Custom audit model

### Health Checks
```python
# Health check endpoints
GET /health/          # Basic health check
GET /health/database/ # Database connectivity
GET /health/cache/    # Cache availability
GET /health/celery/   # Background task health
```

### Performance Monitoring
- Database query performance
- API response times
- Memory and CPU usage
- Background task completion rates

---

*For implementation details, see the [Development Guide](../development/README.md) and [API Reference](../api/README.md).*