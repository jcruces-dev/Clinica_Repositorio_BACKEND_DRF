from django.urls import path
from . import views

urlpatterns = [
    path(
        "paciente_no_registrado/listar_pac_no_registrado/",
        views.listar_pac_no_registrado,
        name="listar_pac_no_registrado",
    ),
]
