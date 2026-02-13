from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.core.validators import MinValueValidator
from paciente_no_registrado.models import PacienteNoRegisterModel
# Create your models here.
class ReservaModel(models.Model):
    fecha_creacion_reserva = models.DateTimeField(default=now)
    usuario_creacion_reserva = models.CharField(null=True, max_length=250)
    fecha_reserva = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField(default="00:00:00")
    hora_termino = models.TimeField(default="00:00:00")
    especialidad = models.CharField(null=True, max_length=200)
    nombre_doctor = models.CharField(null=True, max_length=250)
    tipo_pago = models.CharField(null=True, max_length=250)
    fk_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fk_pac_no_register = models.ForeignKey(PacienteNoRegisterModel, on_delete=models.SET_NULL, null=True)
    reserva_uuid = models.CharField(null=True, max_length=250)
    nombre_clinica = models.CharField(null=True, max_length=250)
    comuna_clinica = models.CharField(null=True, max_length=250)
    direccion_clinica = models.CharField(null=True, max_length=250)
    reserva_cerrada = models.IntegerField(null=True, blank=True, default=0)
    pago_realizado = models.IntegerField(null=True, blank=True, default=0)
    reser_confirmada = models.IntegerField(null=True, blank=True, default=0)
    reser_anulada = models.IntegerField(null=True, blank=True, default=0)