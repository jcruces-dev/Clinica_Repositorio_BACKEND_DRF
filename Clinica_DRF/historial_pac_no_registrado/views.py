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
from historial_pac_no_registrado.models import HistorialPacNoRegistradoModel
from historial_pac_no_registrado.serializers import HistorialPacNoRegistradoSerializer
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
import pdfkit

# ----- Fin Librería para crear PDF ---------------------------------------------


# Create your views here.
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def historial_paciente_no_registrado(request, reserva_uuid):
    try:
        print("Ingresamos")
        print(reserva_uuid)
        obtener_historial = HistorialPacNoRegistradoModel.objects.filter(
            reserva_uuid=reserva_uuid
        )
        if obtener_historial.count() == 0:
            return Response(
                {"error": 0},
                # Específicamos el status.
                status=status.HTTP_400_BAD_REQUEST,
            )
        arr = []
        for his in obtener_historial:
            arr.append(
                {
                    "id": his.id,
                    "reserva_uuid": his.reserva_uuid,
                    "fecha_historial": his.fecha_historial,
                    "sintoma": his.sintoma,
                    "diagnostico": his.diagnostico,
                    "observacion": his.observacion,
                    "fk_pac_no_registrado": his.fk_pac_no_registrado,
                }
            )
        serializer = HistorialPacNoRegistradoSerializer(arr, many=True)

        return Response(
            {"historial": serializer.data},
            # Específicamos el status.
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)
