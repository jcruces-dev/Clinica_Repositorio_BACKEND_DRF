from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/consulta/consulta_paciente/",
        views.consulta_paciente,
        name="consulta_paciente",
    ),
    path(
        "api/consulta/listar_consulta_abierta_paciente/",
        views.listar_consulta_abierta_paciente,
        name="listar_consulta_abierta_paciente",
    ),
    path(
        "api/consulta/listar_consulta_cerrada_paciente/",
        views.listar_consulta_cerrada_paciente,
        name="listar_consulta_cerrada_paciente",
    ),
    path(
        "api/consulta/respuesta_consulta_cerrada_paciente/<int:id_consulta>/",
        views.respuesta_consulta_cerrada_paciente,
        name="respuesta_consulta_cerrada_paciente",
    ),
    path(
        "api/consulta/responder_consulta_panel_secretaria/<int:id_consulta>/",
        views.responder_consulta_panel_secretaria,
        name="responder_consulta_panel_secretaria",
    ),
]
