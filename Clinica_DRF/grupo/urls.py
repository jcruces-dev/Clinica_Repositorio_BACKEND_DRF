from django.urls import path
from . import views

urlpatterns = [
    path("api/grupo/crear_grupo/", views.crear_grupo, name="crear_grupo"),
    path("api/grupo/listar_grupo/", views.listar_grupo, name="listar_grupo"),
    path("api/grupo/editar_grupo/<int:id>/", views.editar_grupo, name="editar_grupo"),
    path(
        "api/grupo/eliminar_grupo/<int:id>/",
        views.eliminar_grupo,
        name="eliminar_grupo",
    ),
]
