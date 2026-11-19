from django.shortcuts import render
from usuarios.models import CustomersUsers
from especialidad.models import Especialidad
from doctor.models import DoctorModel
from direccion.models import DireccionModel
from usuarios.serializers import CustomUserSerializer
from direccion.serializers import DireccionSerializer
from comuna_clinica.models import ComunaClinicaModel
from comuna_clinica.serializers import ComunaClinicaSerializer
from paciente.models import PacienteModel
from paciente.serializers import PacienteSerializer
from reserva.models import ReservaModel
from reserva.serializers import ReservaSerializer
from historial_clinico.models import HistorialClinicoModel
from historial_clinico.serializers import HistorialClinicoSerializer
from descuento.models import DescuentoModel
from descuento.serializers import DescuentoSerializer

# Esta es una tabla intermedia con columnas extras.
from descuento.models import DescuentoPaciente
from descuento.desc_paciente_serializers import DescuentoPacienteSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response

# Crear un código de Venta.
import uuid

# Objeto tiempo.
from datetime import datetime, timedelta

#
from django.contrib.auth.hashers import make_password  # ¡Añade esta importación!

# El token de DRF.
from rest_framework.authtoken.models import Token

# Cerrar la session del usuario actual.
from django.contrib.auth import logout

# Importamos el status.
from rest_framework import status

#
from django.contrib.auth.models import Group

# El token de DRF.
from rest_framework.authtoken.models import Token

#
import os

# Verificar si el usuario existe con este import, en caso de no, envía ERROR.
from django.shortcuts import get_object_or_404

# En Django REST Framework (DRF), los decoradores authentication_classes y
# permission_classes se utilizan para configurar y aplicar las políticas de autenticación y
# permisos a las vistas de la API.
# permission_classes; Este decorador se utiliza para especificar las clases de permisos que se
# deben usar para una vista específica. Los permisos determinan si un usuario tiene el derecho
# de realizar una acción específica en la API. Algunas de las clases de permisos comunes en DRF incluyen:
# AllowAny: Permite acceso sin restricciones, tanto a usuarios autenticados como no autenticados.
# IsAuthenticated: Permite acceso solo a usuarios autenticados.
# IsAdminUser: Permite acceso solo a usuarios administradores (donde user.is_staff es True).
# IsAuthenticatedOrReadOnly: Permite a los usuarios autenticados realizar cualquier solicitud,
# y a los usuarios no autenticados solo realizar solicitudes de lectura (GET, HEAD, OPTIONS)
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)

# La clase IsAuthenticated es un permiso en DRF que verifica si el usuario que realiza la solicitud está autenticado.
# Cuando se establece IsAuthenticated como permiso para una vista, solo los usuarios autenticados podrán acceder a esa vista. Los usuarios no autenticados no tendrán permiso para realizar la solicitud
from rest_framework.permissions import IsAuthenticated, AllowAny

# Proceso de Autenticación
# Obtención del Token: Cuando un usuario se autentica, intercambia su nombre de usuario y
# contraseña por un token único. Este token se genera y almacena en la base de datos asociado al usuario.
# Uso del Token: En solicitudes subsiguientes, el cliente debe incluir este token en el encabezado
# Authorization de la solicitud HTTP. El formato típico es Authorization: Token <token_value>
from rest_framework.authentication import TokenAuthentication

# from rest_framework.decorators import
from datetime import datetime, date

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
def listar_descuento(request):
    try:
        print("Entramos")
        arr = []
        descuento = DescuentoModel.objects.all()
        print(descuento)
        if len(descuento) != 0:
            for desc in descuento:
                print(desc.fecha_creacion)
                arr.append(
                    {
                        "id_descuento": desc.id,
                        "fecha_creacion": desc.fecha_creacion,
                        "nombre_descuento": desc.nombre_descuento,
                        "descripcion": desc.descripcion,
                        "cod_descuento": desc.cod_descuento,
                        "fecha_inicio": desc.fecha_inicio,
                        "fecha_termino": desc.fecha_termino,
                        "descuento": desc.descuento,
                    }
                )
            return Response(
                {"descuento": arr},
                # Específicamos el status.
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": 1},
                # Específicamos el status.
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def crear_descuento(request):
    try:
        arr = []
        #
        nombre_descuento = request.data["nombre_descuento"]
        descripcion = request.data["descripcion"]
        cod_descuento = request.data["cod_descuento"]
        descuento = request.data["descuento"]
        fecha_inicio = request.data["fecha_inicio"]
        print(fecha_inicio)
        fecha_termino = request.data["fecha_termino"]
        print(fecha_termino)
        #
        if not all(
            [
                nombre_descuento,
                descripcion,
                cod_descuento,
                fecha_inicio,
                fecha_termino,
                descuento,
            ]
        ):
            return Response({"error": 2}, status=status.HTTP_400_BAD_REQUEST)
        # Convertir strings en objetos datetime
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ft = datetime.strptime(fecha_termino, "%Y-%m-%d")
        # Validar que la fecha de inicio sea menor que la de término
        if fi >= ft:
            return Response({"error": 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        descuentoSerializers = DescuentoSerializer(data=request.data)
        if descuentoSerializers.is_valid():
            descuentoSerializers.save()
            descuento = DescuentoModel.objects.all()
            print(descuento)
            for desc in descuento:
                print(desc.fecha_creacion)
                arr.append(
                    {
                        "id_descuento": desc.id,
                        "fecha_creacion": desc.fecha_creacion,
                        "nombre_descuento": desc.nombre_descuento,
                        "descripcion": desc.descripcion,
                        "cod_descuento": desc.cod_descuento,
                        "fecha_inicio": desc.fecha_inicio,
                        "fecha_termino": desc.fecha_termino,
                        "descuento": desc.descuento,
                    }
                )
            return Response(
                {"descuento": arr},
                # Específicamos el status.
                status=status.HTTP_200_OK,
            )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


# Create your views here.
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def eliminar_descuento(request, id):
    try:
        print("DELETE")
        arr = []
        desc = DescuentoModel.objects.get(pk=id)
        print(desc)
        desc.delete()
        descuento = DescuentoModel.objects.all()
        print(descuento)
        for desc in descuento:
            print(desc.fecha_creacion)
            arr.append(
                {
                    "id_descuento": desc.id,
                    "fecha_creacion": desc.fecha_creacion,
                    "nombre_descuento": desc.nombre_descuento,
                    "descripcion": desc.descripcion,
                    "cod_descuento": desc.cod_descuento,
                    "fecha_inicio": desc.fecha_inicio,
                    "fecha_termino": desc.fecha_termino,
                    "descuento": desc.descuento,
                }
            )
        return Response(
            {"descuento": arr},
            # Específicamos el status.
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


#
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def descuento_pac(request):
    try:
        #
        fk_usuario = request.data["fk_usuario"]
        codigo = request.data["codigo"]
        valor_especialidad = request.data["valor_especialidad"]
        paciente = PacienteModel.objects.get(fk_user=fk_usuario)
        #
        cod_desc = DescuentoModel.objects.filter(cod_descuento=codigo).exists()
        if cod_desc:
            #
            cod_desc = DescuentoModel.objects.filter(cod_descuento=codigo)
            for cod in cod_desc:
                # print(cod.descuento)
                cod_descuento = cod.descuento
                fecha_expire_desc = cod.fecha_termino
                # El dato existe
                asignado = DescuentoPaciente.objects.filter(
                    fk_descuento=cod.id, fk_paciente=paciente.id
                ).exists()
                if asignado:
                    # DescuentoPaciente.objects.create(fk_descuento=descuento,fk_paciente=paciente,
                    #                                 # Aquí puedes guardar más campos si tu modelo lo requiere
                    #                             )
                    return Response(
                        {"descuento": 2},
                        # Específicamos el status.
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Obtenemos la fecha de hoy.
                fecha_actual = date.today()
                if fecha_actual <= fecha_expire_desc:
                    # Si el código existe y no está utilizado por el paciente, se envía el descuento.
                    return Response(
                        {"descuento": cod_descuento},
                        # Específicamos el status.
                        status=status.HTTP_200_OK,
                    )
                if fecha_actual > fecha_expire_desc:
                    return Response(
                        {"error": 4},
                        # Específicamos el status.
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        return Response(
            {"descuento": 3},
            # Específicamos el status.
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


# Método para pagar reserva NO pagada.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def veri_cod_des(request):
    try:
        #
        print("Método: -- veri_cod_des --")
        fk_usuario = request.data["fk_usuario"]
        codigo = request.data["codigo"]
        valor_especialidad = request.data["valor_especialidad"]
        paciente = PacienteModel.objects.get(fk_user=fk_usuario)
        #
        cod_desc = DescuentoModel.objects.filter(cod_descuento=codigo).exists()
        if cod_desc:
            #
            cod_desc = DescuentoModel.objects.filter(cod_descuento=codigo)
            for cod in cod_desc:
                # print(cod.descuento)
                cod_descuento = cod.descuento
                fecha_expire_desc = cod.fecha_termino
                # El dato existe
                asignado = DescuentoPaciente.objects.filter(
                    fk_descuento=cod.id, fk_paciente=paciente.id
                ).exists()
                if asignado:
                    # DescuentoPaciente.objects.create(fk_descuento=descuento,fk_paciente=paciente,
                    #                                 # Aquí puedes guardar más campos si tu modelo lo requiere
                    #                             )
                    return Response(
                        {"descuento": 2},
                        # Específicamos el status.
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Obtenemos la fecha de hoy.
                fecha_actual = date.today()
                if fecha_actual <= fecha_expire_desc:
                    # Si el código existe y no está utilizado por el paciente, se envía el descuento.
                    return Response(
                        {"descuento": cod_descuento},
                        # Específicamos el status.
                        status=status.HTTP_200_OK,
                    )
                if fecha_actual > fecha_expire_desc:
                    return Response(
                        {"error": 4},
                        # Específicamos el status.
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        return Response(
            {"error": 3},
            # Específicamos el status.
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)
