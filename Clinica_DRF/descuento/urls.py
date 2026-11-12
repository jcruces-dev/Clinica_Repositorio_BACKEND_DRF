from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/descuento/listar_descuento/",
        views.listar_descuento,
        name="listar_descuento",
    ),
    path(
        "api/descuento/crear_descuento/", views.crear_descuento, name="crear_descuento"
    ),
    path(
        "api/descuento/eliminar_descuento/<int:id>/",
        views.eliminar_descuento,
        name="eliminar_descuento",
    ),
    path("api/descuento/descuento_pac/", views.descuento_pac, name="descuento_pac"),
    path("api/descuento/veri_cod_des", views.veri_cod_des, name="veri_cod_des"),
]
