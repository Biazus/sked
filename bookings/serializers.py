from dateutil.utils import today
from datetime import datetime
from rest_framework import serializers
from .models import Company, Service, Appointment, WorkingHours


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = "__all__"

class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()
    class Meta:
        model = Service
        fields = "__all__"

    def get_available(self, obj):
        return True  # TODO get available slots for that day

class AppointmentSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES, read_only=True)
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Appointment
        fields = '__all__'

    def get_status(self, obj):
        return obj.status

    def create(self, validated_data):
        service = validated_data.get('service')
        scheduled_datetime = validated_data.get('scheduled_datetime')  # Obtem o datetime agendado
        date = scheduled_datetime.date()

        available_slots = service.get_available_slots(date)

        desired_slot_time = scheduled_datetime.time().strftime('%H:%M')
        if desired_slot_time not in available_slots:
            raise serializers.ValidationError("O horário escolhido não está disponível para agendamento.")
        user = self.context['request'].user
        return super().create({"customer": user, **validated_data})

class ServiceSerializer(serializers.ModelSerializer):
    available_slots = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'

    def get_available_slots(self, obj):
        # Obtenha a instância da company a partir do objeto Service
        company = obj.company
        # Você pode passar a data desejada, por exemplo, a data atual
        date = self.context.get('date', datetime.now().date())  # Data padrão: hoje

        # Chama o método get_available_slots no modelo Service
        return obj.get_available_slots(date)