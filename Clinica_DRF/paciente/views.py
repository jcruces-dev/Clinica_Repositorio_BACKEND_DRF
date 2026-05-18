from django.shortcuts import render
from usuarios.models import CustomersUsers
from especialidad.models import Especialidad
from especialidad.serializers import EspecialidadSerializers
from doctor.models import DoctorModel
from direccion.models import DireccionModel
from usuarios.serializers import CustomUserSerializer
from direccion.serializers import DireccionSerializer
from comuna_clinica.models import ComunaClinicaModel
from comuna_clinica.serializers import ComunaClinicaSerializer
from paciente.models import PacienteModel
from paciente.serializers import PacienteSerializer
from paciente_no_registrado.models import PacienteNoRegisterModel
from paciente_no_registrado.serializers import PacienteNoRegisterSerializer
from reserva.models import ReservaModel
from reserva.serializers import ReservaSerializer
from historial_clinico.models import HistorialClinicoModel
from historial_clinico.serializers import HistorialClinicoSerializer
#
from historial_pac_no_registrado.models import HistorialPacNoRegistradoModel
from historial_pac_no_registrado.serializers import HistorialPacNoRegistradoSerializer
from credito.models import CreditoModel
from credito.serializers import CreditoSerializer
from debito.models import DebitoModel
from debito.serializers import DebitoSerializer
from secretaria.models import SecretariaModel
from secretaria.serializers import SecretariaSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.core import serializers
from descuento.models import DescuentoModel
from descuento.serializers import DescuentoSerializer
# Esta es una tabla intermedia con columnas extras.
from descuento.models import DescuentoPaciente
from descuento.desc_paciente_serializers import DescuentoPacienteSerializer
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
# Validador de rut.
from doctor import validar_rut
# Crear un código de Venta.
import uuid
# Objeto tiempo.
from datetime import datetime, timedelta
# Hashear la pass ingresada.
from django.contrib.auth.hashers import make_password
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
@permission_classes([IsAuthenticated])
def listar_paciente(request):
    try:
        # Obtener el grupo por nombre
        grupo = Group.objects.get(name='Paciente')
        #print(grupo)
        # Obtener todos los usuarios del grupo
        usuarios = grupo.user_set.all()
        datos = []
        for users in usuarios:
            user_paciente = users.username + ' ' + users.email
            print(user_paciente)
            # Serializar los datos
            paciente = PacienteModel.objects.filter(fk_user=users.id)
            for pac in paciente:
                serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                for dir in serializer_dir:
                    print(dir.comuna)
                    datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
        print(datos)
        print("---------------------///****//")
        return Response({'pacientes':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pac_no_registrado_admin(request):
    try:
        # Nos traemos todas las reservas
        reserva = ReservaModel.objects.all()
        print(reserva)
        datos = []
        for res in reserva:
            print("Ingresamos")
            if res.fk_pac_no_register:
                paciente = res.fk_pac_no_register
                paciente_no_registrado = PacienteNoRegisterModel.objects.filter(pk=paciente.id)
                for pac in paciente_no_registrado:
                    datos.append({'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'email':pac.email, 'paciente_uuid':pac.paciente_uuid, 'fecha_creacion_reserva':res.fecha_creacion_reserva,'usuario_creacion_reserva':res.usuario_creacion_reserva, 'fecha_reserva': res.fecha_reserva, 'hora_inicio': res.hora_inicio, 'hora_termino': res.hora_termino, 'especialidad': res.especialidad, 'nombre_doctor': res.nombre_doctor, 'tipo_pago': res.tipo_pago, 'reserva_uuid': res.reserva_uuid, 'nombre_clinica': res.nombre_clinica, 'comuna_clinica': res.comuna_clinica, 'direccion_clinica': res.direccion_clinica, 'reserva_cerrada': res.reserva_cerrada, 'pago_realizado': res.pago_realizado})
        print(datos)
        print("---------------------///****//")
        return Response({'pacientes':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Crear Paciente INDEX REGISTRAR.HTML.
@api_view(['POST'])
@permission_classes([AllowAny])
def crear_paciente_index_registrar(request):
    try:
        #print("Prueba")
        res = []
        #print(request.data)
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        username = data.get("username")
        if CustomersUsers.objects.filter(username=username).exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        password = data.get("password")
        hashed_password = make_password(password)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        email = data.get("email")
        edad = data.get("edad")
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        fono = str(data.get("fono"))
        print(fono)
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        vivienda = data.get("vivienda")
        region = data.get("region")
        comuna = data.get("comuna")
        num_vivienda = data.get("num_vivienda")
        #res.append({'fecha_reserva': fecha_reserva, })
        usuario_uuid = str(uuid.uuid4())
        data['usuario_uuid'] = usuario_uuid
        paciente_uuid = str(uuid.uuid4())
        print(data)
        dato_user = {
            'username': username,
            'password': hashed_password,
            'email': email,
            'usuario_uuid': usuario_uuid
        }
        #
        if not all([username, password, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo, vivienda, region, comuna, num_vivienda]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        if PacienteModel.objects.filter(rut=rut).exists():
            return Response({'error': 4}, status=status.HTTP_400_BAD_REQUEST)
        dato_serializado = CustomUserSerializer(data=dato_user)
        if dato_serializado.is_valid():
            usuario = dato_serializado.save()
            print(usuario.id)
            usuario_id = CustomersUsers.objects.get(pk=usuario.id)
            print("Pasamos - 1")
            # Insertar el Paciente.
            paciente_data = {
                'primer_nombre': primer_nombre,
                'segundo_nombre':segundo_nombre,
                'edad': edad,
                'sexo': sexo,
                'rut': rut,
                'fono': fono,
                'paciente_uuid': paciente_uuid,
                'fk_user': usuario_id.id,
                'ap_materno': ap_materno,
                'ap_paterno': ap_paterno,
            }
            #
            paciente = PacienteSerializer(data=paciente_data)
            if paciente.is_valid():
                paciente_instancia = paciente.save()
                correo_dato_inicial_pac_registrado(primer_nombre, segundo_nombre, ap_paterno, ap_materno, rut, username, password, email)
                # group = Group.objects.get(name='Paciente')
                # usuario.groups.add(group)
                paciente_id = PacienteModel.objects.get(pk=paciente_instancia.id)
                print(paciente_id)
                data_direccion = {
                    'vivienda':vivienda,
                    'region':region,
                    'comuna':comuna,
                    'num_vivienda':num_vivienda,
                    'fk_paciente' : paciente_id.id
                }
                direccion_dato_serializado = DireccionSerializer(data=data_direccion)
                #print(direccion_dato_serializado)
                if direccion_dato_serializado.is_valid():
                    direccion_dato_serializado.save()
                    # Obtener el grupo por nombre
                    grupo = Group.objects.get(name='Paciente')
                    #print(grupo)
                    # Obtener todos los usuarios del grupo
                    usuarios = grupo.user_set.all()
                    datos = []
                    for users in usuarios:
                        user_paciente = users.username + ' ' + users.email
                        # Serializar los datos
                        paciente = PacienteModel.objects.filter(fk_user=users.id)
                        for pac in paciente:
                            serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                            for dir in serializer_dir:
                                print(dir.comuna)
                                datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
                    return Response({'pacientes':datos},
                                    # Específicamos el status.
                                    status=status.HTTP_200_OK)
                else:
                    print("Errores de validación:", dato_serializado.errors)
                    return Response({'error': 2, 'details': dato_serializado.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)

# Crear Paciente Panel ADMIN y SECRETARIA.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_paciente(request):
    try:
        #print("Prueba")
        res = []
        #print(request.data)
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        username = data.get("username")
        if CustomersUsers.objects.filter(username=username).exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        password = data.get("password")
        hashed_password = make_password(password)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        email = data.get("email")
        edad = data.get("edad")
        rut = data.get("rut")
        print(rut)
        print(len(rut))
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        fono = str(data.get("fono"))
        print(fono)
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        vivienda = data.get("vivienda")
        region = data.get("region")
        comuna = data.get("comuna")
        num_vivienda = data.get("num_vivienda")
        #res.append({'fecha_reserva': fecha_reserva, })
        usuario_uuid = str(uuid.uuid4())
        data['usuario_uuid'] = usuario_uuid
        paciente_uuid = str(uuid.uuid4())
        print(data)
        dato_user = {
            'username': username,
            'password': hashed_password,
            'email': email,
            'usuario_uuid': usuario_uuid
        }
        #
        if not all([username, password, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo, vivienda, region, comuna, num_vivienda]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        # validar = validar_rut.validar_rut(rut)
        # print("Validar Rut")
        # print(validar)
        # if not validar:
        #     return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        if PacienteModel.objects.filter(rut=rut).exists():
            return Response({'error': 4}, status=status.HTTP_400_BAD_REQUEST)
        dato_serializado = CustomUserSerializer(data=dato_user)
        if dato_serializado.is_valid():
            usuario = dato_serializado.save()
            print(usuario.id)
            usuario_id = CustomersUsers.objects.get(pk=usuario.id)
            print("Pasamos - 1")
            # Insertar el Paciente.
            paciente_data = {
                'primer_nombre': primer_nombre,
                'segundo_nombre':segundo_nombre,
                'edad': edad,
                'sexo': sexo,
                'rut': rut,
                'fono': fono,
                'paciente_uuid': paciente_uuid,
                'fk_user': usuario_id.id,
                'ap_materno': ap_materno,
                'ap_paterno': ap_paterno,
            }
            #
            paciente = PacienteSerializer(data=paciente_data)
            if paciente.is_valid():
                paciente_instancia = paciente.save()
                # Enviamos los datos del paciente por correo; Nombre completo, rut, username, password.
                print("*** Funcionando Correos Email ***")
                correo_dato_inicial_pac_registrado(primer_nombre, segundo_nombre, ap_paterno, ap_materno, rut, username, password, email)
                paciente_id = PacienteModel.objects.get(pk=paciente_instancia.id)
                print(paciente_id)
                data_direccion = {
                    'vivienda':vivienda,
                    'region':region,
                    'comuna':comuna,
                    'num_vivienda':num_vivienda,
                    'fk_paciente' : paciente_id.id
                }
                direccion_dato_serializado = DireccionSerializer(data=data_direccion)
                #print(direccion_dato_serializado)
                if direccion_dato_serializado.is_valid():
                    direccion_dato_serializado.save()
                    # Obtener el grupo por nombre
                    grupo = Group.objects.get(name='Paciente')
                    #print(grupo)
                    # Obtener todos los usuarios del grupo
                    usuarios = grupo.user_set.all()
                    datos = []
                    for users in usuarios:
                        user_paciente = users.username + ' ' + users.email
                        # Serializar los datos
                        paciente = PacienteModel.objects.filter(fk_user=users.id)
                        for pac in paciente:
                            serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                            for dir in serializer_dir:
                                print(dir.comuna)
                                datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
                    return Response({'pacientes':datos},
                                    # Específicamos el status.
                                    status=status.HTTP_200_OK)
                else:
                    print("Errores de validación:", dato_serializado.errors)
                    return Response({'error': 2, 'details': dato_serializado.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)
#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_user_paciente(request, id_usuario):
    try:
        print("Historial User Paciente.")
        print(id_usuario)
        res = []
        # Obtener la instancia de User.
        fk_user_id = CustomersUsers.objects.get(pk=id_usuario)
        pac = PacienteModel.objects.get(fk_user=fk_user_id.id)
        nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
        print(nombre_paciente)
        # Obtener Todas las Reservas del Paciente.
        reservas = ReservaModel.objects.filter(fk_usuario=fk_user_id.id)
        for res in reservas:
            print(res.fecha_creacion_reserva)
        # Serializar las reservas.
        reservas_serializadas = ReservaSerializer(reservas, many=True)
        # Modificar los datos directamente a partir de los datos serializados.
        res = [
            {
                'fecha_creacion_reserva': reserv['fecha_creacion_reserva'],
                'fecha_reserva': reserv['fecha_reserva'],
                'especialidad': reserv['especialidad'],
                'nombre_doctor': reserv['nombre_doctor'],
                'tipo_pago': reserv['tipo_pago'],
                'reserva_uuid': reserv['reserva_uuid'],
                'comuna_clinica': reserv['comuna_clinica'],
                'fk_usuario': reserv['fk_usuario'],
                'direccion_clinica': reserv['direccion_clinica'],
                'nombre_clinica': reserv['nombre_clinica'],
                'hora_inicio': reserv['hora_inicio'],
                'hora_termino': reserv['hora_termino'],
                'pago_realizado': reserv['pago_realizado'],
                'reserva_cerrada': reserv['reserva_cerrada'],
                'nombre_paciente': nombre_paciente
            }
            for reserv in reservas_serializadas.data
        ]
        print(res)
        return Response({'pacientes':res},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_paciente(request, id):
    try:
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        #
        user = CustomersUsers.objects.get(pk=id)
        username = data.get("username")
        # Validamos si el Username existe en otro Usuario.
        if CustomersUsers.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        print(username)
        password = None
        password = data.get("password")
        email = data.get("email")
        if password == '0':
            # Creamos e array de objetos para actualizar el usuario.
            dato_user = {
                'username': username,
                'email': email
            }
        if password != '0':
            print("Pasamos 2")
            password = make_password(password)
            # Creamos el array de objetos para actualizar el usuario.
            dato_user = {
                'username': username,
                'password': password,
                'email': email
            }
        #hashed_password = make_password(password)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        edad = data.get("edad")
        rut = data.get("rut")
        fono = str(data.get("fono"))
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        # Agregamos el prefijo +56 para el caso del fono.
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        vivienda = data.get("vivienda")
        region = data.get("region")
        comuna = data.get("comuna")
        num_vivienda = data.get("num_vivienda")
        # Validaciones.
        if not all([primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo, vivienda, region, comuna, num_vivienda]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        # Validar y actualizar datos
        serializer = CustomUserSerializer(user, data=dato_user, partial=True)
        print("-----------------------------------------------------------------")
        if serializer.is_valid():
            # Actualizar campos adicionales
            serializer.save()
            # Creamos el array de objetos de los deatos a actual del paciente.
            paciente_dato = {
                'primer_nombre':primer_nombre,
                'segundo_nombre':segundo_nombre,
                'edad':edad,
                'rut':rut,
                'fono':fono,
                'sexo':sexo,
                'ap_materno':ap_materno,
                'ap_paterno':ap_paterno,
            }
            paciente = PacienteModel.objects.get(fk_user=user.id)
            update_paciente = PacienteSerializer(paciente, data=paciente_dato, partial=True)
            if update_paciente.is_valid():
                id_pac = update_paciente.save()
                # Buscar la instancia de la dirección existente
                direccion = DireccionModel.objects.filter(fk_paciente=id_pac.id).first()
                # Creamos el array de objeto de DIRECCIÓN.
                direcc_datos = {
                    'vivienda': vivienda,
                    'region': region,
                    'comuna': comuna,
                    'num_vivienda': num_vivienda,
                }
                direccion_serializer = DireccionSerializer(direccion, data=direcc_datos, partial=True)
                if direccion_serializer.is_valid():
                    direccion_serializer.save()
                    print("Pasamos")
                    # Obtener el grupo por nombre
                    grupo = Group.objects.get(name='Paciente')
                    #print(grupo)
                    # Obtener todos los usuarios del grupo
                    usuarios = grupo.user_set.all()
                    datos = []
                    for users in usuarios:
                        user_paciente = users.username + ' ' + users.email
                        print(user_paciente)
                        # Serializar los datos
                        paciente = PacienteModel.objects.filter(fk_user=users.id)
                        for pac in paciente:
                            print("Doctor")
                            serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                            for dir in serializer_dir:
                                print(dir.comuna)
                                datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
                    print(datos)
                    print("---------------------///****//")
                    return Response({'pacientes':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
                else:
                    return Response(direccion_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_paciente(request, id):
    try:
        user = CustomersUsers.objects.get(pk=id)
        #direccion = CustomersUsers.objects.get(pk=user.id)
        #direccion.delete()
        user.delete()
        # Obtener el grupo por nombre
        grupo = Group.objects.get(name='Paciente')
        #print(grupo)
        # Obtener todos los usuarios del grupo
        usuarios = grupo.user_set.all()
        datos = []
        for users in usuarios:
            user_paciente = users.username + ' ' + users.email
            print(user_paciente)
            # Serializar los datos
            paciente = PacienteModel.objects.filter(fk_user=users.id)
            for pac in paciente:
                print("Doctor")
                serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                for dir in serializer_dir:
                    print(dir.comuna)
                    datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
        print(datos)
        print("---------------------///****//")
        return Response({'pacientes':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['POST'])
@permission_classes([AllowAny])
def reserva_paciente(request):
    try:
        #
        arr = []
        id_clinica = request.data["id_clinica"]
        id_especialidad = request.data["id_especialidad"]
        id_usuario = request.data["id_usuario"]

        #
        nombre_clinica = ComunaClinicaModel.objects.get(pk=id_clinica)
        print(nombre_clinica.nombre_clinica)
        #
        especialidad = Especialidad.objects.get(pk=id_especialidad)
        print(especialidad.nombre_especialidad)
        arr.append({'especialidad': especialidad.nombre_especialidad, 'valor_especialidad': especialidad.valor_especialidad})
        #
        usuario = CustomersUsers.objects.get(pk=id_usuario)
        print(usuario.first_name)
        #
        print(arr)
        doctor = DoctorModel.objects.get(fk_user=usuario.id)
        #
        datos_reserva = ReservaModel.objects.filter(especialidad= especialidad.id, fk_usuario__id=usuario.id, nombre_clinica=nombre_clinica.nombre_clinica)
        print(datos_reserva)
        for reser in datos_reserva:
            print(reser.reserva_uuid)
        return Response({'pacientes':1},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Reserva Paciente Registrado desde el Panel Secretaria.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reserva_paciente_registrado(request):
    try:
        print("Entramos a la Reserva")
        data = request.data
        print(data)
        # Validación de campos obligatorios
        required_fields = ["id_clinica", "id_especialidad", "id_usuario_doctor", "id_usuario"]
        if any(data.get(field) in [None, '0'] for field in required_fields):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener objetos relacionados
        nombre_clinica = ComunaClinicaModel.objects.get(pk=data["id_clinica"])
        especialidad = Especialidad.objects.get(pk=data["id_especialidad"])
        doctor = DoctorModel.objects.get(pk=data["id_usuario_doctor"])
        nombre_completo_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"

        # Filtramos reservas por doctor, clínica y especialidad
        reservas = ReservaModel.objects.filter(
            especialidad=especialidad.nombre_especialidad,
            nombre_clinica=nombre_clinica.nombre_clinica,
            nombre_doctor=nombre_completo_doctor,
        )
        #
        nueva_data = []
        for reserv in reservas:
            # Determinar el nombre del paciente según tipo Registrado y NO Registrado.
            if reserv.fk_usuario:
                paciente = PacienteModel.objects.filter(fk_user=reserv.fk_usuario.id).first()
                nombre_paciente = f"{paciente.primer_nombre} {paciente.segundo_nombre} {paciente.ap_paterno} {paciente.ap_materno}" if paciente else "Paciente no encontrado"
            elif reserv.fk_pac_no_register:
                paciente_no_reg = PacienteNoRegisterModel.objects.filter(pk=reserv.fk_pac_no_register.id).first()
                nombre_paciente = f"{paciente_no_reg.primer_nombre} {paciente_no_reg.segundo_nombre} {paciente_no_reg.ap_paterno} {paciente_no_reg.ap_materno}" if paciente_no_reg else "Paciente no registrado"
            else:
                nombre_paciente = "Paciente no asignado"
            # Construir evento para el calendario
            nueva_data.append({
                'title': reserv.especialidad,
                'start': f"{reserv.fecha_reserva}T{reserv.hora_inicio}",
                'end': f"{reserv.fecha_reserva}T{reserv.hora_termino}",
                'reserva_uuid': str(reserv.reserva_uuid),
                'nombre_paciente': nombre_paciente,
                'nombre_doctor': nombre_completo_doctor,
            })
        return Response({'pacientes': nueva_data}, status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)

#
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_reserva_pac_registrado(request):
    try:
        print("Creamos Reserva Paciente Registrado panel Secretaria")
        print(request.data)
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        #
        usuario = request.user.id
        grupos = request.user.groups.values_list('name', flat=True)
        usuario_creacion_reserva = None
        #
        if 'Paciente' in grupos:
            usuario_creacion = PacienteModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Doctor' in grupos:
            usuario_creacion = DoctorModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Secretaria' in grupos:
            usuario_creacion = SecretariaModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Administrador' in grupos:
            # usuario_creacion = SecretariaModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = 'Administrador'
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        fecha = data.get("fecha_reserva")
        fecha_formateada = fecha.split("T")[0]  # Esto nos dará "2025-04-10"
        data['fecha_reserva'] = fecha_formateada
        id_user_pac = CustomersUsers.objects.get(pk=data.get("fk_usuario"))
        #data.update({'fk_usuario_id': id_user_pac.id})
        list_pac = []
        reserva = str(uuid.uuid4())
        reserva_uuid = reserva
        data['reserva_uuid'] = reserva_uuid
        print(data)
        id_usuario_existe = data['fk_usuario']
        especialidad_existe = data['especialidad']
        fecha_reserva = data['fecha_reserva']
        fecha_reserva = date.fromisoformat(fecha_reserva)
        hoy = date.today()
        # Obtenemos el valor de la especialidad.
        valor_esp = Especialidad.objects.get("valor_especialidad")
        valor_especialidad = valor_esp.valor_especialidad
        # Verificamosel tipo de pago.
        metodo_pago = data['tipo_pago']
        pago_debito = []
        pago_creito = []
        cant_cuotas = data['cuotas']
        # Validacion de coutas y cant cuotas.
        if metodo_pago == 1:
            print(cant_cuotas)
            if cant_cuotas == "":
                return Response({'error': 15}, status=400)
        # Verificamos si existe reserva en la hora reservada para generar el error.
        verificar = ReservaModel.objects.filter(especialidad=especialidad_existe, fecha_reserva=fecha_reserva,fk_usuario=id_usuario_existe)
        print(verificar.count())
        if verificar.count() > 0:
            return Response({'error':0},
                    # Específicamos el status.
                    status=status.HTTP_400_BAD_REQUEST)
        #
        res = ReservaSerializer(data=data)
        print("Pasamos")
        if res.is_valid():
            res.save()
            # Obtenemos la instancia para obtener el id.
            id_reserva_insertada = res.instance.id
            print(id_reserva_insertada)
            #
            # if metodo_pago == '1':
            #     #
            #     credito = str(uuid.uuid4())
            #     credito_uuid = credito
            #     monto_cuota = valor_especialidad / cant_cuotas
            #     pago_debito = ({
            #         'credito': metodo_pago,
            #         'fecha_pago': hoy,
            #         'credito_uuid': credito_uuid,
            #         'cant_cuotas': cant_cuotas,
            #         'monto_total': valor_especialidad,
            #         'monto_cuotas' : monto_cuota,
            #         'fk_reserva_id': id_reserva_insertada
            #     })
            # Realizamos el insert en la tabla relacionada de
            reserva_user = ReservaModel.objects.filter(fk_usuario=request.data["fk_usuario"])
            print(reserva_user)
            # Obtenemos los datos del paciente.
            pac = PacienteModel.objects.get(fk_user=request.data["fk_usuario"])
            nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + " " + pac.ap_paterno + ' ' + pac.ap_materno
            #reserva_user_paciente = ReservaSerializer(reserva_user, many=True)
            # Obtener los datos para el correo.
            reserva_nueva = ReservaModel.objects.get(pk=id_reserva_insertada)
            # Creación del correo.
            subject = "Correo de Verificación de Compras"
            # Crearemos el envío de correos.
            template = render_to_string("templates/pacientes/correo_reserva.html",{
                'nombre_paciente': nombre_paciente,
                'rut_paciente': pac.rut,
                'email_paciente': id_user_pac.email,
                'fono_paciente': pac.fono,
                'fecha_reserva': reserva_nueva.fecha_reserva,
                'especialidad': reserva_nueva.especialidad,
                'nombre_doctor': reserva_nueva.nombre_doctor,
                'reserva_uuid': reserva_nueva.reserva_uuid,
                'comuna_clinica': reserva_nueva.comuna_clinica,
                'direccion_clinica': reserva_nueva.direccion_clinica,
                'nombre_clinica': reserva_nueva.nombre_clinica,
                'hora_inicio': reserva_nueva.hora_inicio,
                'hora_termino': reserva_nueva.hora_termino,
                'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
            })
            # Envío del mensaje. Debemos pasar el template.
            emailSender = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ["matiasfamilycrew@gmail.com"],
            )
            # print("Creacion del correo ")
            # Formato del mensaje en HTML.
            emailSender.content_subtype = "html"
            emailSender.fail_silently = False
            # Enviamos el correo.
            pdf_reserva(template, nombre_paciente, emailSender)
            emailSender.send()
        todas_reservas = ReservaModel.objects.all()
        todas_reservas_data = ReservaSerializer(todas_reservas, many=True)
        #
        return Response({'pacientes':todas_reservas_data.data},
                # Específicamos el status.
                status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['POST'])
# Para utilizar; IsAuthenticated
# No olvidar, asi debe venir la peticiondel Front-End; fetch(request_calendar,'Authorization': `Token ${token}`
@permission_classes([IsAuthenticated])
def historial_clinico(request):
    try:
        usuario = request.user
        cod_reserva = request.data.get("cod_reserva")
        sintoma = request.data.get("sintoma")
        diagnostico = request.data.get("diagnostico")
        observacion = request.data.get("observacion")
        nombre_paciente = request.data.get("nombre_paciente")

        reserva = ReservaModel.objects.get(reserva_uuid=cod_reserva)

        # Paciente registrado
        if reserva.fk_usuario:
            paciente = PacienteModel.objects.get(fk_user=reserva.fk_usuario.id)
            dato_historial = {
                'diagnostico': diagnostico,
                'sintoma': sintoma,
                'observacion': observacion,
                'fk_paciente': paciente.id,
                'reserva_uuid': cod_reserva,
            }
            serializer = HistorialClinicoSerializer(data=dato_historial)

        # Paciente no registrado
        elif reserva.fk_pac_no_register:
            print(reserva.fk_pac_no_register.id)
            paciente = PacienteNoRegisterModel.objects.get(pk=reserva.fk_pac_no_register.id)
            dato_historial = {
                'fecha_historial': date.today(),
                'diagnostico': diagnostico,
                'sintoma': sintoma,
                'observacion': observacion,
                'fk_pac_no_registrado': paciente.id,
                'reserva_uuid': cod_reserva,
            }
            serializer = HistorialPacNoRegistradoSerializer(data=dato_historial)
        else:
            return Response({'error': 'La reserva no tiene paciente asociado'}, status=status.HTTP_400_BAD_REQUEST)
        # Validación y guardado
        if serializer.is_valid():
            historial = serializer.save()
            reserva.reserva_cerrada = 1
            reserva.save()
        else:
            print("Errores de validación:", serializer.errors)
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener reservas del doctor
        doctor = DoctorModel.objects.filter(fk_user=usuario.id).first()
        if not doctor:
            return Response({'error': 'Doctor no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        nombre_completo = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"
        reservas = ReservaModel.objects.filter(nombre_doctor=nombre_completo)

        arr = []
        for res in reservas:
            arr.append({
                'id_reserva': res.id,
                'title': res.especialidad,
                'nombre_doctor': res.nombre_doctor,
                'nombre_clinica': res.nombre_clinica,
                'comuna_clinica': res.comuna_clinica,
                'direccion_clinica': res.direccion_clinica,
                'fecha_reserva': res.fecha_reserva,
                'hora_inicio': res.hora_inicio,
                'hora_termino': res.hora_termino,
                'fecha_creacion_reserva': res.fecha_creacion_reserva,
                'cod_reserva': res.reserva_uuid,
                'id_usuario': usuario.id,
                'nombre_paciente': nombre_paciente,
                'reserva_cerrada': res.reserva_cerrada,
                'pago_realizado': res.pago_realizado,
            })

        return Response({'paciente': arr}, status=status.HTTP_200_OK)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 'Error interno del servidor'}, status=status.HTTP_400_BAD_REQUEST)


#
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_paciente_panel_secretaria(request, id):
    try:
        print("update_paciente_panel_secretaria")
        print(request.data)
        print("update_paciente_panel_secretaria")
        # Hacer una copia mutable de request.data
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        email = data.get("email")
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")

        edad = data.get("edad")
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        fono = data.get("fono")
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        #
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        vivienda = data.get("vivienda")
        region = data.get("region")
        comuna = data.get("comuna")
        num_vivienda = data.get("num_vivienda")
        # Validaciones.
        if not all([primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo, vivienda, region, comuna, num_vivienda]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        # Creamos e array de objetos para actualizar el usuario.
        dato_user = {
            'email': email
        }
        #
        user = CustomersUsers.objects.get(pk=id)
        # Validar y actualizar datos
        serializer = CustomUserSerializer(user, data=dato_user, partial=True)
        print("-----------------------------------------------------------------")
        if serializer.is_valid():
            # Actualizar campos adicionales
            serializer.save()
            # Creamos el array de objetos de los deatos a actual del paciente.
            paciente_dato = {
                'primer_nombre':primer_nombre,
                'segundo_nombre':segundo_nombre,
                'edad':edad,
                'rut':rut,
                'fono':fono,
                'sexo':sexo,
                'ap_materno':ap_materno,
                'ap_paterno':ap_paterno,
            }
            paciente = PacienteModel.objects.get(fk_user=user.id)
            update_paciente = PacienteSerializer(paciente, data=paciente_dato, partial=True)
            if update_paciente.is_valid():
                id_pac = update_paciente.save()
                # Buscar la instancia de la dirección existente
                direccion = DireccionModel.objects.filter(fk_paciente=id_pac.id).first()
                # Creamos el array de objeto de DIRECCIÓN.
                direcc_datos = {
                    'vivienda': vivienda,
                    'region': region,
                    'comuna': comuna,
                    'num_vivienda': num_vivienda,
                }
                direccion_serializer = DireccionSerializer(direccion, data=direcc_datos, partial=True)
                if direccion_serializer.is_valid():
                    direccion_serializer.save()
                    print("Pasamos")
                    # Obtener el grupo por nombre
                    grupo = Group.objects.get(name='Paciente')
                    #print(grupo)
                    # Obtener todos los usuarios del grupo
                    usuarios = grupo.user_set.all()
                    datos = []
                    for users in usuarios:
                        user_paciente = users.username + ' ' + users.email
                        print(user_paciente)
                        # Serializar los datos
                        paciente = PacienteModel.objects.filter(fk_user=users.id)
                        for pac in paciente:
                            serializer_dir = DireccionModel.objects.filter(fk_paciente=pac.id)
                            for dir in serializer_dir:
                                print(dir.comuna)
                                datos.append({'id_usuario': users.id, 'username':users.username,'email':users.email, 'id_paciente': pac.id, 'primer_nombre': pac.primer_nombre, 'segundo_nombre': pac.segundo_nombre, 'ap_paterno': pac.ap_paterno, 'ap_materno': pac.ap_materno, 'edad': pac.edad, 'sexo': pac.sexo, 'rut': pac.rut, 'fono': pac.fono, 'paciente_uuid':pac.paciente_uuid, 'region': dir.region, 'comuna': dir.comuna, 'vivienda': dir.vivienda, 'num_vivienda': dir.num_vivienda})
                    print(datos)
                    print("---------------------///****//")
                    return Response({'pacientes':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
                else:
                    return Response(direccion_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_datos_paciente(request, username):
    try:
        #
        arr = []
        print(username)
        #
        user = CustomersUsers.objects.get(username=username)
        #
        paciente = PacienteModel.objects.filter(fk_user=user.id)
        for pac in paciente:
            #
            dir = DireccionModel.objects.get(fk_paciente=pac.id)
            arr.append({
                'id_user': user.id,
                'username': user.username,
                'email': user.email,
                'primer_nombre': pac.primer_nombre,
                'segundo_nombre': pac.segundo_nombre,
                'ap_paterno': pac.ap_paterno,
                'ap_materno': pac.ap_materno,
                'edad': pac.edad,
                'sexo': pac.sexo,
                'rut': pac.rut,
                'contacto': pac.fono,
                'region': dir.region,
                'comuna': dir.comuna,
                'vivienda': dir.vivienda,
                'num_vivienda': dir.num_vivienda,
            })
        return Response({'pacientes':arr},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_pac_panel_pac(request, id_user):
    try:
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
        print("Prueba Email")
        print(email)
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
        #
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        edad = data.get("edad")
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        print("Validar Rut")
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        fono = data.get("fono")
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        sexo = data.get("sexo")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        region = data.get("region")
        comuna = data.get("comuna")
        vivienda = data.get("vivienda")
        num_vivienda = data.get("num_vivienda")
        # Validaciones.
        if not all([username, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, rut, fono, sexo, region, comuna, vivienda, num_vivienda]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        #
        user = CustomersUsers.objects.get(pk=id_user)
        serializer = CustomUserSerializer(user, data=user_dato, partial=True)
        #
        if serializer.is_valid():
            #
            id_user = serializer.save()
            #
            paciente = PacienteModel.objects.get(fk_user=id_user)
            # Creamos el array de objetos.
            pac_dato = {
                'primer_nombre': primer_nombre,
                'segundo_nombre': segundo_nombre,
                'edad': edad,
                'rut': rut,
                'fono': fono,
                'sexo': sexo,
                'ap_paterno': ap_paterno,
                'ap_materno': ap_materno,
            }
            pac_serializers = PacienteSerializer(paciente, data=pac_dato, partial=True)
            if pac_serializers.is_valid():
                pac_serializers.save()
            #
                direccion = DireccionModel.objects.get(fk_paciente=paciente.id)
                dir_dato = {
                    'region': region,
                    'comuna': comuna,
                    'vivienda': vivienda,
                    'num_vivienda': num_vivienda,
                }
                dir_serializers = DireccionSerializer(direccion, data=dir_dato, partial=True)
                if dir_serializers.is_valid():
                    dir_serializers.save()
                    dato_pac = {
                        'id_user': user.id,
                        'username': user.username,
                        'email': user.email,
                        'primer_nombre': paciente.primer_nombre,
                        'segundo_nombre': paciente.segundo_nombre,
                        'ap_paterno': paciente.ap_paterno,
                        'ap_materno': paciente.ap_materno,
                        'edad': paciente.edad,
                        'sexo': paciente.sexo,
                        'rut': paciente.rut,
                        'contacto': paciente.fono,
                        'region': direccion.region,
                        'comuna': direccion.comuna,
                        'vivienda': direccion.vivienda,
                        'num_vivienda': direccion.num_vivienda,
                        'paciente_uuid': paciente.paciente_uuid,
                    }
                    if cerrar_session == 1:
                        # Eliminar el token actual del usuario
                        Token.objects.filter(pk=user.id).delete()
                        # Cerrar sesión en el request
                        logout(request)
                        logout_required = True
                        return Response({'paciente':dato_pac,
                                        'cerrar_session': cerrar_session},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
                    if cerrar_session == 0:
                        print("Pass")
                        logout_required = False
                        return Response({'paciente':dato_pac,
                                         'cerrar_session': cerrar_session},
                                        # Específicamos el status.
                                        status=status.HTTP_200_OK)
                print("---------------------///****//")
        else:
            return Response(serializer.errors, status=400)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def res_nombre_paciente(request, username):
    try:
        print(username)
        arr = []
        user = CustomersUsers.objects.get(username=username)
        paciente = PacienteModel.objects.get(fk_user=user.id)
        nombre_paciente = paciente.primer_nombre +' '+ paciente.segundo_nombre +' '+ paciente.ap_paterno +' '+ paciente.ap_materno
        return Response({'paciente':nombre_paciente,
                         'id_user': user.id},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['POST'])
@permission_classes([AllowAny])
def reserva_paciente_panel_paciente(request):
    try:
        #
        print("Reserva Ingresamod")
        print(request.data)
        print("Reserva Ingresamod")
        arr = []
        id_clinica = request.data["id_clinica"]
        id_especialidad = request.data["id_especialidad"]
        id_usuario = request.data["id_usuario"]
        id_doc = request.data["id_usuario_doctor"]
        print(id_usuario)
        #
        nombre_clinica = ComunaClinicaModel.objects.get(pk=id_clinica)
        print(nombre_clinica.nombre_clinica)
        #
        especialidad = Especialidad.objects.get(pk=id_especialidad)
        print(especialidad.nombre_especialidad)
        #
        usuario = CustomersUsers.objects.get(pk=id_usuario)
        #
        print(arr)
        doctor = DoctorModel.objects.get(pk=id_doc)
        nombre_doctor = doctor.primer_nombre + ' ' + doctor.segundo_nombre + ' ' + doctor.ap_paterno + ' ' + doctor.ap_materno
        print(nombre_doctor)
        #
        datos_reserva = ReservaModel.objects.filter(especialidad= especialidad.nombre_especialidad, nombre_doctor=nombre_doctor, nombre_clinica=nombre_clinica.nombre_clinica)
        print("---****---***----***")
        print(datos_reserva)
        print("---****---***----***")
        for reser in datos_reserva:
            print(reser.reserva_uuid)
            # Este array es para utilizarlo en FULL CALLENDAR.
            arr.append({
                'fecha_reserva': reser.fecha_reserva,
                'start': f"{reser.fecha_reserva}T{reser.hora_inicio}",
                'end': f"{reser.fecha_reserva}T{reser.hora_termino}",
                'title': reser.especialidad,
                'nombre_doctor': reser.nombre_doctor,
                'nombre_clinica': reser.nombre_clinica,
                'comuna_clinica': reser.comuna_clinica,
                'direccion_clinica': reser.direccion_clinica,
            })
        #
        return Response({'pacientes':arr},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Rerva Paciente desde el Panel Paciente.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_reserva_panel_pac(request):
    try:
        #print(request.data)
        print("Ingresamos a la reserva del Panel PACIENTE.")
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        print(data)
        #
        usuario = request.user.id
        grupos = request.user.groups.values_list('name', flat=True)
        usuario_creacion_reserva = None
        #
        porcentaje_desc = None
        #
        if 'Paciente' in grupos:
            usuario_creacion = PacienteModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Doctor' in grupos:
            usuario_creacion = DoctorModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Secretaria' in grupos:
            usuario_creacion = SecretariaModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        #
        if 'Administrador' in grupos:
            # usuario_creacion = SecretariaModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = 'Administrador'
            data['usuario_creacion_reserva'] = usuario_creacion_reserva

        fecha = data.get("fecha_reserva")
        #
        fecha_formateada = fecha.split("T")[0]  # Esto nos dará "2025-04-10"
        data['fecha_reserva'] = fecha_formateada
        id_user_pac = CustomersUsers.objects.get(pk=data.get("fk_usuario"))
        #data.update({'fk_usuario_id': id_user_pac.id})
        list_pac = []
        reserva = str(uuid.uuid4())
        reserva_uuid = reserva
        data['reserva_uuid'] = reserva_uuid
        id_usuario_existe = data['fk_usuario']
        especialidad_existe = data['especialidad']
        fecha_reserva = data['fecha_reserva']
        # Convertir string a date
        fecha_reserva_obj = datetime.strptime(fecha_reserva, "%Y-%m-%d").date()
        hoy = date.today()
        verificar = ReservaModel.objects.filter(especialidad=especialidad_existe, fecha_reserva=fecha_reserva_obj,fk_usuario=id_usuario_existe)
        # Verificamos si existe un reserva previa de la misma especialidad en el mismo día.
        if verificar.exists():
            return Response({'error':1},
                # Específicamos el status.
                status=status.HTTP_400_BAD_REQUEST)
        # Obtenemos el valor de la especialidad.
        valor_esp = Especialidad.objects.get(nombre_especialidad=data["especialidad"])
        valor_especialidad = int(valor_esp.valor_especialidad)
        # Verificar si tiene código de descuento.
        # Verificamosel tipo de pago.
        metodo_pago = data['tipo_pago']
        pago_debito = []
        pago_creito = []
        cant_cuotas = data['cuotas']
        valor_real_desc_credito = None
        valor_desc_debito = None
        valor_des_cuotas = None
        valor_descuento_monto = None
        res_nombre_paciente = None
        # Validacion de coutas y cant cuotas.
        if metodo_pago == "1":
            if cant_cuotas == "":
                return Response({'error': 2}, status=status.HTTP_400_BAD_REQUEST)
        res = ReservaSerializer(data=data)
        if res.is_valid():
            res.save()
            # Obtenemos el cod de descuento para verificar.
            cod = data.get("cod")
            verificar_cod = DescuentoModel.objects.filter(cod_descuento=cod)
            descuento_aplicado = None
            descuento_real = None
            if verificar_cod.exists():
                for verificar in verificar_cod:
                    fecha_termino = verificar.fecha_termino
                    # obtenemos el descuento.
                    descuento = int(verificar.descuento)
                    # Verificamos la fecha de la reserva.
                    if hoy > fecha_termino:
                        descuento_real = valor_especialidad
                        pass
                    #
                    if hoy <= fecha_termino:
                        # Para aplicar el descuento, concatenamos antes un número 0.

                        descuento_aplicado = int((valor_especialidad * descuento) / 100)
                        # Aplicamos las cuotas sobre el valor total con descuento incluido.
                        descuento_real = int(valor_especialidad - descuento_aplicado)
                        print(descuento_real)
                        #
                        paciente = PacienteModel.objects.get(fk_user=id_user_pac.id)
                        #
                        verificar_cod = DescuentoModel.objects.get(cod_descuento=cod)
                        porcentaje_desc = verificar_cod.descuento
                        verificar_pac_cod = DescuentoPaciente.objects.filter(fk_paciente=paciente.id, fk_descuento=verificar_cod.id)
                        #
                        if not verificar_pac_cod.exists():
                            #
                            pac_desc = {
                                'total_pagar': valor_especialidad,
                                'total_pagar_descuento': descuento_real,
                                'fecha_utilizacion': hoy,
                                'fk_descuento': verificar_cod.id,
                                'fk_paciente': paciente.id,
                            }
                            #
                            asignado = DescuentoPacienteSerializer(data=pac_desc)
                            if asignado.is_valid():
                                asignado.save()
                                valor_real_desc_credito = 1
                                valor_desc_debito = 1
                                print("Aplicamos descuento")

                        else:
                            descuento_real = valor_especialidad
            else:
                descuento_real = valor_especialidad
            # Obtenemos la instancia para obtener el id.
            id_reserva_insertada = res.instance.id
            #
            if metodo_pago == '1':
                #
                credito = str(uuid.uuid4())
                credito_uuid = credito
                cant_cuotas = int(data['cuotas'])
                monto_cuota = int(valor_especialidad / cant_cuotas)
                pago_credito = ({
                    'credito': metodo_pago,
                    'fecha_pago': hoy,
                    'credito_uuid': credito_uuid,
                    'monto': descuento_real,
                    'cant_cuotas': cant_cuotas,
                    'monto_total': descuento_real,
                    'monto_cuotas' : monto_cuota,
                    'fk_reserva': id_reserva_insertada
                })
                credito = CreditoSerializer(data=pago_credito)
                if credito.is_valid():
                    credito.save()
                    reserva_user = ReservaModel.objects.filter(fk_usuario=request.data["fk_usuario"])
                    # Obtenemos los datos del paciente.
                    pac = PacienteModel.objects.get(fk_user=request.data["fk_usuario"])
                    #reserva_user_paciente = ReservaSerializer(reserva_user, many=True)
                    # Obtener los datos para el correo.
                    reserva_nueva = ReservaModel.objects.get(pk=id_reserva_insertada)
                    # Creación del correo.
                    subject = "Correo de Verificación de Reserva"
                    # Realizamos el descuento a la cantidad de cuotas si aplica.
                    if valor_real_desc_credito == 1:
                        valor_descuento_monto = int(descuento_real / cant_cuotas)
                        res_nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
                        # Crearemos el envío de correos CON DESCUENTO.
                        template = render_to_string("pacientes/correo_reserva.html",{
                            'nombre_paciente': res_nombre_paciente,
                            'rut_paciente': pac.rut,
                            'email_paciente': id_user_pac.email,
                            'fono_paciente': pac.fono,
                            'fecha_reserva': reserva_nueva.fecha_reserva,
                            'especialidad': reserva_nueva.especialidad,
                            'valor_especialidad': valor_especialidad,
                            'nombre_doctor': reserva_nueva.nombre_doctor,
                            'reserva_uuid': reserva_nueva.reserva_uuid,
                            'comuna_clinica': reserva_nueva.comuna_clinica,
                            'direccion_clinica': reserva_nueva.direccion_clinica,
                            'nombre_clinica': reserva_nueva.nombre_clinica,
                            'hora_inicio': reserva_nueva.hora_inicio,
                            'hora_termino': reserva_nueva.hora_termino,
                            'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
                            'reserva_pagada': 'Sí',
                            'tipo_pago': 'Crédito',
                            'valor_base': valor_especialidad,
                            'descuento': porcentaje_desc,
                            'total_pagar': descuento_real,
                            'credito': metodo_pago,
                            'fecha_pago': hoy,
                            'credito_uuid': credito_uuid,
                            'cant_cuotas': cant_cuotas,
                            'monto_total': valor_descuento_monto,
                            'monto_cuotas' : valor_descuento_monto,
                        })
                    else:
                        res_nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
                        # Crearemos el envío de correos SIN DESCUENTO.
                        template = render_to_string("pacientes/correo_reserva.html",{
                                'nombre_paciente': res_nombre_paciente,
                                'rut_paciente': pac.rut,
                                'email_paciente': id_user_pac.email,
                                'fono_paciente': pac.fono,
                                'fecha_reserva': reserva_nueva.fecha_reserva,
                                'especialidad': reserva_nueva.especialidad,
                                'valor_especialidad': valor_especialidad,
                                'nombre_doctor': reserva_nueva.nombre_doctor,
                                'reserva_uuid': reserva_nueva.reserva_uuid,
                                'comuna_clinica': reserva_nueva.comuna_clinica,
                                'direccion_clinica': reserva_nueva.direccion_clinica,
                                'nombre_clinica': reserva_nueva.nombre_clinica,
                                'hora_inicio': reserva_nueva.hora_inicio,
                                'hora_termino': reserva_nueva.hora_termino,
                                'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
                                'reserva_pagada': 'Sí',
                                'tipo_pago': 'Crédito',
                                'valor_base': valor_especialidad,
                                'descuento': "No aplica",
                                'total_pagar': valor_especialidad,
                                'credito': metodo_pago,
                                'fecha_pago': hoy,
                                'credito_uuid': credito_uuid,
                                'cant_cuotas': cant_cuotas,
                                'monto_total': valor_des_cuotas,
                                'monto_cuotas' : monto_cuota,
                            })
                    #
                    emailSender = EmailMessage(
                        subject,
                        template,
                        settings.EMAIL_HOST_USER,
                        ["matiasfamilycrew@gmail.com"],
                    )
                    # print("Creacion del correo ")
                    # Formato del mensaje en HTML.
                    emailSender.content_subtype = "html"
                    emailSender.fail_silently = False
                    # Agregamos el PDF que hemos creado como adjunto al correo.
                    pdf_panel_paciente(template,res_nombre_paciente, emailSender)
                    # Enviamos el correo.
                    emailSender.send()
                    todas_reservas = ReservaModel.objects.all()
                    todas_reservas_data = ReservaSerializer(todas_reservas, many=True)
                    #
                    return Response({'pacientes':todas_reservas_data.data},
                            # Específicamos el status.
                            status=status.HTTP_200_OK)
            if metodo_pago == '0':
                #
                debitos = str(uuid.uuid4())
                debito_uuid = debitos
                pago_debito = ({
                    'debito': metodo_pago,
                    'monto': valor_especialidad,
                    'monto_total': descuento_real,
                    'debito_uuid': debito_uuid,
                    'fecha_pago': hoy,
                    'fk_reserva': id_reserva_insertada
                })
                debito = DebitoSerializer(data=pago_debito)
                if debito.is_valid():
                    debito.save()
                    reserva_user = ReservaModel.objects.filter(fk_usuario=request.data["fk_usuario"])
                    print(reserva_user)
                    # Obtenemos los datos del paciente.
                    pac = PacienteModel.objects.get(fk_user=request.data["fk_usuario"])
                    #reserva_user_paciente = ReservaSerializer(reserva_user, many=True)
                    # Obtener los datos para el correo.
                    reserva_nueva = ReservaModel.objects.get(pk=id_reserva_insertada)
                    # Creación del correo.
                    subject = "Correo de Verificación de Compras"
                    print(valor_desc_debito)
                    if valor_desc_debito == 1:
                        res_nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
                        print(res_nombre_paciente)
                        # Crearemos el envío de correos.
                        template = render_to_string("pacientes/correo_reserva.html",{
                            'nombre_paciente': res_nombre_paciente,
                            'rut_paciente': pac.rut,
                            'email_paciente': id_user_pac.email,
                            'fono_paciente': pac.fono,
                            'fecha_reserva': reserva_nueva.fecha_reserva,
                            'especialidad': reserva_nueva.especialidad,
                            'valor_especialidad': valor_especialidad,
                            'nombre_doctor': reserva_nueva.nombre_doctor,
                            'reserva_uuid': reserva_nueva.reserva_uuid,
                            'comuna_clinica': reserva_nueva.comuna_clinica,
                            'direccion_clinica': reserva_nueva.direccion_clinica,
                            'nombre_clinica': reserva_nueva.nombre_clinica,
                            'hora_inicio': reserva_nueva.hora_inicio,
                            'hora_termino': reserva_nueva.hora_termino,
                            'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
                            'reserva_pagada': 'Sí',
                            'tipo_pago': 'Débito',
                            'valor_base': valor_especialidad,
                            'descuento': porcentaje_desc,
                            'total_pagar': descuento_real,
                        })
                    # Envío del mensaje. Debemos pasar el template.
                    else:
                        res_nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
                        print(res_nombre_paciente)
                        # Crearemos el envío de correos.
                        template = render_to_string("pacientes/correo_reserva.html",{
                            'nombre_paciente': res_nombre_paciente,
                            'rut_paciente': pac.rut,
                            'email_paciente': id_user_pac.email,
                            'fono_paciente': pac.fono,
                            'fecha_reserva': reserva_nueva.fecha_reserva,
                            'especialidad': reserva_nueva.especialidad,
                            'valor_especialidad': valor_especialidad,
                            'nombre_doctor': reserva_nueva.nombre_doctor,
                            'reserva_uuid': reserva_nueva.reserva_uuid,
                            'comuna_clinica': reserva_nueva.comuna_clinica,
                            'direccion_clinica': reserva_nueva.direccion_clinica,
                            'nombre_clinica': reserva_nueva.nombre_clinica,
                            'hora_inicio': reserva_nueva.hora_inicio,
                            'hora_termino': reserva_nueva.hora_termino,
                            'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
                            'reserva_pagada': 'Sí',
                            'tipo_pago': 'Débito',
                            'valor_base': valor_especialidad,
                            'descuento': 'No Aplica',
                            'total_pagar': valor_especialidad,
                        })
                    #
                    emailSender = EmailMessage(
                        subject,
                        template,
                        settings.EMAIL_HOST_USER,
                        ["matiasfamilycrew@gmail.com"],
                    )
                    # print("Creacion del correo ")
                    # Formato del mensaje en HTML.
                    emailSender.content_subtype = "html"
                    emailSender.fail_silently = False
                    # Agregamos el PDF que hemos creado como adjunto al correo.
                    pdf_panel_paciente(template, res_nombre_paciente, emailSender)
                    # Enviamos el correo.
                    emailSender.send()
                    todas_reservas = ReservaModel.objects.all()
                    todas_reservas_data = ReservaSerializer(todas_reservas, many=True)
                    #
                    return Response({'pacientes':todas_reservas_data.data},
                            # Específicamos el status.
                            status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Crear la reserva desde el panel de ADMIN.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_reserva_panel_admin(request):
    try:
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        print(data)
        #
        usuario = request.user.id
        print(usuario)
        es_superusuario = request.user.is_superuser
        print("Tipo Usuario")
        print(es_superusuario)
        print("Tipo Usuario")
        usuario_creacion_reserva = None
        #
        if es_superusuario == 1:
            data['usuario_creacion_reserva'] = "Administrador"
        #
        fecha = data.get("fecha_reserva")
        #
        fecha_formateada = fecha.split("T")[0]  # Esto nos dará "2025-04-10"
        data['fecha_reserva'] = fecha_formateada
        id_user_pac = CustomersUsers.objects.get(pk=data.get("fk_usuario"))
        #data.update({'fk_usuario_id': id_user_pac.id})
        list_pac = []
        reserva = str(uuid.uuid4())
        reserva_uuid = reserva
        data['reserva_uuid'] = reserva_uuid
        id_usuario_existe = data['fk_usuario']
        especialidad_existe = data['especialidad']
        fecha_reserva = data['fecha_reserva']
        # Convertir string a date
        fecha_reserva_obj = datetime.strptime(fecha_reserva, "%Y-%m-%d").date()
        hoy = date.today()
        verificar = ReservaModel.objects.filter(especialidad=especialidad_existe, fecha_reserva=fecha_reserva_obj,fk_usuario=id_usuario_existe)
        if verificar.exists():
            return Response({'error':1},
                # Específicamos el status.
                status=status.HTTP_400_BAD_REQUEST)
        # Obtenemos el valor de la especialidad.
        valor_esp = Especialidad.objects.get(nombre_especialidad=data["especialidad"])
        valor_especialidad = int(valor_esp.valor_especialidad)
        print(valor_especialidad)
        res = ReservaSerializer(data=data)
        print("Pasamos")
        if res.is_valid():
            id_reserva_insertada = res.save()
            id_reserva = id_reserva_insertada.id
            reserva_user = ReservaModel.objects.filter(fk_usuario=request.data["fk_usuario"])
            # Obtenemos los datos del paciente.
            pac = PacienteModel.objects.get(fk_user=request.data["fk_usuario"])
            #reserva_user_paciente = ReservaSerializer(reserva_user, many=True)
            # Obtener los datos para el correo.
            reserva_nueva = ReservaModel.objects.get(pk=id_reserva)
            dato_cita = []
            dato_cita.append({
                'nombre_paciente': pac.primer_nombre + ' ' + pac.segundo_nombre  + ' ' + pac.ap_paterno + ' ' + pac.ap_materno,
                'rut_paciente': pac.rut,
                'email_paciente': id_user_pac.email,
                'fono_paciente': pac.fono,
                'fecha_reserva': reserva_nueva.fecha_reserva,
                'especialidad': reserva_nueva.especialidad,
                'nombre_doctor': reserva_nueva.nombre_doctor,
                'reserva_uuid': reserva_nueva.reserva_uuid,
                'comuna_clinica': reserva_nueva.comuna_clinica,
                'direccion_clinica': reserva_nueva.direccion_clinica,
                'nombre_clinica': reserva_nueva.nombre_clinica,
                'hora_inicio': reserva_nueva.hora_inicio,
                'hora_termino': reserva_nueva.hora_termino,
                'valor_especialidad': valor_especialidad,
                'monto': valor_especialidad,
                'total_pagar': valor_especialidad,
                'valor_base': valor_especialidad,
                'fecha_creacion_reserva': reserva_nueva.fecha_creacion_reserva,
                'reserva_pagada': "No",
            })
            correo_reserva_cita(dato_cita)
            todas_reservas = ReservaModel.objects.all()
            todas_reservas_data = ReservaSerializer(todas_reservas, many=True)
            #
            return Response({'pacientes':todas_reservas_data.data},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Crear Reserva desde el panel Secretaria.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_reserva_pac_registrado_secretaria(request):
    try:
        print("crear_reserva_pac_registrado_secretaria")
        # Esto se hace para poder agregar mas data al array de objetos.
        data = request.data.copy()
        print(data)
        # Extraer y convertir la fecha
        fecha_original = data.get("fecha_reserva")
        fecha_objeto = datetime.fromisoformat(fecha_original.replace("Z", ""))
        # Formato correcto para DateField
        fecha_formateada = fecha_objeto.strftime("%Y-%m-%d")
        # Reemplazar en el diccionario
        data["fecha_reserva"] = fecha_formateada
        print(fecha_formateada)
        print(data["hora_inicio"])
        res = ReservaModel.objects.filter(
            nombre_doctor=data["nombre_doctor"],
            especialidad=data["especialidad"],
            fecha_reserva=data["fecha_reserva"],
            hora_inicio=data["hora_inicio"]
        )
        if res.exists():
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        reserva = str(uuid.uuid4())
        data["reserva_uuid"] = reserva
        usuario = request.user.id
        grupos = request.user.groups.values_list('name', flat=True)
        # Obtener los grupos del usuario
        if 'Secretaria' in grupos:
            usuario_creacion = SecretariaModel.objects.get(fk_user=usuario)
            usuario_creacion_reserva = usuario_creacion.primer_nombre + " " + usuario_creacion.segundo_nombre + " " + usuario_creacion.ap_paterno + " " + usuario_creacion.ap_materno
            data['usuario_creacion_reserva'] = usuario_creacion_reserva
        print(data)
        # Guardamos en la BD.
        data_save = ReservaSerializer(data=data)
        if data_save.is_valid():
            data_save.save()
            dato_cita = []
            paciente = PacienteModel.objects.get(fk_user=data["fk_usuario"])
            user = CustomersUsers.objects.get(pk=data["fk_usuario"])
            espe = Especialidad.objects.get(nombre_especialidad=data["especialidad"])
            fecha_hoy = date.today()
            dato_cita.append({
                'nombre_paciente': paciente.primer_nombre + ' ' + paciente.segundo_nombre  + ' ' + paciente.ap_paterno + ' ' + paciente.ap_materno,
                'rut_paciente': paciente.rut,
                'email_paciente': user.email,
                'fono_paciente': paciente.fono,
                'fecha_reserva': data["fecha_reserva"],
                'especialidad': data["especialidad"],
                'nombre_doctor': data["nombre_doctor"],
                'reserva_uuid': data["reserva_uuid"],
                'comuna_clinica': data["comuna_clinica"],
                'direccion_clinica': data["direccion_clinica"],
                'nombre_clinica': data["nombre_clinica"],
                'hora_inicio': data["hora_inicio"],
                'hora_termino': data["hora_termino"],
                'valor_especialidad': espe.valor_especialidad,
                'total_pagar': espe.valor_especialidad,
                'fecha_creacion_reserva': fecha_hoy,
                'reserva_pagada': "No",
                'valor_base': espe.valor_especialidad,
            })
            print(dato_cita)
            correo_reserva_cita(dato_cita)
            todas_reservas = ReservaModel.objects.filter(nombre_doctor=data["nombre_doctor"], especialidad=data["especialidad"])
            reserv_doc = []
            for res in todas_reservas:
                reserv_doc.append({
                    'title': res.especialidad,
                    'start': res.hora_inicio,
                    'end': res.hora_termino,
                    'reserva_uuid': res.reserva_uuid,
                })
            return Response({'pacientes':reserv_doc},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Obtener la ESPECIALIDAD para la reserva desde el panel de PACIENTE REGISTRADO.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def esp_panel_pac_registrado(request):
    try:
        print("esp_panel_pac_registrado")
        especialidad = Especialidad.objects.all()
        especialidad_data = EspecialidadSerializers(especialidad, many=True)
        return Response({'especialidades':especialidad_data.data},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Correo de Reserva de hora por el ADMIN y Secretaria.
def correo_reserva_cita(dato_cita):
    try:
        print("Ingresamos al Correo.....")
        # Creación del correo.
        subject = "Correo de Verificación de Reseva Cita"
        nombre_paciente = None
        # Recibimos el el diccionarios conlos datos.
        for dato in dato_cita:
            nombre_paciente = dato["nombre_paciente"]
            print("Nombre del Paciente")
            print(nombre_paciente)
            print("Nombre del Paciente")
            # Crearemos el envío de correos.
            template = render_to_string("pacientes/correo_reserva.html", dato)
            emailSender = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ["matiasfamilycrew@gmail.com"],
            )
            # print("Creacion del correo ")
            # Formato del mensaje en HTML.
            emailSender.content_subtype = "html"
            emailSender.fail_silently = False
            # Enviamos el correo.
            pdf_reserva(template, nombre_paciente,emailSender)
            emailSender.send()

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Creación PDF de Reseva creada solamente por el Administrador y Secretaria.
def pdf_reserva(template, nombre_paciente, emailSender):
    try:
        print("Ingresamos al PDF.")
        # print(nombre_paciente)
        # # Ruta base de la carpeta donde se almacenan los PDF.
        # carpeta_destino = "C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\BOLETA_PDF_PACIENTES"
        # # Verificar si la carpeta existe, si no, la debemos crear.
        # if not os.path.exists(carpeta_destino):
        #     os.makedirs(carpeta_destino)
        #     print(f"Carpeta creada: {carpeta_destino}")
        # else:
        #     pass
        # # Generación del nombre de archivo único
        # now = datetime.now()
        # filename = f"Boleta_{nombre_paciente}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        # # Creación del PDF.
        # # Configuración de pdfkit
        # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        # options = {'enable-local-file-access': None}
        # # Generar el PDF
        # # template; Pertenece
        # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}", configuration=config, options=options)
        # #Envío del mensaje. Debemos pasar el template.
        # emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}")
        print(f"Generando para: {nombre_paciente}")

        # 1. Definimos la carpeta de destino usando BASE_DIR (Universal)
        # Esto elimina la ruta fija C:\\Users\\Plask91... que falla en Linux
        carpeta_destino = os.path.join(settings.BASE_DIR, 'BOLETA_PDF_PACIENTES')

        # Verificar si la carpeta existe, si no, la creamos
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            print(f"Carpeta creada: {carpeta_destino}")

        # 2. Generación del nombre de archivo único
        now = datetime.now()
        # Limpiamos el nombre para evitar caracteres extraños en rutas Linux
        nombre_limpio = nombre_paciente.replace(" ", "_")
        filename = f"Boleta_{nombre_limpio}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

        # 3. Ruta completa final (Dinámica)
        ruta_completa_pdf = os.path.join(carpeta_destino, filename)

        # 4. Configuración de pdfkit según el Sistema Operativo
        # Evita el error de "wkhtmltopdf.exe" en PythonAnywhere
        if os.name == 'nt': # Si es Windows
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else: # Si es Linux (PythonAnywhere)
            # En Linux suele estar en el PATH global, no necesita ruta al .exe
            config = pdfkit.configuration()

        options = {'enable-local-file-access': None}

        # 5. Generar el PDF usando la ruta dinámica
        # Reemplazamos las rutas hardcoded de Windows por ruta_completa_pdf
        pdfkit.from_string(template, ruta_completa_pdf, configuration=config, options=options)

        # 6. Envío del mensaje adjuntando el archivo generado
        emailSender.attach_file(ruta_completa_pdf)

        print(f"PDF generado y adjuntado correctamente: {filename}")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Creación PDF reserva panel PACIENTE REGISTRADO pagando la reserva creada por la SECRETARIA.
def pdf_panel_paciente(template, nombre_paciente, emailSender):
    try:
        print("Creación PDF Paciente Panel Paciente")
        print("Ingresamos al PDF.")
        print(nombre_paciente)
        # Ruta base de la carpeta donde se almacenan los PDF.
        carpeta_destino = os.path.join(settings.BASE_DIR, 'BOLETA_PDF_PACIENTES')
        # Verificar si la carpeta existe, si no, la debemos crear.
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            print(f"Carpeta creada: {carpeta_destino}")
        # Generación del nombre de archivo único
        now = datetime.now()
        filename = f"Boleta_Compra_{nombre_paciente}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        # Creación del PDF.
        # Configuración de pdfkit
        # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        # options = {'enable-local-file-access': None}
        # # Generar el PDF
        # # template; Pertenece
        # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}", configuration=config, options=options)
        ##Este pedazo de codigo sirve para cambiar las rutas / windows a Linux/.
        # En PythonAnywhere no necesitas la ruta al .exe de Windows
        # Puedes intentar omitir la configuración o usar una condicional:
        if os.name == 'nt': # Si es Windows
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else: # Si es Linux (PythonAnywhere)
            config = pdfkit.configuration() # Por defecto busca en /usr/bin/wkhtmltopdf

        options = {'enable-local-file-access': None}

        # 3. Ruta completa del archivo PDF
        ruta_completa_pdf = os.path.join(carpeta_destino, filename)

        # Generar el PDF
        pdfkit.from_string(template, ruta_completa_pdf, configuration=config, options=options)

        # Envío del mensaje
        emailSender.attach_file(ruta_completa_pdf)
        ##########################################################################
        #Envío del mensaje. Debemos pasar el template.
        #emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)


# Crear Paciente Panel ADMIN.
def correo_dato_inicial_pac_registrado(primer_nombre, segundo_nombre, ap_paterno, ap_materno, rut, username, password, email):
    try:
        print("correo_dato_inicial_pac_registrado")
        # Pasamos los datos al template.
        dato = {
            "primer_nombre": primer_nombre,
            "segundo_nombre": segundo_nombre,
            "ap_paterno": ap_paterno,
            "ap_materno": ap_materno,
            "rut": rut,
            "username": username,
            "password": password,
            "email": email,
        }
        # Creación del correo.
        subject = "Correo Dato Login Paciente Registrado"
        nombre_paciente = f"{primer_nombre}_{ap_paterno}"

        # 1. Definimos la carpeta de destino usando BASE_DIR (Universal para Windows/Linux)
        carpeta_destino = os.path.join(settings.BASE_DIR, 'BOLETA_PDF_PACIENTES')

        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            print(f"Carpeta creada: {carpeta_destino}")

        # 2. Generación del nombre de archivo y ruta completa
        now = datetime.now()
        filename = f"Dato_Inicial_{nombre_paciente}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        ruta_completa_pdf = os.path.join(carpeta_destino, filename)

        # 3. Configuración de pdfkit (Detección automática de SO)
        if os.name == 'nt': # Si es Windows
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else: # Si es Linux (PythonAnywhere)
            config = pdfkit.configuration()

        options = {'enable-local-file-access': None}

        # 4. Renderizamos el template (Usamos "/" para compatibilidad)
        template_html = render_to_string("pacientes/correo_pac_dato_register.html", dato)

        # 5. Generar el PDF usando la ruta dinámica
        # Eliminamos la ruta fija "C:\\Users..." y usamos ruta_completa_pdf
        pdfkit.from_string(template_html, ruta_completa_pdf, configuration=config, options=options)

        # 6. Preparar y enviar el correo
        emailSender = EmailMessage(
            subject,
            template_html,
            settings.EMAIL_HOST_USER,
            ["matiasfamilycrew@gmail.com"], # O podrías usar la variable 'email'
        )

        emailSender.content_subtype = "html"
        emailSender.fail_silently = False

        # Adjuntamos usando la ruta dinámica
        emailSender.attach_file(ruta_completa_pdf)

        emailSender.send()
        print("Correo enviado exitosamente.")
        return Response({'pacientes':1},
                                    # Específicamos el status.
                                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)