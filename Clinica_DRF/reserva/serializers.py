
from rest_framework import serializers
# Hacemos el llamado a la clase donde agregamos mas cmpos a la tabla User.
from .models import ReservaModel
from paciente_no_registrado.models import PacienteNoRegisterModel


# Create your models here.
class ReservaSerializer(serializers.ModelSerializer):
    # Agregamos el campo usuario_creacion_reserva para que se guarde el usuario que crea la reserva.
    #fecha_creacion_reserva = serializers.DateTimeField(format="%d-%m-%Y")
    class Meta:
        model = ReservaModel
        fields = ['id', 'usuario_creacion_reserva', 'fecha_creacion_reserva','fecha_reserva', 'especialidad','nombre_doctor', 'tipo_pago', 'reserva_uuid', 'comuna_clinica', 'fk_usuario','fk_pac_no_register','direccion_clinica', 'nombre_clinica', 'hora_inicio','hora_termino', 'pago_realizado','reserva_cerrada', 'reser_confirmada', 'reser_anulada']