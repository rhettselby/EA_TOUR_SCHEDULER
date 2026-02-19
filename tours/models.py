from django.db import models

# Create your models here.

class Tour(models.Model):
    event_id = models.CharField(unique=True)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()
    group_tour = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.start_dt} to {self.end_dt}"