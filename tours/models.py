from datetime import datetime, timezone
from django.db import models
import os




# Create your models here.

class Tour(models.Model):
    event_id = models.CharField(unique=True, max_length=255)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()
    group_tour = models.BooleanField(default=False)
    guest_name = models.JSONField(default=list, blank=True, null=True)
    week_number = models.PositiveIntegerField(null=True, blank=True)

    STATUS_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('message_sent', 'Message Sent'),
        ('confirmed', 'Confirmed'),
        ('past_event', 'Past Event'),
        ('cancelled', 'Tour Cancelled'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unassigned')


    def __str__(self):
        return f"{self.start_dt} to {self.end_dt}"
    

class Guest(models.Model):
    event_id = models.CharField(unique=True, max_length=255)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    number_of_guests = models.PositiveIntegerField()
    group_tour = models.BooleanField(default=False)
    guest_name = models.CharField()
    week_number = models.PositiveIntegerField(null=True, blank=True)
    tour = models.ForeignKey(Tour, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    past_event = models.BooleanField(default=False)

   


    
    