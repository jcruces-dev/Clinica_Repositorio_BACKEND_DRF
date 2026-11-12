from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/clinica/listar_clinica_adm/",
        views.listar_clinica_adm,
        name="listar_clinica_adm",
    ),
    path("api/clinica/crear_clinica/", views.crear_clinica, name="crear_clinica"),
    path(
        "api/clinica/editar_clinica/<int:id>/",
        views.editar_clinica,
        name="editar_clinica",
    ),
    path(
        "api/clinica/delete_clinica/<int:id>/",
        views.delete_clinica,
        name="delete_clinica",
    ),
]
