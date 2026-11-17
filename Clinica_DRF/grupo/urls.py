from django.urls import path
from . import views

urlpatterns = [
    path("grupo/crear_grupo/", views.crear_grupo, name="crear_grupo"),
    path("grupo/listar_grupo/", views.listar_grupo, name="listar_grupo"),
    path("grupo/editar_grupo/<int:id>/", views.editar_grupo, name="editar_grupo"),
    path(
        "grupo/eliminar_grupo/<int:id>/",
        views.eliminar_grupo,
        name="eliminar_grupo",
    ),
]
