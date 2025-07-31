from datetime import datetime, timedelta
from datetime import datetime, time, timedelta

from django.db import models

from accounts.models import CustomUser


class Company(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.IntegerField()
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'zipcode')

    # TODO    This method can be part of services object instead
    # TODO    That would facilitate management of time since we can create multiple services per day
    # TODO    and wouldnt matter which company the service is part of. Also we would have the chance
    # TODO    to remove the 'compete' attribute since the service itself would not compete to other service
    def get_available_slots(self, service, date) -> list[str]:
        """
        Return a list of available time slots for a given service and date,
        considering the company's working hours, service duration, and existing appointments.

        Args:
            service (Service): The service for which to find available slots.
            date (datetime or date): The date to check for available slots.

        Returns:
            list: List of available slot times as strings in 'HH:MM' format.
        """

        # Ensure date is a date object
        if hasattr(date, 'date'):
            date = date.date()

        working_hours = self.working_hours.filter(week_day=date.weekday()).first()
        if not working_hours:
            return []  # no slots today

        opening, closing = working_hours.open_time, working_hours.close_time
        duration = timedelta(minutes=service.duration_minutes)
        max_appointments_per_slot = working_hours.max_appointments_per_slot

        # Query appointments for the company and date
        agendamentos = Appointment.objects.filter(
            scheduled_datetime__date=date,
            service__company=self,
            status__in=["pending", "confirmed"]
        )

        # Build a dict of booked slots: {time: count}
        booked_slots = {}
        if service.competes_with_others:
            for agendamento in agendamentos.values('scheduled_datetime').annotate(appointments_count=models.Count('id')):
                slot_time = agendamento['scheduled_datetime'].time()
                booked_slots[slot_time] = agendamento['appointments_count']

        # Generate available slots
        slots = []
        current = datetime.combine(date, opening)
        end = datetime.combine(date, closing) - duration
        while current <= end:
            slot_time = current.time()
            if booked_slots.get(slot_time, 0) < max_appointments_per_slot:
                slots.append(slot_time.strftime('%H:%M'))
            current += duration
        return slots

class WorkingHours(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='working_hours')
    week_day = models.PositiveIntegerField(choices=[
        (0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'),
        (3, 'Quinta-feira'), (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo')
    ])
    open_time = models.TimeField()
    close_time = models.TimeField()
    max_appointments_per_slot = models.PositiveIntegerField()

    class Meta:
        unique_together = ('company', 'week_day')

    def __str__(self):
        return f"{self.company.name} - {self.get_week_day_display()} {self.open_time} - {self.close_time}"


class Service(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=150, verbose_name='Nome do serviço')
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # if service cannot share slot with any different services of the same company
    competes_with_others = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ({self.company.name})"

class Appointment(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    scheduled_datetime = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('canceled', 'Cancelado'),
        ('completed', 'Concluído'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.service.name} para {self.customer} em {self.scheduled_datetime:%d/%m/%Y %H:%M} na empresa {self.service.company.name}"

    class Meta:
        ordering = ['-scheduled_datetime']