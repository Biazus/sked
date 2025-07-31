from django.contrib import admin

from bookings.models import Appointment, WorkingHours, Service, Company

# Register your models here.
admin.site.register(Appointment)
admin.site.register(WorkingHours)
admin.site.register(Service)
admin.site.register(Company)