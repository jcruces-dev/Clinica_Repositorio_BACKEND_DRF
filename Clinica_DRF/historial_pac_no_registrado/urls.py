from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/historial_pac_no_registrado/historial_paciente_no_registrado/<str:reserva_uuid>/",
        views.historial_paciente_no_registrado,
        name="historial_paciente_no_registrado",
    ),
]
