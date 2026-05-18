from django.urls import path
from . import views

urlpatterns = [
    path('paciente/listar_paciente', views.listar_paciente, name='listar_paciente'),
    path('paciente/pac_no_registrado_admin', views.pac_no_registrado_admin, name='pac_no_registrado_admin'),
    path('paciente/crear_paciente_index_registrar', views.crear_paciente_index_registrar, name='crear_paciente_index_registrar'),
    path('paciente/crear_paciente', views.crear_paciente, name='crear_paciente'),
    path('paciente/update_paciente/<int:id>/', views.update_paciente, name='update_paciente'),
    path('paciente/delete_paciente/<int:id>/', views.delete_paciente, name='delete_paciente'),
    path('paciente/reserva_paciente', views.reserva_paciente, name='reserva_paciente'),
    path('paciente/historial_user_paciente/<int:id_usuario>/', views.historial_user_paciente, name='historial_user_paciente'),
    path('paciente/reserva_paciente_registrado', views.reserva_paciente_registrado, name='reserva_paciente_registrado'),
    path('paciente/crear_reserva_pac_registrado', views.crear_reserva_pac_registrado, name='crear_reserva_pac_registrado'),
    path('paciente/historial_clinico', views.historial_clinico, name='historial_clinico'),
    path('paciente/update_paciente_panel_secretaria/<int:id>/', views.update_paciente_panel_secretaria, name='update_paciente_panel_secretaria'),
    path('paciente/listar_datos_paciente/<str:username>/', views.listar_datos_paciente, name='listar_datos_paciente'),
    path('paciente/update_pac_panel_pac/<int:id_user>/', views.update_pac_panel_pac, name='update_pac_panel_pac'),
    path('paciente/res_nombre_paciente/<str:username>/', views.res_nombre_paciente, name='res_nombre_paciente'),
    path('paciente/reserva_paciente_panel_paciente', views.reserva_paciente_panel_paciente, name='reserva_paciente_panel_paciente'),
    path('paciente/crear_reserva_panel_pac', views.crear_reserva_panel_pac, name='crear_reserva_panel_pac'),
    # Obtener la especialidad desde el panel de PACIENTE REGISTRADO.
    path('paciente/esp_panel_pac_registrado/', views.esp_panel_pac_registrado, name='esp_panel_pac_registrado'),
    # Obtener la especial
    # Reserva de cita desde el panel ADMIN.
    path('paciente/crear_reserva_panel_admin', views.crear_reserva_panel_admin, name='crear_reserva_panel_admin'),
    path('paciente/crear_reserva_pac_registrado_secretaria/', views.crear_reserva_pac_registrado_secretaria, name='crear_reserva_pac_registrado_secretaria'),
]