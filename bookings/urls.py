from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, AppointmentViewSet, ServiceViewSet, WorkingHoursViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'working hours', WorkingHoursViewSet)


urlpatterns = router.urls