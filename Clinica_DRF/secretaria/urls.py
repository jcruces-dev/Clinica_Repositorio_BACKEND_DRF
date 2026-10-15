from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/secretaria/listar_secretaria/",
        views.listar_secretaria,
        name="listar_secretaria",
    ),
    path(
        "api/secretaria/crear_secretaria/",
        views.crear_secretaria,
        name="crear_secretaria",
    ),
    path(
        "api/secretaria/update_secretaria/<int:id>/",
        views.update_secretaria,
        name="update_secretaria",
    ),
    path(
        "api/secretaria/delete_secretaria/<int:id>/",
        views.delete_secretaria,
        name="delete_secretaria",
    ),
    path(
        "api/secretaria/obtener_clin_secretaria/<int:id_user>/",
        views.obtener_clin_secretaria,
        name="obtener_clin_secretaria",
    ),
    path(
        "api/secretaria/agregar_clin_secretaria_panel_adm/",
        views.agregar_clin_secretaria_panel_adm,
        name="agregar_clin_secretaria_panel_adm",
    ),
    path(
        "api/secretaria/delete_clin_secretaria/<int:id_clin>/<int:id_user_secret>/",
        views.delete_clin_secretaria,
        name="delete_clin_secretaria",
    ),
    # Panel Secretaria. secretaria/listar_datos_secretaria
    path(
        "api/secretaria/listar_datos_secretaria/<str:username>/",
        views.listar_datos_secretaria,
        name="listar_datos_secretaria",
    ),
    path(
        "api/secretaria/update_panel_secretaria/<int:id_user>/",
        views.update_panel_secretaria,
        name="update_panel_secretaria",
    ),
    path(
        "api/secretaria/listar_secretarias_panel_secretaria/",
        views.listar_secretarias_panel_secretaria,
        name="listar_secretarias_panel_secretaria",
    ),
]
