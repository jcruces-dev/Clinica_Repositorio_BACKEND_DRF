from django.urls import path
from . import views

# Actualización de URLs.
urlpatterns = [
    path(
        "doctor/listar_doctor_admin/",
        views.listar_doctor_admin,
        name="listar_doctor_admin",
    ),
    path("doctor/crear_doctor/", views.crear_doctor, name="crear_doctor"),
    path("doctor/esp_doc_list/<int:id>/", views.esp_doc_list, name="esp_doc_list"),
    path(
        "doctor/nueva_esp_doctor_admin/<int:id>/",
        views.nueva_esp_doctor_admin,
        name="nueva_esp_doctor_admin",
    ),
    path(
        "doctor/borrar_esp_doctor/<int:id>/",
        views.borrar_esp_doctor,
        name="borrar_esp_doctor",
    ),
    path(
        "doctor/borrar_doctor/<int:id>/<str:username>/",
        views.borrar_doctor,
        name="borrar_doctor",
    ),
    path(
        "doctor/listar_clinica/<int:id>/",
        views.listar_clinica_doc,
        name="listar_clinica_doc",
    ),
    path(
        "doctor/listar_clinica_panel_doc/<int:id>/",
        views.listar_clinica_panel_doc,
        name="listar_clinica_panel_doc",
    ),
    path(
        "doctor/doctor_nueva_clinica/<int:id>/",
        views.doctor_nueva_clinica,
        name="doctor_nueva_clinica",
    ),
    path(
        "doctor/delete_clinica_doctor/<int:id>/",
        views.delete_clinica_doctor,
        name="delete_clinica_doctor",
    ),
    path("doctor/update_doctor/<int:id>/", views.update_doctor, name="update_doctor"),
    path(
        "doctor/esp_doc_list_reserva_panel_adm/",
        views.esp_doc_list_reserva_panel_adm,
        name="esp_doc_list_reserva_panel_adm",
    ),
    # Panel Doctor.
    path(
        "doctor/listar_datos_doctor/<str:username>/",
        views.listar_datos_doctor,
        name="listar_datos_doctor",
    ),
    path(
        "doctor/update_panel_doctor/<int:id>/",
        views.update_panel_doctor,
        name="update_panel_doctor",
    ),
    path("doctor/listar_doctor/", views.listar_doctor, name="listar_doctor"),
]
