from django.shortcuts import render

# Validador de rut.
from reserva import validar_rut
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)

# Hashear la Pass.
from django.contrib.auth.hashers import make_password
from usuarios.models import CustomersUsers
from usuarios.serializers import CustomUserSerializer
from especialidad.models import Especialidad
from especialidad.serializers import EspecialidadSerializers
from comuna_clinica.models import ComunaClinicaModel
from comuna_clinica.serializers import ComunaClinicaSerializer

#
from paciente_no_registrado.models import PacienteNoRegisterModel
from paciente_no_registrado.serializers import PacienteNoRegisterSerializer
from doctor.models import DoctorModel
from doctor.serializers import DoctorSerializer
from paciente.models import PacienteModel
from paciente.serializers import PacienteSerializer
from historial_clinico.models import HistorialClinicoModel
from historial_clinico.serializers import HistorialClinicoSerializer
from descuento.models import DescuentoPaciente
from descuento.desc_paciente_serializers import DescuentoPacienteSerializer

# Crear un código de Venta.
import uuid

# Importamos el status.
from rest_framework import status
from reserva.models import ReservaModel
from reserva.serializers import ReservaSerializer
from debito.models import DebitoModel
from debito.serializers import DebitoSerializer
from credito.models import CreditoModel
from credito.serializers import CreditoSerializer
from descuento.models import DescuentoModel
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from django.contrib.auth.models import Group

# Obtenemos la Fecha de Hoy.
from datetime import date, datetime
import pytz

# Crear la Carpeta de los PDF que se enviarán por Correo. ------------------
import os

# render_to_string; Sirve para enviar el HTML del correo.-------------------
from django.template.loader import render_to_string

# Mensaje del E-mail.
from django.core.mail import EmailMessage

#
from django.conf import settings

# ----- Librería para crear PDF -------------------------------------------------
# import pdfkit

# ----- Fin Librería para crear PDF ---------------------------------------------


# Create your views here.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def listar_pac_no_registrado(request):
    try:
        print("Listar Paciente No Registrado")
        #
        print("Usuario Logeado:")
        print(request.user)
        print("Usuario Logeado ID:")
        print(request.user.id)
        print("Usuario Logeado Username------------")
        listar_pac = PacienteNoRegisterModel.objects.all()
        doctor = DoctorModel.objects.get(fk_user=request.user.id)
        nombre_doctor = (
            doctor.primer_nombre
            + " "
            + doctor.segundo_nombre
            + " "
            + doctor.ap_paterno
            + " "
            + doctor.ap_materno
        )
        print(listar_pac)
        #
        arr = []
        #
        modo_pago = None
        cerrada = None
        realizado = None
        for pac in listar_pac:
            print("Paciente ID:")
            print(pac.id)
            reserva = ReservaModel.objects.filter(
                fk_pac_no_register=pac.id, nombre_doctor=nombre_doctor
            )
            print("Reserva Paciente:")
            print(reserva)
            for res in reserva:
                especialidad = Especialidad.objects.get(
                    nombre_especialidad=res.especialidad
                )
                print(type(res.tipo_pago))
                if res.tipo_pago == "0":
                    modo_pago = "Débito"
                if res.tipo_pago == "1":
                    modo_pago = "Crédito"
                if res.reserva_cerrada == 0:
                    cerrada = "No"
                if res.reserva_cerrada == 1:
                    cerrada = "Si"
                if res.pago_realizado == 0:
                    realizado = "Débito"
                if res.pago_realizado == 1:
                    realizado = "Crédito"
                arr.append(
                    {
                        "id_reserva": res.id,
                        "fecha_creacion_reserva": res.fecha_creacion_reserva,
                        "fecha_reserva": res.fecha_reserva,
                        "usuario_creacion_reserva": str(res.usuario_creacion_reserva),
                        "fecha_reserva": res.fecha_reserva,
                        "hora_inicio": res.hora_inicio,
                        "hora_termino": res.hora_termino,
                        "especialidad": res.especialidad,
                        "valor_especialidad": especialidad.valor_especialidad,
                        "nombre_doctor": res.nombre_doctor,
                        "tipo_pago": realizado,
                        "reserva_uuid": str(res.reserva_uuid),
                        "nombre_clinica": res.nombre_clinica,
                        "comuna_clinica": res.comuna_clinica,
                        "direccion_clinica": res.direccion_clinica,
                        "reserva_cerrada": res.reserva_cerrada,
                        "pago_realizado": res.pago_realizado,
                        "fk_pac_no_register": res.fk_pac_no_register.id,
                        "id": pac.id,
                        "primer_nombre": pac.primer_nombre,
                        "segundo_nombre": pac.segundo_nombre,
                        "ap_paterno": pac.ap_paterno,
                        "ap_materno": pac.ap_materno,
                        "edad": pac.edad,
                        "sexo": pac.sexo,
                        "rut": pac.rut,
                        "fono": pac.fono,
                        "email": pac.email,
                        "paciente_uuid": str(pac.paciente_uuid),
                    }
                )
                print(arr)
                print("Fin del For de la Reserva")
        return Response(
            {"pacientes": arr},
            # Específicamos el status.
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 0}, status=400)
