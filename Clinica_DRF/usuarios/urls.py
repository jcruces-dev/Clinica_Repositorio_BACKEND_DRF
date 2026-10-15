from django.urls import path
from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path(
        "api/usuario/registrar_usuario/",
        views.registrar_usuario,
        name="registrar_usuario",
    ),
    # path('usuario/listar_doctor', views.listar_doctor, name='listar_doctor'),
    # path('usuario/crear_doctor', views.crear_doctor, name='crear_doctor'),
    # path('usuario/esp_doc_list/<int:id>/', views.esp_doc_list, name='esp_doc_list'),
    # path('usuario/nueva_esp_doctor_admin/<int:id>/', views.nueva_esp_doctor_admin, name='nueva_esp_doctor_admin'),
    # path('usuario/borrar_esp_doctor/<int:id>/', views.borrar_esp_doctor, name='borrar_esp_doctor'),
    # path('usuario/borrar_doctor/<int:id>/', views.borrar_doctor, name='borrar_doctor'),
    path(
        "api/usuario/listar_doctor_index/",
        views.listar_doctor_index,
        name="listar_doctor_index",
    ),
    # ------------------ PANEL ADMIN PACIENTE. ----------------------------------------------------------
    # path('paciente/listar_paciente', views.listar_paciente, name='listar_paciente'),
    # path('paciente/crear_paciente', views.crear_paciente, name='crear_paciente'),
    # path('paciente/update_paciente/<int:id>/', views.update_paciente, name='update_paciente'),
    # path('paciente/delete_paciente/<int:id>/', views.delete_paciente, name='delete_paciente'),
    # ------------------ FIN PANEL ADMIN PACIENTE. -------------------------------------------------------
    # -------------------- Panel Admin Módulo Secretaria. -------------------------------------------------
    # path('secretaria/listar_secretaria', views.listar_secretaria, name='listar_secretaria'),
    # path('secretaria/crear_secretaria', views.crear_secretaria, name='crear_secretaria'),
    # path('secretaria/update_secretaria/<int:id>/', views.update_secretaria, name='update_secretaria'),
    # path('secretaria/delete_secretaria/<int:id>/', views.delete_secretaria, name='delete_secretaria'),
    # -------------------- Fin Panel Admin Módulo Secretaria. ---------------------------------------------
    # -------------------- Inicio Panel Cardiologia Admin. ------------------------------------------------
    path(
        "api/cardiologia/listar_info_cardiologia/",
        views.listar_info_cardiologia,
        name="listar_info_cardiologia",
    ),
    # -------------------- Fin Inicio Panel Cardiologia Admin. --------------------------------------------
    # ----------------- Cerrar Sessión. -------------------------------------------------------------------
    path("api/usuario/cerrar_sesion/", views.cerrar_sesion, name="cerrar_sesion"),
]
