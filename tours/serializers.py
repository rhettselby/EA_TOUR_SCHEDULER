from rest_framework import serializers
from .models import Tour, Guest

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ['guest_name', 'contact_name', 'group_name', 'cell_number', 'purpose_of_visit', 'major_of_interest', 'questions_comments']

class TourSerializer(serializers.ModelSerializer):
    guests = GuestSerializer(many=True, read_only=True, source='guest_set')

    class Meta:
        model = Tour
        fields = '__all__'