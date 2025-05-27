from django.core.management.base import BaseCommand
from core.views import schedule_upcoming_appointment_reminders

class Command(BaseCommand):
    help = 'Manually trigger appointment SMS reminders for upcoming appointments.'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='How many hours before appointment to send reminders (default: 24)')

    def handle(self, *args, **options):
        hours = options['hours']
        self.stdout.write(self.style.NOTICE(f'Scheduling reminders for appointments {hours} hours in advance...'))
        schedule_upcoming_appointment_reminders(hours_before=hours)
        self.stdout.write(self.style.SUCCESS('Reminders scheduled (tasks dispatched to Celery).'))
