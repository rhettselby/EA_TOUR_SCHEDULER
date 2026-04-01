from django.db import migrations, models
import json

def convert_guest_name_to_list(apps, schema_editor):
    Tour = apps.get_model('tours', 'Tour')
    for tour in Tour.objects.all():
        if tour.guest_name:
            # Wrap existing string value in a list
            tour.guest_name = json.dumps([tour.guest_name])
        else:
            tour.guest_name = json.dumps([])
        tour.save()

class Migration(migrations.Migration):

    dependencies = [
    ('tours', '0008_alter_tour_status'),
]

    operations = [
        # Step 1: convert existing string data to JSON strings in the old column
        migrations.RunPython(convert_guest_name_to_list, reverse_code=migrations.RunPython.noop),
        # Step 2: change the column type to JSONField
        migrations.AlterField(
            model_name='tour',
            name='guest_name',
            field=models.JSONField(default=list, blank=True, null=True),
        ),
    ]