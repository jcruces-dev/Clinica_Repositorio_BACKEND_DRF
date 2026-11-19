from django.shortcuts import render
from usuarios.models import CustomersUsers
from especialidad.models import Especialidad
from comuna_clinica.models import ComunaClinicaModel
from comuna_clinica.serializers import ComunaClinicaSerializer
from direccion.models import DireccionModel
from usuarios.serializers import CustomUserSerializer
from direccion.serializers import DireccionSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response

# Crear un código de Venta.
import uuid

#
from django.contrib.auth.hashers import make_password  # ¡Añade esta importación!

# El token de DRF.
from rest_framework.authtoken.models import Token

# Cerrar la session del usuario actual.
from django.contrib.auth import logout

# Importamos el status.
from rest_framework import status

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
@permission_classes([AllowAny])
def listar_clinica_adm(request):
    try:
        # Obtener el grupo por nombre
        clinica = ComunaClinicaModel.objects.all()
        # Serializar los datos
        serializer = ComunaClinicaSerializer(clinica, many=True)
        # print(serializer.data)
        if serializer.data:
            return Response(
                {"list_clinica": serializer.data},
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


#
@api_view(["POST"])
@permission_classes([AllowAny])
def crear_clinica(request):
    try:
        print(request.data)
        data = request.data.copy()
        nombre_clinica = data.get("nombre_clinica")
        comuna_clinica = data.get("comuna_clinica")
        direccion_clinica = data.get("direccion_clinica")
        if not all([nombre_clinica, comuna_clinica, direccion_clinica]):
            return Response({"error": 0}, status=status.HTTP_400_BAD_REQUEST)
        # Serializar los datos
        serializer = ComunaClinicaSerializer(data=request.data)
        print(serializer)
        if serializer.is_valid():
            serializer.save()
            # Obtener el grupo por nombre
            clinica_list = ComunaClinicaModel.objects.all()
            serializer_list = ComunaClinicaSerializer(clinica_list, many=True)
            return Response(
                {"list_clinica": serializer_list.data},
                # Específicamos el status.
                status=status.HTTP_200_OK,
            )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


#
@api_view(["PUT"])
@permission_classes([AllowAny])
def editar_clinica(request, id):
    try:
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        nombre_clinica = data.get("nombre_clinica")
        comuna_clinica = data.get("comuna_clinica")
        direccion_clinica = data.get("direccion_clinica")
        # # Validaciones.
        if not all([nombre_clinica, comuna_clinica, direccion_clinica]):
            return Response({"error": 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        clinica = ComunaClinicaModel.objects.get(pk=id)
        # Validar y actualizar datos
        serializer = ComunaClinicaSerializer(clinica, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            list_clinica = ComunaClinicaModel.objects.all()
            serializsers_clinica = ComunaClinicaSerializer(list_clinica, many=True)
            return Response(
                {"list_clinica": serializsers_clinica.data}, status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


#
@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_clinica(request, id):
    try:
        clinica = ComunaClinicaModel.objects.get(pk=id)
        clinica.delete()
        # print(grupo)
        # Obtener todos los usuarios del grupo
        list_clinica = ComunaClinicaModel.objects.all()
        serializers = ComunaClinicaSerializer(list_clinica, many=True)
        return Response(
            {"list_clinica": serializers.data},
            # Específicamos el status.
            status=status.HTTP_200_OK,
        )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({"error": 1}, status=400)


#
