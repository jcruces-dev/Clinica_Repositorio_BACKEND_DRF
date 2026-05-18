from django.shortcuts import render
from django.core import serializers
from secretaria.models import SecretariaModel
from secretaria.serializers import SecretariaSerializer
from direccion.models import DireccionModel
from direccion.serializers import DireccionSerializer
from usuarios.models import CustomersUsers
from usuarios.serializers import CustomUserSerializer
from comuna_clinica.models import ComunaClinicaModel
from comuna_clinica.serializers import ComunaClinicaSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
# Crear un código de Venta.
import uuid
# Validador de rut.
from doctor import validar_rut
# Hashear la Pass.
from django.contrib.auth.hashers import make_password
# El token de DRF.
from rest_framework.authtoken.models import Token
# Cerrar la session del usuario actual.
from django.contrib.auth import logout
# Importamos el status.
from rest_framework import status
#
from django.contrib.auth.models import Group
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
from rest_framework.decorators import authentication_classes, permission_classes, api_view
# La clase IsAuthenticated es un permiso en DRF que verifica si el usuario que realiza la solicitud está autenticado.
# Cuando se establece IsAuthenticated como permiso para una vista, solo los usuarios autenticados podrán acceder a esa vista. Los usuarios no autenticados no tendrán permiso para realizar la solicitud
from rest_framework.permissions import IsAuthenticated, AllowAny
# Proceso de Autenticación
# Obtención del Token: Cuando un usuario se autentica, intercambia su nombre de usuario y
# contraseña por un token único. Este token se genera y almacena en la base de datos asociado al usuario.
# Uso del Token: En solicitudes subsiguientes, el cliente debe incluir este token en el encabezado
# Authorization de la solicitud HTTP. El formato típico es Authorization: Token <token_value>
from rest_framework.authentication import TokenAuthentication
#from rest_framework.decorators import
from datetime import datetime, date
# render_to_string; Sirve para enviar el HTML del correo.-------------------
from django.template.loader import render_to_string
# Mensaje del E-mail.
from django.core.mail import EmailMessage
#
from django.conf import settings
#----- Librería para crear PDF -------------------------------------------------
import pdfkit
#----- Fin Librería para crear PDF ---------------------------------------------

# Create your views here.
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_secretaria(request):
    try:
        # Obtener el grupo por nombre
        grupo = Group.objects.get(name='Secretaria')
        #print(grupo)
        # Obtener todos los usuarios del grupo
        usuarios = grupo.user_set.all()
        print(usuarios)
        datos = []
        for users in usuarios:
            print(users.id)
            serializer_secretaria = SecretariaModel.objects.filter(fk_user=users.id)
            for ser in serializer_secretaria:
                # secretaria_clinica = ser.secretaria_clinica.all()
                # for secretaria in secretaria_clinica:
                datos.append({
                        'id_user': users.id,
                        'username': users.username,
                        'primer_nombre': ser.primer_nombre,
                        'segundo_nombre': ser.segundo_nombre,
                        'ap_paterno': ser.ap_paterno,
                        'ap_materno': ser.ap_materno,
                        'email': users.email,
                        'edad': ser.edad,
                        'sexo': ser.sexo,
                        'rut': ser.rut,
                        'fono': ser.fono,
                        'secretaria_uuid': ser.secretaria_uuid,
                        # 'nombre_clinica': secretaria.nombre_clinica,
                        # 'comuna_clinica': secretaria.comuna_clinica,
                        # 'direccion_clinica': secretaria.direccion_clinica,
                    })
        print(datos)
        print("---------------------///****//")
        return Response({'secretarias':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)
#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_clin_secretaria(request, id_user):
    try:
        print(id_user)
        arr = []
        usuario = CustomersUsers.objects.get(pk=id_user)
        secretaria = SecretariaModel.objects.get(fk_user=usuario.id)
        clinica_secretaria = secretaria.secretaria_clinica.all()
        print(clinica_secretaria)
        for clinica in clinica_secretaria:
            arr.append({
                'id_clinica': clinica.id,
                'nombre_clinica': clinica.nombre_clinica,
                'comuna_clinica': clinica.comuna_clinica,
                'direccion_clinica': clinica.direccion_clinica,
            })
        #
        return Response({'clinicas':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)
#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agregar_clin_secretaria_panel_adm(request):
    try:
        print(request.data)
        arr = []
        secretaria = SecretariaModel.objects.get(fk_user=request.data['id_user_secretaria'])
        clinica = ComunaClinicaModel.objects.get(pk=request.data['id_clinica'])
        secretaria.secretaria_clinica.add(clinica)
        # Obtenemos todas las clínicas de la secretaria.
        obtener_clinicas = secretaria.secretaria_clinica.all()
        print(obtener_clinicas)
        for clin in obtener_clinicas:
            print(clin.nombre_clinica)
            arr.append({
                'id_clinica': clin.id,
                'nombre_clinica': clin.nombre_clinica,
                'comuna_clinica': clin.comuna_clinica,
                'direccion_clinica': clin.direccion_clinica,
            })

        #
        return Response({'clinicas':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)
#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_secretaria(request):
    try:
        print(request.data)
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        username = data.get("username")
        print(username)
        password = data.get("password")
        print(password)
        hashed_password = make_password(password)
        primer_nombre = data.get("primer_nombre")
        print("Primer Nombre")
        print(primer_nombre)
        print("----********-------")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        email = data.get("email")
        edad = data.get("edad")
        rut = data.get("rut")
        fono = str(data.get("fono"))
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        usuario_uuid = str(uuid.uuid4())
        secretaria_uuid = str(uuid.uuid4())
        id_clinica = data.get("id_clinica")
        print(secretaria_uuid)
        #data.update({'usuario_uuid': usuario_uuid})
        if not all([username, primer_nombre, segundo_nombre, ap_paterno, ap_materno, password, email, edad, rut, fono, sexo]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        # Validamos el rut de la secretaria.
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        if SecretariaModel.objects.filter(rut=rut).exists():
            return Response({'error': 4}, status=status.HTTP_400_BAD_REQUEST)
        # Validamos si el Username existe.
        if CustomersUsers.objects.filter(username=username).exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        # Creamos el array de Objeto.
        user_dato = {
            'username': username,
            'password': hashed_password,
            'email': email,
            'usuario_uuid': usuario_uuid,
        }
        #
        dato_serializado = CustomUserSerializer(data=user_dato)
        if dato_serializado.is_valid():
            print("Ojo---------")
            usuario = dato_serializado.save()
            print(usuario.id)
            # Creamos el array de objeto de la Secretaria.
            dato_secretaria = {
                    'primer_nombre': primer_nombre,
                    'segundo_nombre': segundo_nombre,
                    'email': email,
                    'edad': edad,
                    'rut': rut,
                    'fono': fono,
                    'sexo': sexo,
                    'secretaria_uuid': secretaria_uuid,
                    'fk_user': usuario.id,
                    'ap_materno': ap_materno,
                    'ap_paterno': ap_paterno,
            }
            #
            secretaria = SecretariaSerializer(data=dato_secretaria)
            if secretaria.is_valid():
                instancia_secretaria = secretaria.save()
                #print(data)
                # group = Group.objects.get(name='Secretaria')
                # usuario.groups.add(group)
                # Agregar la relación muchos a muchos
                clinica = ComunaClinicaModel.objects.filter(pk=id_clinica)
                instancia_secretaria.secretaria_clinica.set(clinica)
                # Obtener el grupo por nombre
                grupo = Group.objects.get(name='Secretaria')
                #print(grupo)
                # Obtener todos los usuarios del grupo
                usuarios = grupo.user_set.all()
                print("*************")
                print(usuarios)
                print("*************")
                datos = []
                print("Casi Entramos")
                for users in usuarios:
                    print("Entramos")
                    print(users.id)
                    serializer_secretaria = SecretariaModel.objects.filter(fk_user=users.id)
                    for ser in serializer_secretaria:
                        # Obtener los nombres de las clínicas asociadas
                        nombres_clinicas = list(ser.secretaria_clinica.values_list('nombre_clinica', flat=True))
                        print("//***********************************//")
                        print(nombres_clinicas)
                        print("//***********************************//")
                        datos.append({
                                'id_user': users.id,
                                'username': users.username,
                                'primer_nombre': ser.primer_nombre,
                                'segundo_nombre': ser.segundo_nombre,
                                'ap_paterno': ser.ap_paterno,
                                'ap_materno': ser.ap_materno,
                                'email': users.email,
                                'edad': ser.edad,
                                'sexo': ser.sexo,
                                'rut': ser.rut,
                                'fono': ser.fono,
                                'secretaria_uuid': ser.secretaria_uuid
                            })
                print(datos)
                print("---------------------///****//")
                return Response({'secretarias':datos},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
        else:
            print("Errores de validación:", dato_serializado.errors)
            return Response({'error': 2, 'details': dato_serializado.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)

#
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_secretaria(request, id):
    try:
        print(id)
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        print(data)
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        user_dato = {}
        if password == "0":
            # Creaos el array de objetos.
            user_dato = {
                'username': username,
                'email': email,
            }
        hashed_password = make_password(password)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        edad = data.get("edad")
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        fono = str(data.get("fono"))
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        # Validaciones.
        if not all([username, password, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        user = CustomersUsers.objects.get(pk=id)
        print(user.id)
        # Validamos si el Username existe en otro Usuario.
        if CustomersUsers.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        # Creaos el array de objetos.
        user_dato = {
            'username': username,
            'password': hashed_password,
            'email': email,
        }
        serializer = CustomUserSerializer(user, data=user_dato, partial=True)
        #
        if serializer.is_valid():
            #
            id_user = serializer.save()
            #
            secretaria = SecretariaModel.objects.get(fk_user=id_user)
            # Creamos el array de objetos.
            secre_dato = {
                'primer_nombre': primer_nombre,
                'segundo_nombre': segundo_nombre,
                'edad': edad,
                'rut': rut,
                'fono': fono,
                'sexo': sexo,
                'ap_paterno': ap_paterno,
                'ap_materno': ap_materno,
            }
            sercretaria_serializers = SecretariaSerializer(secretaria, data=secre_dato, partial=True)
            if sercretaria_serializers.is_valid():
                sercretaria_serializers.save()
                # Obtener el grupo por nombre
                grupo = Group.objects.get(name='Secretaria')
                #print(grupo)
                # Obtener todos los usuarios del grupo
                usuarios = grupo.user_set.all()
                print("*************")
                print(usuarios)
                print("*************")
                datos = []
                print("Casi Entramos")
                for users in usuarios:
                    print("Entramos")
                    print(users.id)
                    serializer_secretaria = SecretariaModel.objects.filter(fk_user=users.id)
                    for ser in serializer_secretaria:
                        print(ser.primer_nombre)
                        datos.append({
                                'id_user': users.id,
                                'username': users.username,
                                'primer_nombre': ser.primer_nombre,
                                'segundo_nombre': ser.segundo_nombre,
                                'ap_paterno': ser.ap_paterno,
                                'ap_materno': ser.ap_materno,
                                'email': users.email,
                                'edad': ser.edad,
                                'sexo': ser.sexo,
                                'rut': ser.rut,
                                'fono': ser.fono,
                                'secretaria_uuid': ser.secretaria_uuid
                            })
                print(datos)
                print("---------------------///****//")
                return Response({'secretarias':datos},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_secretaria(request, id):
    try:
        print(id)
        usuario = CustomersUsers.objects.get(pk=id)
        usuario.delete()
        # Obtener el grupo por nombre
        grupo = Group.objects.get(name='Secretaria')
        #print(grupo)
        # Obtener todos los usuarios del grupo
        usuarios = grupo.user_set.all()
        print("*************")
        print(usuarios)
        print("*************")
        datos = []
        print("Casi Entramos")
        for users in usuarios:
            print("Entramos")
            print(users.id)
            serializer_secretaria = SecretariaModel.objects.filter(fk_user=users.id)
            for ser in serializer_secretaria:
                print(ser.primer_nombre)
                datos.append({
                        'id_user': users.id,
                        'username': users.username,
                        'primer_nombre': ser.primer_nombre,
                        'segundo_nombre': ser.segundo_nombre,
                        'ap_paterno': ser.ap_paterno,
                        'ap_materno': ser.ap_materno,
                        'email': users.email,
                        'edad': ser.edad,
                        'sexo': ser.sexo,
                        'rut': ser.rut,
                        'fono': ser.fono,
                        'secretaria_uuid': ser.secretaria_uuid
                    })
        print(datos)
        print("---------------------///****//")
        return Response({'secretarias':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 3}, status=400)

#
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_clin_secretaria(request, id_clin, id_user_secret):
    try:
        print("Entramos")
        # print(f"ID de Clínica: {id_clin}")
        # print(f"ID de Usuario Secretaria: {id_user_secret}")
        secretaria = SecretariaModel.objects.get(fk_user=id_user_secret)
        secretaria.secretaria_clinica.remove(id_clin)
        arr = []
        usuario = CustomersUsers.objects.get(pk=id_user_secret)
        secretaria = SecretariaModel.objects.get(fk_user=usuario.id)
        clinica_secretaria = secretaria.secretaria_clinica.filter()
        print("clinica_secretaria")
        print(clinica_secretaria)
        print("clinica_secretaria")
        for clinica in clinica_secretaria:
            arr.append({
                'id_clinica': clinica.id,
                'nombre_clinica': clinica.nombre_clinica,
                'comuna_clinica': clinica.comuna_clinica,
                'direccion_clinica': clinica.direccion_clinica,
            })
        #
        return Response({'secretarias':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 3}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_datos_secretaria(request, username):
    try:
        print(username)
        arr = []
        usuario = CustomersUsers.objects.get(username=username)
        print(usuario.id)
        secretaria = SecretariaModel.objects.get(fk_user=usuario.id)
        arr.append({
            'id_user': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
            'primer_nombre': secretaria.primer_nombre,
            'segundo_nombre': secretaria.segundo_nombre,
            'edad': secretaria.edad,
            'sexo': secretaria.sexo,
            'rut': secretaria.rut,
            'fono': secretaria.fono,
            'ap_paterno': secretaria.ap_paterno,
            'ap_materno': secretaria.ap_materno,
        })
        return Response({'secretaria':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 3}, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_panel_secretaria(request, id_user):
    try:
        print("Prueba 123")
        print(id_user)
        print("Prueba 123")
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        print("/*/*/*/*/*/*/*/*/*/*//*/*")
        print(data)
        print("/*/*/*/*/*/*/*/*/*/*//*/*")
        cerrar_session = 0
        id_user_secret = data.get("id_usuario")
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        #
        user_sec = CustomersUsers.objects.get(pk=id_user)
        bd_username = user_sec.username
        # Realizaremos
        user_dato = {}
        #
        if password == "0" or bd_username == username:
            # Creaos el array de objetos.
            user_dato = {
                'email': email,
            }
        #
        if password == "0" and bd_username != username:
            cerrar_session = 1
            # Creaos el array de objetos.
            user_dato = {
                'username': username,
                'email': email,
            }
        if password != "0" and bd_username == username:
            #
            cerrar_session = 1
            #
            hashed_password = make_password(password)
            # Creaos el array de objetos.
            user_dato = {
                'password': hashed_password,
                'email': email,
            }
        if password != "0" and bd_username != username:
            #
            cerrar_session = 1
            # Creaos el array de objetos.
            hashed_password = make_password(password)
            user_dato = {
                'username':username,
                'email': email,
                'password': hashed_password,
            }

        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        edad = data.get("edad")
        rut = data.get("rut")
        fono = data.get("fono")
        sexo = data.get("sexo")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        # Validaciones.
        if not all([username, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        user = CustomersUsers.objects.get(pk=id_user)
        serializer = CustomUserSerializer(user, data=user_dato, partial=True)
        #
        if serializer.is_valid():
            #
            id_user = serializer.save()
            secretaria = SecretariaModel.objects.get(fk_user=id_user)
            # Creamos el array de objetos.
            secre_dato = {
                'primer_nombre': primer_nombre,
                'segundo_nombre': segundo_nombre,
                'edad': edad,
                'rut': rut,
                'fono': fono,
                'sexo': sexo,
                'ap_paterno': ap_paterno,
                'ap_materno': ap_materno,
            }
            sercretaria_serializers = SecretariaSerializer(secretaria, data=secre_dato, partial=True)
            datos = []
            if sercretaria_serializers.is_valid():
                sercretaria_serializers.save()
                secretaria_model = SecretariaModel.objects.get(fk_user=id_user)
                datos.append({
                        'id_user': user.id,
                        'username': user.username,
                        'primer_nombre': secretaria_model.primer_nombre,
                        'segundo_nombre': secretaria_model.segundo_nombre,
                        'ap_paterno': secretaria_model.ap_paterno,
                        'ap_materno': secretaria_model.ap_materno,
                        'email': user.email,
                        'edad': secretaria_model.edad,
                        'sexo': secretaria_model.sexo,
                        'rut': secretaria_model.rut,
                        'fono': secretaria_model.fono,
                        'secretaria_uuid': secretaria_model.secretaria_uuid,
                    })
                print(datos)
                print("Prueba: ", datos)
                #
                if cerrar_session == 1:
                    # Eliminar el token actual del usuario
                    Token.objects.filter(pk=user.id).delete()
                    # Cerrar sesión en el request
                    logout(request)
                    logout_required = True
                    return Response({'secretarias':datos,
                                     'cerrar_session': cerrar_session},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
                if cerrar_session == 0:
                    logout_required = False
                    return Response({'secretarias':datos,
                                     'cerrar_session': cerrar_session},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
                print("---------------------///****//")

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_secretarias_panel_secretaria(request):
    try:
        # Obtener el grupo por nombre
        grupo = Group.objects.get(name='Secretaria')
        #print(grupo)
        # Obtener todos los usuarios del grupo
        usuarios = grupo.user_set.all()
        print(usuarios)
        datos = []
        for users in usuarios:
            print(users.id)
            serializer_secretaria = SecretariaModel.objects.filter(fk_user=users.id)
            for ser in serializer_secretaria:
                # secretaria_clinica = ser.secretaria_clinica.all()
                # for secretaria in secretaria_clinica:
                datos.append({
                        'id_user': users.id,
                        'username': users.username,
                        'primer_nombre': ser.primer_nombre,
                        'segundo_nombre': ser.segundo_nombre,
                        'ap_paterno': ser.ap_paterno,
                        'ap_materno': ser.ap_materno,
                        'email': users.email,
                        'edad': ser.edad,
                        'sexo': ser.sexo,
                        'rut': ser.rut,
                        # 'fono': ser.fono,
                        'secretaria_uuid': ser.secretaria_uuid,
                        # 'nombre_clinica': secretaria.nombre_clinica,
                        # 'comuna_clinica': secretaria.comuna_clinica,
                        # 'direccion_clinica': secretaria.direccion_clinica,
                    })
        print(datos)
        print("---------------------///****//")
        return Response({'secretarias':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)