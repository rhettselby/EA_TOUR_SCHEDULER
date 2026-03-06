from django.core.management.base import BaseCommand
from tours.models import Tour
from datetime import datetime, timezone
import os


class Command(BaseCommand):
    help = 'Backfills week_number for all tours missing it'

    def handle(self, *args, **kwargs):
        quarter_start = os.environ.get('QUARTER_START_DATE')

        if not quarter_start:
            self.stdout.write(self.style.ERROR('QUARTER_START_DATE env variable not set'))
            return

        quarter_start_dt = datetime.strptime(quarter_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        tours = Tour.objects.filter(week_number__isnull=True)
        self.stdout.write(f'Found {tours.count()} tours missing week_number')

        updated = 0
        for tour in tours:
            days = (tour.start_dt - quarter_start_dt).days
            tour.week_number = (days // 7) + 1
            tour.save()
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} tours'))