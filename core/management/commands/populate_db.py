import os
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chelal_backend_api.settings')
django.setup()

from core.models import *

fake = Faker()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Starting database population...')

        # Create roles first
        self.create_roles()

        # Create users for all roles
        self.create_users()

        # Create organizations
        self.create_organizations()

        # Create patients
        self.create_patients()

        # Create medical data
        self.create_medical_data()

        # Create inventory and pharmacy data
        self.create_inventory_data()

        # Create billing data
        self.create_billing_data()

        # Create appointments and encounters
        self.create_appointments_encounters()

        # Create notifications and tasks
        self.create_notifications_tasks()

        # Create audit logs
        self.create_audit_logs()

        self.stdout.write(self.style.SUCCESS('Database population completed!'))

    def create_roles(self):
        roles_data = [
            ('admin', 'Administrator role'),
            ('receptionist', 'Receptionist role'),
            ('NURSE', 'Nurse role'),
            ('PHARMACIST', 'Pharmacist role'),
            ('DOCTOR', 'Doctor role'),
            ('PATIENT', 'Patient role'),
            ('defaultuser', 'Default user role'),
        ]

        for name, description in roles_data:
            Role.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )

        self.stdout.write('Created roles')

    def create_users(self):
        roles = Role.objects.all()

        # Create users for each role (at least 5 per role)
        for role in roles:
            for i in range(5):
                username = f"{role.name.lower()}_{i+1}"
                email = f"{username}@example.com"

                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': fake.first_name(),
                        'last_name': fake.last_name(),
                        'role': role,
                        'is_staff': role.name in ['admin', 'DOCTOR'],
                        'is_superuser': role.name == 'admin',
                    }
                )

                if created:
                    user.set_password('password123')
                    user.save()

        # Create 5 additional defaultusers
        default_role = Role.objects.get(name='defaultuser')
        for i in range(5):
            username = f"defaultuser_extra_{i+1}"
            email = f"{username}@example.com"

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': default_role,
                }
            )

            if created:
                user.set_password('password123')
                user.save()

        self.stdout.write('Created users')

    def create_organizations(self):
        for _ in range(25):
            Organization.objects.get_or_create(
                name=fake.company(),
                defaults={
                    'address': fake.address(),
                    'contact_email': fake.email(),
                    'is_active': random.choice([True, False]),
                }
            )

        # Assign users to organizations
        users = User.objects.all()
        organizations = Organization.objects.all()

        for user in users:
            if random.choice([True, False]):
                org = random.choice(list(organizations))
                OrganizationMembership.objects.get_or_create(
                    user=user,
                    organization=org,
                    defaults={
                        'role': user.role.name if user.role else 'Member',
                        'is_active': True,
                    }
                )

        self.stdout.write('Created organizations and memberships')

    def create_patients(self):
        for _ in range(50):
            patient, created = Patient.objects.get_or_create(
                unique_id=fake.unique.bothify(text='????####'),
                defaults={
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'date_of_birth': fake.date_of_birth(minimum_age=1, maximum_age=90),
                    'gender': random.choice(['Male', 'Female', 'Other']),
                    'contact_info': fake.phone_number(),
                    'address': fake.address(),
                    'known_allergies': fake.sentence() if random.choice([True, False]) else '',
                }
            )

        self.stdout.write('Created patients')

    def create_medical_data(self):
        patients = Patient.objects.all()
        doctors = User.objects.filter(role__name='DOCTOR')

        # Medical Conditions
        for _ in range(100):
            MedicalCondition.objects.get_or_create(
                patient=random.choice(list(patients)),
                name=fake.sentence(nb_words=3),
                defaults={
                    'notes': fake.text(max_nb_chars=500),
                    'diagnosed_at': fake.date_this_decade(),
                }
            )

        # Surgical History
        for _ in range(80):
            SurgicalHistory.objects.get_or_create(
                patient=random.choice(list(patients)),
                procedure=fake.sentence(nb_words=4),
                defaults={
                    'notes': fake.text(max_nb_chars=700),
                    'date': fake.date_this_decade(),
                }
            )

        # Family History
        for _ in range(120):
            FamilyHistory.objects.get_or_create(
                patient=random.choice(list(patients)),
                relation=random.choice(['Father', 'Mother', 'Brother', 'Sister', 'Grandfather', 'Grandmother']),
                condition=fake.sentence(nb_words=2),
                defaults={
                    'notes': fake.text(max_nb_chars=100),
                }
            )

        # Vaccinations
        vaccines = ['COVID-19', 'Flu', 'Hepatitis B', 'MMR', 'DTaP', 'Polio', 'Chickenpox']
        for _ in range(200):
            Vaccination.objects.get_or_create(
                patient=random.choice(list(patients)),
                vaccine_name=random.choice(vaccines),
                defaults={
                    'date_administered': fake.date_this_decade(),
                    'dose_number': random.choice(['1', '2', '3', 'Booster']),
                    'administered_by': fake.name(),
                }
            )

        # Insurance Details
        for _ in range(60):
            InsuranceDetail.objects.get_or_create(
                patient=random.choice(list(patients)),
                provider=fake.company(),
                policy_number=fake.bothify(text='POL-########'),
                defaults={
                    'coverage_details': fake.text(max_nb_chars=300),
                    'valid_until': fake.future_date(),
                }
            )

        # Consents
        for _ in range(150):
            Consent.objects.get_or_create(
                patient=random.choice(list(patients)),
                consent_type=random.choice(['treatment', 'data_processing', 'research']),
                defaults={
                    'given': random.choice([True, False]),
                    'notes': fake.text(max_nb_chars=100),
                    'created_by': random.choice(list(User.objects.all())),
                }
            )

        # Referrals
        for _ in range(40):
            Referral.objects.get_or_create(
                patient=random.choice(list(patients)),
                referring_doctor_details=fake.name(),
                referred_to_doctor_details=fake.name(),
                reason_for_referral=fake.text(max_nb_chars=200),
                defaults={
                    'status': random.choice(['Pending', 'Accepted', 'Declined', 'Completed']),
                }
            )

        self.stdout.write('Created medical data')

    def create_inventory_data(self):
        # Suppliers
        for _ in range(30):
            Supplier.objects.get_or_create(
                name=fake.company(),
                defaults={
                    'contact_person': fake.name(),
                    'phone': fake.phone_number(),
                    'email': fake.email(),
                    'address': fake.address(),
                }
            )

        # Medication Categories
        categories = ['Antibiotics', 'Pain Relief', 'Cardiovascular', 'Diabetes', 'Respiratory', 'Mental Health']
        for cat in categories:
            MedicationCategory.objects.get_or_create(name=cat)

        # Medication Items
        suppliers = Supplier.objects.all()
        categories = MedicationCategory.objects.all()

        for _ in range(100):
            MedicationItem.objects.get_or_create(
                generic_name=fake.sentence(nb_words=2),
                defaults={
                    'brand_name': fake.company(),
                    'formulation': random.choice(['Tablet', 'Syrup', 'Injection', 'Capsule', 'Other']),
                    'strength': f"{random.randint(1, 1000)}mg",
                    'manufacturer': fake.company(),
                    'supplier': random.choice(list(suppliers)),
                    'category': random.choice(list(categories)),
                    'unit_of_measure': random.choice(['Box', 'Bottle', 'Vial', 'Pack']),
                    'reorder_level': random.randint(10, 100),
                    'reorder_quantity': random.randint(50, 200),
                    'storage_conditions': fake.sentence(),
                    'is_controlled_substance': random.choice([True, False]),
                    'total_quantity': random.randint(0, 1000),
                    'description': fake.text(max_nb_chars=200),
                }
            )

        # Stock Batches
        medications = MedicationItem.objects.all()
        for _ in range(200):
            med = random.choice(list(medications))
            StockBatch.objects.get_or_create(
                medication_item=med,
                batch_number=fake.bothify(text='BAT-########'),
                defaults={
                    'expiry_date': fake.future_date(),
                    'quantity_received': random.randint(50, 500),
                    'current_quantity': random.randint(0, 500),
                    'cost_price_per_unit': Decimal(str(random.uniform(1, 50))),
                    'selling_price_per_unit': Decimal(str(random.uniform(2, 75))),
                }
            )

        # Inventory Items
        for _ in range(80):
            InventoryItem.objects.get_or_create(
                name=fake.sentence(nb_words=3),
                defaults={
                    'description': fake.text(max_nb_chars=150),
                    'quantity': random.randint(0, 200),
                    'unit': random.choice(['pieces', 'boxes', 'kits', 'sets']),
                }
            )

        # Service Catalog
        services = [
            'General Consultation', 'Specialist Consultation', 'Emergency Care',
            'Surgery', 'Laboratory Test', 'X-Ray', 'MRI', 'Ultrasound',
            'Physical Therapy', 'Dental Care', 'Eye Care', 'Vaccination'
        ]

        for service in services:
            ServiceCatalog.objects.get_or_create(
                name=service,
                defaults={
                    'description': fake.text(max_nb_chars=100),
                    'price': Decimal(str(random.uniform(50, 1000))),
                    'is_active': True,
                }
            )

        self.stdout.write('Created inventory and pharmacy data')

    def create_billing_data(self):
        patients = Patient.objects.all()
        services = ServiceCatalog.objects.all()

        # Bills
        for _ in range(150):
            patient = random.choice(list(patients))
            bill = Bill.objects.create(
                patient=patient,
                total_amount=Decimal('0'),
                is_paid=random.choice([True, False]),
            )

            # Bill Items
            total = Decimal('0')
            for _ in range(random.randint(1, 5)):
                service = random.choice(list(services))
                quantity = random.randint(1, 3)
                amount = service.price * quantity
                total += amount

                BillItem.objects.create(
                    bill=bill,
                    service=service,
                    description=f"{service.name} x{quantity}",
                    amount=amount,
                    quantity=quantity,
                )

            bill.total_amount = total
            bill.save()

            # Payments for paid bills
            if bill.is_paid:
                Payment.objects.create(
                    bill=bill,
                    amount=bill.total_amount,
                    method=random.choice(['Cash', 'Card', 'Insurance']),
                    reference=fake.bothify(text='PAY-########'),
                    received_by=random.choice(list(User.objects.all())),
                )

        self.stdout.write('Created billing data')

    def create_appointments_encounters(self):
        patients = Patient.objects.all()
        doctors = User.objects.filter(role__name='DOCTOR')

        # Appointments
        for _ in range(200):
            patient = random.choice(list(patients))
            doctor = random.choice(list(doctors))

            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=fake.date_this_year(),
                time=fake.time(),
                status=random.choice(['scheduled', 'completed', 'cancelled']),
            )

            # Encounters for completed appointments
            if appointment.status == 'completed':
                encounter = Encounter.objects.create(
                    patient=patient,
                    appointment=appointment,
                    doctor=doctor,
                    notes=fake.text(max_nb_chars=300),
                    diagnosis=fake.sentence(),
                )

                # Vitals for encounters
                Vitals.objects.create(
                    encounter=encounter,
                    systolic_bp=random.randint(90, 180),
                    diastolic_bp=random.randint(60, 120),
                    heart_rate=random.randint(60, 100),
                    respiratory_rate=random.randint(12, 20),
                    temperature=round(random.uniform(36.0, 40.0), 1),
                    oxygen_saturation=random.randint(95, 100),
                    height=random.uniform(150, 200),
                    weight=random.uniform(50, 120),
                )

                # Prescriptions
                for _ in range(random.randint(0, 3)):
                    Prescription.objects.create(
                        encounter=encounter,
                        medication_name=fake.sentence(nb_words=2),
                        dosage=f"{random.randint(1, 4)} x {random.randint(1, 3)} daily",
                        frequency=f"{random.randint(1, 4)} times daily",
                    )

                # Lab Orders
                if random.choice([True, False]):
                    lab_order = LabOrder.objects.create(
                        encounter=encounter,
                        test_name=fake.sentence(nb_words=2),
                        specimen_type=random.choice(['Blood', 'Urine', 'Saliva', 'Tissue']),
                        status=random.choice(['Ordered', 'Completed', 'Pending']),
                    )

        # Wards and Beds
        for _ in range(20):
            ward = Ward.objects.create(
                name=f"Ward {fake.word().capitalize()} {random.randint(1, 10)}",
                description=fake.text(max_nb_chars=100),
                capacity=random.randint(10, 50),
            )

            # Beds for each ward
            for bed_num in range(1, ward.capacity + 1):
                Bed.objects.get_or_create(
                    ward=ward,
                    number=str(bed_num),
                    defaults={
                        'status': random.choice(['available', 'occupied', 'cleaning', 'maintenance']),
                    }
                )

        # Assign patients to beds
        occupied_beds = Bed.objects.filter(status='occupied')
        for bed in occupied_beds:
            if random.choice([True, False]):
                bed.assigned_patient = random.choice(list(patients))
                bed.last_assigned = fake.date_this_month()
                bed.save()

        # Schedulable Resources
        for _ in range(25):
            SchedulableResource.objects.create(
                name=f"{fake.word().capitalize()} {random.choice(['Room', 'Equipment', 'Lab'])} {random.randint(1, 20)}",
                resource_type=random.choice(['Operating Room', 'Equipment', 'Other']),
                description=fake.text(max_nb_chars=100),
                is_active=random.choice([True, False]),
            )

        # Resource Bookings
        resources = SchedulableResource.objects.all()
        for _ in range(50):
            resource = random.choice(list(resources))
            start_time = fake.date_time_this_year()
            end_time = start_time + timedelta(hours=random.randint(1, 8))

            ResourceBooking.objects.create(
                resource=resource,
                booked_by=random.choice(list(User.objects.all())),
                patient=random.choice(list(patients)) if random.choice([True, False]) else None,
                start_time=start_time,
                end_time=end_time,
                purpose=fake.sentence(),
                status=random.choice(['Scheduled', 'Completed', 'Cancelled']),
            )

        # Telemedicine Sessions
        appointments = Appointment.objects.filter(status='completed').exclude(telemedicine_session__isnull=False)
        for appointment in appointments[:30]:  # Create telemedicine for some appointments
            TelemedicineSession.objects.create(
                appointment=appointment,
                scheduled_start=fake.date_time_this_year(),
                scheduled_end=fake.date_time_this_year(),
                video_room_id=fake.uuid4(),
                join_url_doctor=fake.url(),
                join_url_patient=fake.url(),
                is_active=random.choice([True, False]),
            )

        self.stdout.write('Created appointments and encounters')

    def create_notifications_tasks(self):
        users = User.objects.all()
        patients = Patient.objects.all()

        # Notifications
        for _ in range(300):
            Notification.objects.create(
                user=random.choice(list(users)),
                message=fake.text(max_nb_chars=150),
                type=random.choice(['info', 'warning', 'success', 'error']) if random.choice([True, False]) else '',
                is_read=random.choice([True, False]),
            )

        # Tasks
        for _ in range(150):
            Task.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.text(max_nb_chars=200),
                assignee=random.choice(list(users)) if random.choice([True, False]) else None,
                status=random.choice(['pending', 'in_progress', 'completed', 'cancelled']),
                related_patient=random.choice(list(patients)) if random.choice([True, False]) else None,
                due_date=fake.future_date() if random.choice([True, False]) else None,
                created_by=random.choice(list(users)),
            )

        # Note Templates
        for _ in range(40):
            NoteTemplate.objects.create(
                title=fake.sentence(nb_words=3),
                content=fake.text(max_nb_chars=500),
                created_by=random.choice(list(users)),
                is_active=random.choice([True, False]),
            )

        # Secure Messages
        for _ in range(100):
            sender = random.choice(list(users))
            recipient = random.choice(list(users.exclude(id=sender.id)))

            SecureMessage.objects.create(
                sender=sender,
                recipient=recipient,
                patient=random.choice(list(patients)) if random.choice([True, False]) else None,
                subject=fake.sentence(nb_words=4),
                message=fake.text(max_nb_chars=300),
                is_read=random.choice([True, False]),
            )

        # Feedback
        for _ in range(80):
            Feedback.objects.create(
                user=random.choice(list(users)) if random.choice([True, False]) else None,
                message=fake.text(max_nb_chars=400),
                contact_email=fake.email() if random.choice([True, False]) else '',
                resolved=random.choice([True, False]),
                resolution_notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
            )

        # Delegate Access
        for _ in range(30):
            user = random.choice(list(users))
            delegate = random.choice(list(users.exclude(id=user.id)))

            DelegateAccess.objects.create(
                user=user,
                delegate=delegate,
                can_manage_schedule=random.choice([True, False]),
                can_view_data=random.choice([True, False]),
                can_act_as_user=random.choice([True, False]),
                revoked=random.choice([True, False]),
            )

        self.stdout.write('Created notifications and tasks')

    def create_audit_logs(self):
        users = User.objects.all()

        # Audit Logs
        for _ in range(500):
            AuditLog.objects.create(
                user=random.choice(list(users)) if random.choice([True, False]) else None,
                action=random.choice(['view', 'edit', 'create', 'delete', 'login', 'logout', 'export', 'session_revoke']),
                object_type=random.choice(['Patient', 'Appointment', 'User', 'Bill', 'Medication', 'LabOrder']) if random.choice([True, False]) else '',
                object_id=str(random.randint(1, 1000)) if random.choice([True, False]) else '',
                description=fake.text(max_nb_chars=200),
                details={'ip': fake.ipv4(), 'user_agent': fake.user_agent()} if random.choice([True, False]) else {},
            )

        # Login Activities
        for _ in range(400):
            LoginActivity.objects.create(
                user=random.choice(list(users)),
                ip_address=fake.ipv4(),
                user_agent=fake.user_agent(),
                status=random.choice(['success', 'failure']),
            )

        # API Keys
        for _ in range(50):
            ApiKey.objects.create(
                user=random.choice(list(users)),
                name=fake.sentence(nb_words=2),
                is_active=random.choice([True, False]),
            )

        # Role Change Requests
        roles = Role.objects.all()
        for _ in range(25):
            user = random.choice(list(users))
            # Exclude the user's current role if they have one
            exclude_ids = [user.role.id] if user.role else []
            requested_role = random.choice(list(roles.exclude(id__in=exclude_ids) if exclude_ids else roles))

            RoleChangeRequest.objects.create(
                user=user,
                requested_role=requested_role,
                reason=fake.text(max_nb_chars=200),
                status=random.choice(['pending', 'approved', 'rejected']),
                admin_response=fake.text(max_nb_chars=150) if random.choice([True, False]) else '',
            )

        # Sync Conflicts and Queue Status
        for _ in range(20):
            SyncConflict.objects.create(
                model_name=random.choice(['Patient', 'Appointment', 'User']),
                record_id=str(random.randint(1, 1000)),
                field=random.choice(['name', 'date', 'status']),
                device_id=fake.uuid4(),
                user=random.choice(list(users)),
                server_value=fake.word(),
                device_value=fake.word(),
                resolved_value=fake.word() if random.choice([True, False]) else '',
                status=random.choice(['pending', 'resolved']),
            )

        for _ in range(15):
            SyncQueueStatus.objects.create(
                device_id=fake.uuid4(),
                user=random.choice(list(users)),
                queue_length=random.randint(0, 100),
                status=random.choice(['idle', 'syncing', 'error']),
                error_message=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
            )

        # Appointment Notifications
        appointments = Appointment.objects.all()
        for appointment in appointments[:50]:
            AppointmentNotification.objects.create(
                appointment=appointment,
                notification_type=random.choice(['reminder', 'followup']),
                channel=random.choice(['sms', 'email']),
                status=random.choice(['pending', 'sent', 'failed']),
                scheduled_for=fake.date_time_this_year(),
                message=fake.text(max_nb_chars=160),
            )

        # Lab Test Catalog and Results
        for _ in range(60):
            test = LabTestCatalog.objects.create(
                test_code=fake.bothify(text='???-###'),
                test_name=fake.sentence(nb_words=3),
                specimen_type=random.choice(['Blood', 'Urine', 'Saliva', 'Stool']),
                department=random.choice(['Hematology', 'Chemistry', 'Microbiology', 'Immunology']),
                critical_range_low=Decimal(str(random.uniform(0, 50))) if random.choice([True, False]) else None,
                critical_range_high=Decimal(str(random.uniform(50, 200))) if random.choice([True, False]) else None,
            )

        # Lab Order Items and Results
        lab_orders = LabOrder.objects.all()
        tests = LabTestCatalog.objects.all()

        for order in lab_orders[:80]:
            for _ in range(random.randint(1, 3)):
                order_item = LabOrderItem.objects.create(
                    lab_order=order,
                    lab_test=random.choice(list(tests)),
                    notes_for_lab=fake.text(max_nb_chars=100) if random.choice([True, False]) else '',
                )

                # Lab Results
                for _ in range(random.randint(1, 5)):
                    LabResultValue.objects.create(
                        lab_order_item=order_item,
                        parameter_name=fake.sentence(nb_words=2),
                        value_numeric=Decimal(str(random.uniform(1, 200))) if random.choice([True, False]) else None,
                        value_text=fake.word() if random.choice([True, False]) else '',
                        units=random.choice(['mg/dL', 'g/L', 'IU/L', 'mmol/L', 'cells/uL']) if random.choice([True, False]) else '',
                        reference_range_low=Decimal(str(random.uniform(0, 50))) if random.choice([True, False]) else None,
                        reference_range_high=Decimal(str(random.uniform(50, 150))) if random.choice([True, False]) else None,
                        abnormal_flag=random.choice(['normal', 'low', 'high', 'critical']),
                        entered_by=random.choice(list(users)),
                    )

        # Purchase Orders and related
        suppliers = Supplier.objects.all()
        medications = MedicationItem.objects.all()

        for _ in range(40):
            supplier = random.choice(list(suppliers))
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                expected_delivery_date=fake.future_date(),
                status=random.choice(['Pending', 'Partially Received', 'Received', 'Cancelled']),
            )

            # PO Items
            for _ in range(random.randint(1, 5)):
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    medication_item=random.choice(list(medications)),
                    quantity_ordered=random.randint(10, 200),
                )

        # Goods Received Notes
        pos = PurchaseOrder.objects.all()
        for po in pos[:25]:
            grn = GoodsReceivedNote.objects.create(
                purchase_order=po,
                supplier=po.supplier,
                invoice_number=fake.bothify(text='INV-########'),
            )

            # GRN Items
            for item in po.items.all():
                GRNItem.objects.create(
                    grn=grn,
                    medication_item=item.medication_item,
                    batch_number=fake.bothify(text='BAT-########'),
                    expiry_date=fake.future_date(),
                    quantity_received=item.quantity_ordered,
                )

        # Dispensing Logs
        prescriptions = Prescription.objects.all()
        batches = StockBatch.objects.all()

        for prescription in prescriptions[:60]:
            DispensingLog.objects.create(
                prescription=prescription,
                stock_batch=random.choice(list(batches)),
                quantity_dispensed=random.randint(1, 10),
                dispensed_by=random.choice(list(users)),
            )

        # Stock Adjustments
        for _ in range(50):
            StockAdjustment.objects.create(
                medication_item=random.choice(list(medications)),
                stock_batch=random.choice(list(batches)) if random.choice([True, False]) else None,
                adjustment_type=random.choice(['Damaged', 'Expired-Discarded', 'Stock-Take Variance', 'Internal Transfer']),
                quantity=random.randint(-50, 50),
                reason=fake.text(max_nb_chars=100),
                adjusted_by=random.choice(list(users)),
            )

        self.stdout.write('Created audit logs and additional data')