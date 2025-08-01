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
    duration_minutes = models.PositiveIntegerField(choices=[(30, '30 minutes'), (60, '60 minutes')], default=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # if service cannot share slot with any different services of the same company
    competes_with_others = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ({self.company.name})"

    def get_available_slots(self, date) -> list[str]:
        # Ensure date is a date object
        if hasattr(date, 'date'):
            date = date.date()

        working_hours = self.company.working_hours.filter(week_day=date.weekday()).first()
        if not working_hours:
            return []  # No slots today

        opening, closing = working_hours.open_time, working_hours.close_time
        duration = timedelta(minutes=self.duration_minutes)
        max_appointments_per_slot = working_hours.max_appointments_per_slot

        # Query appointments for the company and date
        bookings = Appointment.objects.filter(
            scheduled_datetime__date=date,
            service=self,
            status__in=["pending", "confirmed"]
        )

        # Build a dict of booked slots: {time: count}
        booked_slots = {}
        for booking in bookings.values('scheduled_datetime').annotate(appointments_count=models.Count('id')):
            slot_time = booking['scheduled_datetime'].time()
            booked_slots[slot_time] = booking['appointments_count']

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