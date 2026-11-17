from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from usuarios.models import CustomersUsers
from usuarios.serializers import CustomUserSerializer
from paciente.models import PacienteModel
from paciente.serializers import PacienteSerializer
from historial_clinico.models import HistorialClinicoModel
from historial_clinico.serializers import HistorialClinicoSerializer

# Crear un código de Venta.
import uuid

# Importamos el status.
from rest_framework import status
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from django.contrib.auth.models import Group


# Create your views here.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def listar_historial_clinico_pacien_panel_doctor(request):
    try:
        print("Entramos al Hitorial")
        print(request.data)
        print("Entramos al Hitorial")
        reserva_uuid = request.data["reserva_uuid"]
        historial_cli = HistorialClinicoModel.objects.filter(
            fk_paciente=request.data["id_paciente"], reserva_uuid=reserva_uuid
        )
        print(historial_cli)
        arr = []
        for historial in historial_cli:
            arr.append(
                {
                    "id_paciente": historial.fk_paciente.id,
                    "fecha_creacion_historial": historial.fecha_creacion_historial,
                    "diagnostico": historial.diagnostico,
                    "sintoma": historial.sintoma,
                    "observacion": historial.observacion,
                }
            )
        print(arr)
        return Response(
            {"paciente": arr},
            # Específicamos el status.
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)
