from rest_framework import serializers
from .models import Tour

class TourSerializer(serializers.ModelSerializer):
    model = Tour
    fields = '__all__'