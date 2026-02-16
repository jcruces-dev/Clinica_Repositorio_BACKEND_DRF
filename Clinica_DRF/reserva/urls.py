from django.urls import path
from . import views

urlpatterns = [
    # INDEX.HTML
    path('reserva/listar_clinica_index', views.listar_clinica_index, name='listar_clinica_index'),
    # Esta ruta es de la seleccion del Index.
    path('reserva/listar_esp_index/<int:id>/', views.listar_esp_index, name='listar_esp_index'),
    # Esta ruta es de la seleccion del Index.
    path('reserva/listar_doc_index/<int:id_clinica>/<int:id_especialidad>/', views.listar_doc_index, name='listar_doc_index'),
    # Esta ruta es de la seleccion del Index.
    path('reserva/reserva_paciente_index', views.reserva_paciente_index, name='reserva_paciente_index'),
    # Eliminar una reserva del paciente registrado panel ADMIN.
    path('reserva/delete_pac_reserva/<int:fk_usuario>/', views.delete_pac_reserva, name='delete_pac_reserva'),
    # Obtener todas las citas registradas..
    path('reserva/historial_reserva', views.historial_reserva, name='historial_reserva'),
    # Obtener todos los pacientes correspondientes al doctor.
    path('reserva/listar_paciente_doctor', views.listar_paciente_doctor, name='listar_paciente_doctor'),
    # Obtener todos los pacientes correspondientes al doctor.
    path('reserva/listar_paciente_historial_doctor/<int:id>/', views.listar_paciente_historial_doctor, name='listar_paciente_historial_doctor'),
    # Listar laas clínicas del doctor para que vea sus reservas o citas, Panel
    path('reserva/listar_clinica_paciente_doctor', views.listar_clinica_paciente_doctor, name='listar_clinica_paciente_doctor'),
    # Obtener todos los pacientes correspondientes al doctor con citas.
    path('reserva/listar_paciente_doctor_cita', views.listar_paciente_doctor_cita, name='listar_paciente_doctor_cita'),
    path('reserva/historial_cli_pac_panel_secretaria/<int:id>/', views.historial_cli_pac_panel_secretaria, name='historial_cli_pac_panel_secretaria'),
    path('reserva/delete_reserva_panel_secretaria/<int:id_reserva>/', views.delete_reserva_panel_secretaria, name='delete_reserva_panel_secretaria'),
    # Obtener todas las citas registradas..
    path('reserva/historial_reserva_pac/<int:id_usuario>/', views.historial_reserva_pac, name='historial_reserva_pac'),
    # Obtener el diagnostico delpaciente.
    path('reserva/diagnostico_historial_pac/<int:id_usuario>/<str:cod_reserva>/', views.diagnostico_historial_pac, name='diagnostico_historial_pac'),
    # Verificar coid reserva Panel Pagar Reserva.
    path('reserva/cod_reserva_verificacion', views.cod_reserva_verificacion, name='cod_reserva_verificacion'),
    #
    path('reserva/update_pago_debito_reserva/<str:reserva_uuid>/', views.update_pago_debito_reserva, name='update_pago_debito_reserva'),
    #
    path('reserva/update_pago_credito_reserva/<str:reserva_uuid>/', views.update_pago_credito_reserva, name='update_pago_credito_reserva'),
    # Esta ruta es del pago con débito de la reserva en el Index.
    path('reserva/pago_debito_reserva_index', views.pago_debito_reserva_index, name='pago_debito_reserva_index'),
    # Esta ruta es del pago con CRÉDITO de la reserva en el Index.
    path('reserva/pago_credito_reserva_index', views.pago_credito_reserva_index, name='pago_credito_reserva_index'),
    ##############################################################################################################################
    # Esa ruta es solo para el microservicio de reservas. COMO PRUEBA.
    path('reserva/api/listar_reservas/', views.listar_reservas, name='listar_reservas'),
    #path('reserva/confirma_reserva/<str:reserva_uuid>/', views.confirma_reserva, name='confirma_reserva'),
    #path('reserva/anular_reserva/<str:reserva_uuid>/', views.anular_reserva, name='anular_reserva'),
    ##############################################################################################################################
    path('reserva/api/confirmar_correo_reservas/<str:reserva_uuid>/', views.confirmar_correo_reservas, name='confirmar_correo_reservas'),
    #
    #path('reserva/api/anular_reserva_correo_reservas/<str:reserva_uuid>/', views.anular_reserva, name='anular_reserva'),
    path('reserva/api/anular_reserva_paciente_correo/<str:reserva_uuid>/', views.anular_reserva, name='anular_reserva'),
]