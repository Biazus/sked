from dateutil.utils import today
from rest_framework import serializers
from .models import Company, Service


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = ('id', 'name')

class ServiceSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()
    class Meta:
        model = Service
        fields = ('id', 'name', 'available')

    def get_available(self, obj):
        return True  # TODO get available slots for that day