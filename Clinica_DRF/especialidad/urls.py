from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/especialidad/especialidad_doctor/",
        views.especialidad_doctor,
        name="especialidad_doctor",
    ),
    path(
        "api/especialidad/insertar_especialidad/",
        views.insertar_especialidad,
        name="insertar_especialidad",
    ),
    path(
        "api/especialidad/edit_especialidad/<int:id>/",
        views.edit_especialidad,
        name="edit_especialidad",
    ),
    path(
        "api/especialidad/eliminar_especialidad/<int:id>/",
        views.eliminar_especialidad,
        name="eliminar_especialidad",
    ),
    # Listar las especialidades en el panel secretaria para la reserva de un paciente REGISTRADO.
    path(
        "api/especialidad/listar_esp_panel_secretaria/",
        views.listar_esp_panel_secretaria,
        name="listar_esp_panel_secretaria",
    ),
]
