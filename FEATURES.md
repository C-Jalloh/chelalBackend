# Real-time Notifications (WebSocket)
ws://<your-domain>/ws/notifications/<user_id>/
- Connect to this endpoint to receive real-time notifications for a user.
- Notifications are sent as JSON messages.

# Data Export
GET /api/patients/export/?format=csv
- Exports all patient data as CSV. Requires authentication and proper permissions.

# Internationalization (i18n) & Localization (l10n)
- All user-facing strings are marked for translation.
- Supported languages: English, French, Swahili.
- To add translations: run `django-admin makemessages -l <lang>` and `django-admin compilemessages`.

# Offline Sync (Field-level Conflict Resolution)
POST /api/sync_offline_data/
- Batch upserts with field-level merging for patient data.
- Only fields with newer `updated_at` are updated.

# Drug Allergy & Interaction Checks
POST /api/prescriptions/check_drug_allergy/
- Checks for allergies using RxNorm and string matching.
POST /api/prescriptions/check_drug_interaction/
- Checks for drug-drug interactions using RxNorm.

# WebSocket Usage Example
- See `core/consumers.py` for NotificationConsumer usage.
- To send a notification from backend: `await NotificationConsumer.notify_user(user_id, {...})`

# Permissions
- All endpoints are protected by role-based access control.

# Testing
- Automated tests for all features in `core/tests.py`.
