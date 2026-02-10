from django.shortcuts import render
# Validador de rut.
from reserva import validar_rut
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import authentication_classes, permission_classes, api_view
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
from .models import ReservaModel
from .serializers import ReservaSerializer
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
#----- Librería para crear PDF -------------------------------------------------
import pdfkit
#----- Fin Librería para crear PDF ---------------------------------------------
#
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature



# Create your views here.
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_clinica_index(request):
    try:
        clinica = ComunaClinicaModel.objects.all()
        arr = []
        for cli in clinica:
            arr.append({
                'id': cli.id,
                'nombre_clinica': cli.nombre_clinica,
                'comuna_clinica': cli.comuna_clinica,
                'direccion_clinica': cli.direccion_clinica
            })
        return Response({'list_clinica':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_esp_index(request, id):
    try:
        # Obtenemos la clinica.
        clinica = ComunaClinicaModel.objects.get(pk=id)
        #
        doctores = clinica.doctormodel_set.all()
        print(doctores)
        # Obtenemos todas las especialidades de esos doctores
        especialidades = Especialidad.objects.filter(doctormodel__in=doctores).distinct()
        print(especialidades)
        # Obtener el grupo por nombre
        especialidad_Serializers = EspecialidadSerializers(especialidades, many=True)
        return Response({'especialidad':especialidad_Serializers.data},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_doc_index(request, id_clinica, id_especialidad):
    try:
        # # Obtenemos las Clínica.
        # clinica = ComunaClinicaModel.objects.get(pk=id_clinica)
        # print(clinica.nombre_clinica)
        # # print(id_especialidad)
        # # Obtener el grupo por nombre.
        # especialidad = Especialidad.objects.get(pk=id_especialidad)
        # # print(especialidad.id)
        # # Filtrar a los doctores que tienen esta especialidad (usamos el nombre correcto de la relación)
        # usuarios = CustomersUsers.objects.filter(especialidades=especialidad)
        # arr = []
        # for ser in serializer.data:
        #     nombre_completo = ser["first_name"] + ' ' + ser["last_name"]
        #     arr.append(nombre_completo)
        # Obtenemos la clínica y la especialidad
        clinica = ComunaClinicaModel.objects.get(pk=id_clinica)
        especialidad = Especialidad.objects.get(pk=id_especialidad)
        # Filtramos doctores que estén en esa clínica y tengan esa especialidad
        doctores = DoctorModel.objects.filter(
            doctor_clinica=clinica,
            especialidades=especialidad
        ).select_related('fk_user')  # Para acceder al usuario sin hacer muchas queries
        arr = []
        # Armamos la lista de nombres completos desde fk_user
        for doctor in doctores:
            user = doctor.fk_user
            arr.append({
                'id_doctor': doctor.id,
                'primer_nombre': doctor.primer_nombre,
                'segundo_nombre': doctor.segundo_nombre,
                'ap_paterno': doctor.ap_paterno,
                'ap_materno': doctor.ap_materno,
            })
        #
        return Response({'doctores':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Datos para full Callendar.
@api_view(['POST'])
@permission_classes([AllowAny])
def reserva_paciente_index(request):
    try:
        print(request.data)
        data = request.data.copy()
        id_clinica = data.get("id_clinica")
        id_especialidad = data.get("id_especialidad")
        id_doctor = data.get("id_doctor")
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        email = data.get("email")
        edad = data.get("edad")
        fono = str(data.get("fono"))
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        sexo = data.get("sexo")
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        # Validamos que ls datos no se encuentre vacíos.
        if not all([id_clinica, id_especialidad, id_doctor, primer_nombre, segundo_nombre, ap_paterno, ap_materno, email, edad, fono, rut, sexo]):
            return Response({'error': 0}, status=status.HTTP_400_BAD_REQUEST)
        # Nombre de la Clínica.
        clinica = ComunaClinicaModel.objects.get(pk=id_clinica)
        nombre_clinica = clinica.nombre_clinica
        direccion_clinica = clinica.direccion_clinica
        comuna_clinica = clinica.comuna_clinica
        # Nombre Especialidad.
        especialidad = Especialidad.objects.get(pk=id_especialidad)
        nombre_especialidad = especialidad.nombre_especialidad
        # DOCTOR.
        doctor = DoctorModel.objects.get(pk=id_doctor)
        nombre_doctor = doctor.primer_nombre + " " + doctor.segundo_nombre + " " + doctor.ap_paterno + " " + doctor.ap_materno
        # Filtración de las Reservas.
        reserva = ReservaModel.objects.filter(nombre_doctor=nombre_doctor, especialidad=nombre_especialidad, nombre_clinica=nombre_clinica)
        # Array.
        arr = []
        for res in reserva:
            # Formateamos la fecha para mostrarla en los eventos de Full Callendar.
            fecha = res.fecha_reserva.strftime('%Y-%m-%d')
            # Formato de hora para mostrar en los eventos de Full Callendar.
            hora_inicio = res.hora_inicio.strftime('%H:%M:%S')
            hora_termino = res.hora_termino.strftime('%H:%M:%S')
            arr.append({
                'id_reserva': res.id,
                'nombre_doctor': res.nombre_doctor,
                'title': res.especialidad,
                'nombre_clinica': res.nombre_clinica,
                'start': f"{fecha}T{hora_inicio}",
                'end': f"{fecha}T{hora_termino}",
                'direccion_clinica': direccion_clinica,
                'comuna_clinica': comuna_clinica,
                'fecha_reserva': res.fecha_reserva,
            })
        return Response({'reserva':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['POST'])
@permission_classes([AllowAny])
def pago_debito_reserva_index(request):
    try:
        data = request.data.copy()
        print(data)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        # Capturamos la hora actual donde se realizó la reserva.
        # Zona horaria de Chile
        chile_tz = pytz.timezone('Chile/Continental')
        # Fecha y hora actual en Chile
        fecha_actual_chile = datetime.now(chile_tz)
        # Mostrar en el formato deseado
        print(fecha_actual_chile.strftime('%Y-%m-%d %H:%M:%S.%f'))
        nombre_paciente = data.get("nombre_paciente")
        email = data.get("email")
        edad = data.get("edad")
        sexo = data.get("sexo")
        fono = data.get("fono")
        # Validar la cantidad de caracteres del fono, deben ser 9 digitos y solo números.
        if not fono or not fono.isdigit() or len(fono) != 9:
            return Response({'error': 7}, status=status.HTTP_400_BAD_REQUEST)
        fono = f"+56{fono}"
        rut = data.get("rut")
        validar = validar_rut.validar_rut(rut)
        print(validar)
        if not validar:
            return Response({'error': 6}, status=status.HTTP_400_BAD_REQUEST)
        especialidad = data.get("especialidad")
        valor_esp = Especialidad.objects.get(nombre_especialidad=especialidad)
        #
        valor_especialidad = data.get("valor_especialidad")
        nombre_clinica = data.get("nombre_clinica")
        direccion_clinica = data.get("direccion_clinica")
        comuna_clinica = data.get("comuna_clinica")
        nombre_doctor = data.get("nombre_doctor")
        # Fecha recibida en formato DD-MM-YYYY
        fecha_reserva = data.get("fecha_reserva")
        # Convertir a objeto datetime
        fecha_reserva_obj = datetime.strptime(fecha_reserva, "%d-%m-%Y")
        # Formatear como YYYY-MM-DD
        fecha_reserva_formateada = fecha_reserva_obj.strftime("%Y-%m-%d")
        hora_inicio = data.get("hora_inicio")
        hora_termino = data.get("hora_termino")
        reserva_uuid = str(uuid.uuid4())
        pac_no_register_uuid = str(uuid.uuid4())
        #
        fk_user_exist = None
        deb = []
        arr = []
        # Verificar si existe reserva el mismo dia yh la misma hora, el mismo doctor, la misma especialidad, etc.
        veri_res = ReservaModel.objects.filter(fecha_reserva= fecha_reserva_formateada, hora_inicio= hora_inicio,nombre_doctor=nombre_doctor, especialidad=especialidad, nombre_clinica=nombre_clinica)
        if veri_res.exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        # Datos para el Full Calendar.
        full_calendar = []
        # Crear el paciente no registrado usando el serializer
        pac_data = {
            'primer_nombre': primer_nombre,
            'segundo_nombre': segundo_nombre,
            'ap_paterno': ap_paterno,
            'ap_materno': ap_materno,
            'edad': edad,
            'sexo': sexo,
            'rut': rut,
            'fono': fono,
            'email': email,
            'paciente_uuid': pac_no_register_uuid,
        }
        #
        pac_no_register_serializers = PacienteNoRegisterSerializer(data=pac_data)
        if pac_no_register_serializers.is_valid():
            pac_no_register = pac_no_register_serializers.save()
            # Crear la reserva
            arr = {
                'fecha_creacion_reserva':fecha_actual_chile,
                'usuario_creacion_reserva':nombre_paciente,
                'fecha_reserva':fecha_reserva_formateada,
                'hora_inicio':hora_inicio,
                'hora_termino':hora_termino,
                'especialidad':especialidad,
                'nombre_doctor':nombre_doctor,
                'tipo_pago':0,
                'reserva_uuid': reserva_uuid,
                'nombre_clinica':nombre_clinica,
                'direccion_clinica':direccion_clinica,
                'comuna_clinica':comuna_clinica,
                'pago_realizado': 1,
                'fk_pac_no_register':pac_no_register.id,
            }
            #
            reserva = ReservaSerializer(data=arr)
            if reserva.is_valid():
                res = reserva.save()
                deb = {
                    'debito': 0,
                    'fecha_pago': fecha_actual_chile.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'debito_uuid': str(uuid.uuid4()),
                    'monto': valor_esp.valor_especialidad,
                    'monto_total': valor_esp.valor_especialidad,
                    'fk_reserva': res.id,
                }
                #
                pago_debito = DebitoSerializer(data=deb)
                if pago_debito.is_valid():
                    pago_debito.save()
                    generar_correo_reserv_index(reserva_uuid, "0")
                    return Response({'reserva':reserva.data, 'debito':pago_debito.data},
                                    # Específicamos el status.
                                    status=status.HTTP_200_OK)
                else:
                    print(pago_debito.errors)
        else:
            print(pac_no_register_serializers.errors)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Pago reserva desde el index solo DÉBITO, paciente registrado y no registrado.
@api_view(['POST'])
@permission_classes([AllowAny])
def pago_credito_reserva_index(request):
    try:
        data = request.data.copy()
        print(data)
        primer_nombre = data.get("primer_nombre")
        segundo_nombre = data.get("segundo_nombre")
        ap_paterno = data.get("ap_paterno")
        ap_materno = data.get("ap_materno")
        # Capturamos la hora actual donde se realizó la reserva.
        # Zona horaria de Chile
        chile_tz = pytz.timezone('Chile/Continental')
        # Fecha y hora actual en Chile
        fecha_actual_chile = datetime.now(chile_tz)
        # Mostrar en el formato deseado
        print(fecha_actual_chile.strftime('%Y-%m-%d %H:%M:%S.%f'))
        nombre_paciente = data.get("nombre_paciente")
        email = data.get("email")
        edad = data.get("edad")
        sexo = data.get("sexo")
        cant_cuota = data.get("cant_cuotas")
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
        especialidad = data.get("especialidad")
        valor_esp = Especialidad.objects.get(nombre_especialidad=especialidad)
        #
        valor_especialidad = data.get("valor_especialidad")
        # Eliminar el símbolo de dólar y convertir a entero
        valor_limpio = int(valor_especialidad.replace("$", "").replace(".", "").strip())
        nombre_clinica = data.get("nombre_clinica")
        direccion_clinica = data.get("direccion_clinica")
        comuna_clinica = data.get("comuna_clinica")
        nombre_doctor = data.get("nombre_doctor")
        # Fecha recibida en formato DD-MM-YYYY
        fecha_reserva = data.get("fecha_reserva")
        # Convertir a objeto datetime
        fecha_reserva_obj = datetime.strptime(fecha_reserva, "%d-%m-%Y")
        # Formatear como YYYY-MM-DD
        fecha_reserva_formateada = fecha_reserva_obj.strftime("%Y-%m-%d")
        hora_inicio = data.get("hora_inicio")
        hora_termino = data.get("hora_termino")
        reserva_uuid = str(uuid.uuid4())
        #
        fk_user_exist = None
        deb = []
        arr = []
        # Datos para el Full Calendar.
        full_calendar = []
        # Verificar si existe reserva el mismo dia y la misma hora, el mismo doctor, la misma especialidad, etc.
        veri_res = ReservaModel.objects.filter(fecha_reserva= fecha_reserva_formateada, hora_inicio= hora_inicio,nombre_doctor=nombre_doctor, especialidad=especialidad, nombre_clinica=nombre_clinica)
        if veri_res.exists():
            return Response({'error': 8}, status=status.HTTP_400_BAD_REQUEST)
        # Agregaremos al nuevo paciente a la BD.
        pac_no_register = {
            'primer_nombre': primer_nombre,
            'segundo_nombre': segundo_nombre,
            'ap_paterno': ap_paterno,
            'ap_materno': ap_materno,
            'edad': edad,
            'sexo': sexo,
            'rut': rut,
            'fono': fono,
            'email': email,
            'paciente_uuid': str(uuid.uuid4()),
        }
        # Creamos el usuario no registrado.
        pac_no_register_serializers = PacienteNoRegisterSerializer(data=pac_no_register)
        if pac_no_register_serializers.is_valid():
            user = pac_no_register_serializers.save()
            print(type(user.id))
            # Crear la reserva
            arr = {
                'fecha_creacion_reserva':fecha_actual_chile,
                'usuario_creacion_reserva':nombre_paciente,
                'fecha_reserva':fecha_reserva_formateada,
                'hora_inicio':hora_inicio,
                'hora_termino':hora_termino,
                'especialidad':especialidad,
                'nombre_doctor':nombre_doctor,
                'tipo_pago':1,
                'reserva_uuid': reserva_uuid,
                'nombre_clinica':nombre_clinica,
                'direccion_clinica':direccion_clinica,
                'comuna_clinica':comuna_clinica,
                'pago_realizado': 1,
                'fk_pac_no_register':user.id,
            }
            reserva = ReservaSerializer(data=arr)
            if reserva.is_valid():
                res = reserva.save()
                # Redondeamos al entero más cercano.
                monto_cuotas = round(int(valor_esp.valor_especialidad) / int(cant_cuota))
                cred = {
                    'credito': 1,
                    'fecha_pago': fecha_actual_chile.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'credito_uuid': str(uuid.uuid4()),
                    'monto': valor_esp.valor_especialidad,
                    'cant_cuotas': cant_cuota,
                    'monto_total': valor_esp.valor_especialidad,
                    'monto_cuotas': monto_cuotas,
                    'fk_reserva': res.id,
                }
                #
                pago_credito = CreditoSerializer(data=cred)
                if pago_credito.is_valid():
                    pago_credito.save()
                    # Correo más PDF, para el usuario registrao por el rut.
                    generar_correo_reserv_index(reserva_uuid, "1")
                    # Filtración de las Reservas.
                    reser = ReservaModel.objects.filter(nombre_doctor=nombre_doctor, especialidad=especialidad, nombre_clinica=nombre_clinica)
                    for res in reser:
                        # Formateamos la fecha para mostrarla en los eventos de Full Callendar.
                        fecha = res.fecha_reserva.strftime('%Y-%m-%d')
                        # Formato de hora para mostrar en los eventos de Full Callendar.
                        hora_ini = res.hora_inicio.strftime('%H:%M:%S')
                        hora_ter = res.hora_termino.strftime('%H:%M:%S')
                        full_calendar.append({
                            'id_reserva': res.id,
                            'nombre_doctor': res.nombre_doctor,
                            'title': res.especialidad,
                            'nombre_clinica': res.nombre_clinica,
                            'start': f"{fecha}T{hora_ini}",
                            'end': f"{fecha}T{hora_ter}",
                            'direccion_clinica': direccion_clinica,
                            'comuna_clinica': comuna_clinica,
                            'fecha_reserva': res.fecha_reserva,
                        })
                    return Response({'reserva_pagada': full_calendar},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
            else:
                return Response({'error pagar Crédito': 6}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

# Método para generar el PDF de una cita reservada por el INDEX.
def generar_correo_reserv_index(reserva_uuid, tipo_pago):
    try:
        print("Ingresamos al CORREO INDEX DÉBITO")
        reserva = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
        metodo_pago = reserva.tipo_pago
        pac_no_register = reserva.fk_pac_no_register
        pac = PacienteNoRegisterModel.objects.get(pk=pac_no_register.id)
        print(pac.email)
        print(pac.id)
        id_usuario = pac.id
        # Datos del usuario.
        nombre_completo = pac.primer_nombre + " " + pac.segundo_nombre + " " + pac.ap_paterno + " " + pac.ap_materno
        rut = pac.rut
        fono = pac.fono
        email = pac.email
        fecha_reserva = reserva.fecha_reserva
        especialidad = reserva.especialidad
        valor_esp = Especialidad.objects.get(nombre_especialidad=reserva.especialidad)
        valor_base = valor_esp.valor_especialidad
        nombre_doctor = reserva.nombre_doctor
        reserva_uuid = reserva.reserva_uuid
        nombre_clinica = reserva.nombre_clinica
        comuna_clinica = reserva.comuna_clinica
        direccion_clinica = reserva.direccion_clinica
        nombre_doctor = reserva.nombre_doctor
        hora_inicio = reserva.hora_inicio
        hora_termino = reserva.hora_termino
        fecha_creacion_reserva = reserva.fecha_creacion_reserva
        tipo_pago = reserva.tipo_pago
        aplica_descuento = None
        debito = ""
        credito = ""
        if tipo_pago == "0":
            debito = "Débito"
        if tipo_pago == "1":
            credito = "Crédito"
        # Si existe descuento, guardamos los datos en estas variables.
        total_pagar = None;
        total_pagar_descuento = None;
        fecha_utilizacion = None;
        print(metodo_pago)
        descuento = None;
        #
        if metodo_pago == "0":
            debito = DebitoModel.objects.get(fk_reserva=reserva.id)
            total_pagar = "No Existen Datos"
            total_pagar_descuento = "No Existen Datos"
            fecha_utilizacion = "No Existen Datos"
            aplica_descuento = "No"
            # Creación del correo.
            subject = "Correo Verificación Reserva"
            # Crearemos el envío de correos.
            template = render_to_string("pacientes_no_registrado/correo_reserva.html",{
                'nombre_paciente': nombre_completo,
                'rut_paciente': rut,
                'email_paciente': email,
                'fono_paciente': fono,
                'fecha_reserva': fecha_reserva,
                'especialidad': especialidad,
                'nombre_doctor': nombre_doctor,
                'reserva_uuid': reserva_uuid,
                'comuna_clinica': comuna_clinica,
                'direccion_clinica': direccion_clinica,
                'nombre_clinica': nombre_clinica,
                'hora_inicio': hora_inicio,
                'hora_termino': hora_termino,
                'fecha_creacion_reserva': fecha_creacion_reserva,
                'total_pagar': valor_base,
                'tipo_pago': "Débito",
                'monto': debito.monto,
                'aplica_descuento': "No",
                'valor_especialidad': valor_base,
                'monto_total': debito.monto_total,
                'total_pagar_descuento': "No aplica",
                'fecha_utilizacion': "No aplica",
                'descuento': "No aplica",
                'reserva_pagada': 'Sí',
                'valor_base': valor_base,
            })
            # # Generar el PDF
            # nombre_carpeta = "Boleta_PDF_PACIENTES"
            # ruta = f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}"
            # if not os.path.exists(ruta):
            #     os.makedirs(ruta)
            #     print(f"Carpeta creada en: {ruta}")
            # else:
            #     pass
            # now = datetime.now()
            # filename = f"Boleta_Reserva_Cita_{nombre_completo}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            # # Creación del PDF.
            # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            # # Configuración de pdfkit
            # options = {
            #     'enable-local-file-access': None,
            #     # 'orientation': 'Landscape',
            #     # 'page-size': 'A4',
            #     # 'margin-top': '0.2in',
            #     # 'margin-bottom': '0.2in',
            #     # 'encoding': "UTF-8",
            # }
            # print("Adjunto..........")
            # # template; Pertenece
            # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}\\{filename}", configuration=config, options=options)
            # # Envío del mensaje. Debemos pasar el template.
            # emailSender = EmailMessage(
            #     subject,
            #     template,
            #     settings.EMAIL_HOST_USER,
            #     ["matiasfamilycrew@gmail.com"],
            # )
            # # print("Creacion del correo ")
            # # Formato del mensaje en HTML.
            # emailSender.content_subtype = "html"
            # emailSender.fail_silently = False
            # # Agregamos el PDF que hemos creado como adjunto al correo.
            # emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}\\{filename}")
            # # Enviamos el correo.
            # emailSender.send()
            # --- Generar el PDF ---
            nombre_carpeta = "Boleta_PDF_PACIENTES"

            # Usamos BASE_DIR para que la ruta sea automática según el sistema (Linux o Windows)
            # En PythonAnywhere esto apuntará a /home/tu-usuario/tu-proyecto/Boleta_PDF_PACIENTES
            ruta_carpeta = os.path.join(settings.BASE_DIR, nombre_carpeta)

            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
                print(f"Carpeta verificada/creada en: {ruta_carpeta}")

            now = datetime.now()
            # Limpiamos el nombre para evitar problemas de caracteres en Linux
            nombre_limpio = nombre_completo.replace(" ", "_")
            filename = f"Boleta_Reserva_Cita_{nombre_limpio}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

            # Definimos la ruta completa del archivo
            ruta_archivo_pdf = os.path.join(ruta_carpeta, filename)

            # --- Configuración de pdfkit ---
            # Detectamos el sistema para evitar el error de ruta del .exe en Linux
            if os.name == 'nt':  # Windows
                path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            else:  # Linux (PythonAnywhere)
                # En Linux suele estar instalado en el PATH global
                config = pdfkit.configuration()

            options = {
                'enable-local-file-access': None,
            }

            print("Generando PDF y adjuntando...")

            # Generar el PDF usando la ruta dinámica
            # Eliminamos las rutas C:\\Users... fijas que causan errores en Bash
            pdfkit.from_string(template, ruta_archivo_pdf, configuration=config, options=options)

            # --- Envío del mensaje ---
            emailSender = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ["matiasfamilycrew@gmail.com"],
            )

            emailSender.content_subtype = "html"
            emailSender.fail_silently = False

            # Agregamos el PDF usando la ruta dinámica universal
            emailSender.attach_file(ruta_archivo_pdf)

            # Enviamos el correo
            emailSender.send()
        #
        if metodo_pago == "1":
            print("Ingresamos al Crédito")
            metodo_credito = CreditoModel.objects.get(fk_reserva=reserva.id)
            # Creación del correo.
            subject = "Correo Verificación Reserva"
            # Crearemos el envío de correos.
            template = render_to_string("pacientes_no_registrado/correo_reserva.html",{
                'nombre_paciente': nombre_completo,
                'rut_paciente': rut,
                'email_paciente': email,
                'fono_paciente': fono,
                'fecha_reserva': fecha_reserva,
                'especialidad': especialidad,
                'nombre_doctor': nombre_doctor,
                'reserva_uuid': reserva_uuid,
                'comuna_clinica': comuna_clinica,
                'direccion_clinica': direccion_clinica,
                'nombre_clinica': nombre_clinica,
                'hora_inicio': hora_inicio,
                'hora_termino': hora_termino,
                'fecha_creacion_reserva': fecha_creacion_reserva,
                'tipo_pago': 'Crédito',
                'credito_uuid': metodo_credito.credito_uuid,
                'total_pagar': valor_base,
                'valor_especialidad': valor_base,
                'valor_base': valor_base,
                'descuento': 'No aplica',
                'fecha_utilizacion': fecha_utilizacion,
                'fecha_pago': metodo_credito.fecha_pago,
                'cant_cuotas': metodo_credito.cant_cuotas,
                'monto_total': metodo_credito.monto_total,
                'monto_cuotas': metodo_credito.monto_cuotas,
                'monto': metodo_credito.monto,
                'reserva_pagada': 'Sí',
            })
            # # Generar el PDF
            # ruta = f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\Boleta_PDF_PACIENTES"
            # if not os.path.exists(ruta):
            #     os.makedirs(ruta)
            #     print(f"Carpeta creada en: {ruta}")
            # else:
            #     pass
            # now = datetime.now()
            # filename = f"Boleta_Reserva_Cita_{nombre_completo}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            # # Creación del PDF.
            # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
            # options = {
            #     'enable-local-file-access': None,
            #     # 'orientation': 'Landscape',
            #     # 'page-size': 'A4',
            #     # 'margin-top': '0.2in',
            #     # 'margin-bottom': '0.2in',
            #     # 'encoding': "UTF-8",
            # }
            # print("Adjunto..........")
            # # template; Pertenece
            # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\Boleta_PDF_PACIENTES\\{filename}", configuration=config, options=options)
            # # Envío del mensaje. Debemos pasar el template.
            # emailSender = EmailMessage(
            #     subject,
            #     template,
            #     settings.EMAIL_HOST_USER,
            #     ["matiasfamilycrew@gmail.com"],
            # )
            # # print("Creacion del correo ")
            # # Formato del mensaje en HTML.
            # emailSender.content_subtype = "html"
            # emailSender.fail_silently = False
            # # Agregamos el PDF que hemos creado como adjunto al correo.
            # emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\Boleta_PDF_PACIENTES\\{filename}")
            # # Enviamos el correo.
            # emailSender.send()
            # --- Generar el PDF ---
            # 1. Definimos el nombre de la carpeta y la ruta dinámica
            nombre_carpeta = "Boleta_PDF_PACIENTES"
            # Usamos BASE_DIR para que funcione en cualquier sistema operativo
            ruta_base_pdf = os.path.join(settings.BASE_DIR, nombre_carpeta)

            if not os.path.exists(ruta_base_pdf):
                os.makedirs(ruta_base_pdf)
                print(f"Carpeta verificada/creada en: {ruta_base_pdf}")

            # 2. Preparamos el nombre del archivo
            now = datetime.now()
            # Reemplazamos espacios por guiones bajos para evitar errores en rutas de Linux
            nombre_limpio = nombre_completo.replace(" ", "_")
            filename = f"Boleta_Reserva_Cita_{nombre_limpio}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

            # 3. Ruta completa final del archivo (Universal)
            ruta_archivo_final = os.path.join(ruta_base_pdf, filename)

            # 4. Configuración de pdfkit (Detección automática de SO)
            # Esto evita que PythonAnywhere busque un archivo .exe que no existe
            if os.name == 'nt':  # Si estás en Windows (Local)
                path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            else:  # Si estás en Linux (PythonAnywhere)
                config = pdfkit.configuration()

            options = {
                'enable-local-file-access': None,
            }

            print(f"Generando PDF en: {ruta_archivo_final}")

            # 5. Creación del PDF
            # Eliminamos la ruta manual C:\\Users... para usar la variable dinámica
            pdfkit.from_string(template, ruta_archivo_final, configuration=config, options=options)

            # --- Envío del mensaje ---

            emailSender = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ["matiasfamilycrew@gmail.com"],
            )

            # Formato del mensaje en HTML.
            emailSender.content_subtype = "html"
            emailSender.fail_silently = False

            # 6. Agregamos el PDF adjunto usando la ruta dinámica
            emailSender.attach_file(ruta_archivo_final)

            # Enviamos el correo.
            emailSender.send()
            print("Correo enviado con éxito.")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)
#
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_pac_reserva(request, fk_usuario):
    try:
        res_uuid = request.data.get('res_uuid')
        print(res_uuid)
        print(fk_usuario)
        #
        user = CustomersUsers.objects.get(pk=fk_usuario)
        nombre_paciente = user.first_name + ' ' + user.last_name
        #
        datos = []
        # Serializar los datos
        reserva = ReservaModel.objects.filter(reserva_uuid=res_uuid)
        reserva.delete()
        res_pac = ReservaModel.objects.filter(fk_usuario=user.id)
        print(reserva)
        for res in res_pac:
            #
            datos.append({'id': fk_usuario, 'nombre_paciente': nombre_paciente,'fecha_reserva': res.fecha_reserva, 'especialidad': res.especialidad, 'nombre_doctor': res.nombre_doctor, 'tipo_pago': res.tipo_pago, 'cod_reserva': res.reserva_uuid, 'comuna_clinica': res.comuna_clinica, 'direccion_clinica': res.direccion_clinica, 'nombre_clinica': res.nombre_clinica, 'hora_inicio': res.hora_inicio, 'hora_termino': res.hora_termino})
        return Response({'reserva':datos},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_reserva(request):
    try:
        arr = []
        # Filtramos por los usuarios que no se encuentren en NULL, osea solo por los registrados.
        reserva = ReservaModel.objects.filter(fk_usuario__isnull=False)
        if len(reserva) != 0:
            for res in reserva:
                print("Entramos")
                print(res.fk_usuario.id)
                paciente = PacienteModel.objects.filter(fk_user=res.fk_usuario.id)
                print(paciente)
                for pac in paciente:
                    nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno

                    arr.append({'id_reserva': res.id,'fecha_reserva': res.fecha_reserva, 'especialidad': res.especialidad, 'nombre_doctor': res.nombre_doctor, 'tipo_pago': res.tipo_pago, 'reserva_uuid': res.reserva_uuid, 'comuna_clinica': res.comuna_clinica, 'direccion_clinica': res.direccion_clinica, 'nombre_clinica': res.nombre_clinica, 'hora_inicio':res.hora_inicio, 'hora_termino': res.hora_termino, 'fecha_creacion_reserva': res.fecha_creacion_reserva, 'nombre_paciente': nombre_paciente})
            return Response({'reserva':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
        else:
            return Response({'error':1},
                        # Específicamos el status.
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def listar_clinica_paciente_doctor(request):
    try:
        # Obtenemos todas las clínicas.
        clinicas = ComunaClinicaModel.objects.all()
        cl = []
        for cli in clinicas:
            print("Todas las clínicas")
            print(cli.id)
            print(cli.nombre_clinica)
            cl.append({
                'id': cli.id,
                'nombre_clinica': cli.nombre_clinica
            })
        return Response({'reserva':cl},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)
#
@api_view(['POST'])
@permission_classes([AllowAny])
def listar_paciente_doctor(request):
    try:
        usuario = CustomersUsers.objects.get(username=request.data["username"])
        doctor = DoctorModel.objects.get(fk_user=usuario.id)
        nombre_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"
        clinica = ComunaClinicaModel.objects.filter(pk=request.data["id_clinica"])
        arr = []
        for cli in clinica:
            reservas = ReservaModel.objects.filter(nombre_doctor=nombre_doctor, nombre_clinica=cli.nombre_clinica)
            for res in reservas:
                paciente = None
                nombre_paciente = ''
                edad = ''
                sexo = ''
                rut = ''
                # Paciente registrado
                if res.fk_usuario:
                    paciente = PacienteModel.objects.filter(fk_user=res.fk_usuario.id).first()
                # Paciente no registrado
                elif res.fk_pac_no_register:
                    paciente = PacienteNoRegisterModel.objects.filter(pk=res.fk_pac_no_register.id).first()
                if paciente:
                    nombre_paciente = f"{paciente.primer_nombre} {paciente.segundo_nombre} {paciente.ap_paterno} {paciente.ap_materno}"
                    edad = paciente.edad
                    sexo = paciente.sexo
                    rut = paciente.rut
                    arr.append({
                        'id_reserva': res.id,
                        'id_paciente': paciente.id,
                        'fecha_reserva': res.fecha_reserva,
                        'start': res.hora_inicio,
                        'end': res.hora_termino,
                        'title': res.especialidad,
                        'nombre_clinica': res.nombre_clinica,
                        'nombre_doctor': res.nombre_doctor,
                        'nombre_paciente': nombre_paciente,
                        'edad': edad,
                        'sexo': sexo,
                        'rut': rut,
                        'cod_reserva': res.reserva_uuid,
                        'reserva_cerrada': res.reserva_cerrada,
                        'pago_reserva': res.pago_realizado,
                    })
        return Response({'paciente': arr}, status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_paciente_doctor_cita(request):
    try:
        # Obtener al usuario que está haciendo la petición.
        usuario = CustomersUsers.objects.get(pk=request.user.id)
        doctor = DoctorModel.objects.get(fk_user=usuario.id)
        nombre_doctor = doctor.primer_nombre + ' ' + doctor.segundo_nombre + ' ' + doctor.ap_paterno + ' ' + doctor.ap_materno
        print(nombre_doctor)
        #
        arr = []
        res = ReservaModel.objects.filter(nombre_doctor=nombre_doctor)
        for us in res:
            # Obtenemos la FK del Paciente Registrado.
            if us.fk_usuario:
                user_pc = us.fk_usuario
                paciente = PacienteModel.objects.get(fk_user=user_pc.id)
                nombre_paciente = f"{paciente.primer_nombre} {paciente.segundo_nombre} {paciente.ap_paterno} {paciente.ap_materno}"
                arr.append({
                    'id_reserva': us.id,
                    'id_paciente': paciente.id,
                    'email': user_pc.email,
                    'fecha_reserva': us.fecha_reserva,
                    'hora_inicio': us.hora_inicio,
                    'hora_termino': us.hora_termino,
                    'especialidad': us.especialidad,
                    'nombre_clinica': us.nombre_clinica,
                    'comuna_clinica': us.comuna_clinica,
                    'direccion_clinica': us.direccion_clinica,
                    'nombre_doctor': us.nombre_doctor,
                    'nombre_paciente': nombre_paciente,
                    'edad': paciente.edad,
                    'sexo': paciente.sexo,
                    'rut': paciente.rut,
                    'fono': paciente.fono,
                    'reserva_uuid': us.reserva_uuid,
                    'reserva_cerrada': us.reserva_cerrada,
                    'tipo_paciente': 'registrado'
                })
        print(arr)
        return Response({'paciente':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_paciente_historial_doctor(request, id):
    try:
        print(id)
        arr = []
        usuario = CustomersUsers.objects.get(pk=id)
        #
        reserva = ReservaModel.objects.filter(fk_usuario=usuario.id)
        print(reserva)
        arr = []
        for res in reserva:
            print("Entramos")
            arr.append({'id_reserva': res.id,'especialidad': res.especialidad, 'nombre_doctor':res.nombre_doctor,'nombre_clinica': res.nombre_clinica, 'comuna_clinica':res.comuna_clinica, 'direccion_clinica':res.direccion_clinica,'fecha_reserva': res.fecha_reserva,'hora_inicio':res.hora_inicio, 'hora_termino':res.hora_termino, 'fecha_creacion_reserva':res.fecha_creacion_reserva, 'cod_reserva': res.reserva_uuid,'id_usuario': usuario.id})
        return Response({'reserva':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_cli_pac_panel_secretaria(request, id):
    try:
        print(id)
        arr = []
        usuario = CustomersUsers.objects.get(pk=id)
        #
        reserva = ReservaModel.objects.filter(fk_usuario=usuario.id)
        print(reserva)
        arr = []
        for res in reserva:
            print("Entramos")
            arr.append({'id_reserva': res.id, 'especialidad': res.especialidad, 'nombre_doctor':res.nombre_doctor,'nombre_clinica': res.nombre_clinica, 'comuna_clinica':res.comuna_clinica, 'direccion_clinica':res.direccion_clinica,'fecha_reserva': res.fecha_reserva,'hora_inicio':res.hora_inicio, 'hora_termino':res.hora_termino, 'fecha_creacion_reserva':res.fecha_creacion_reserva, 'tipo_pago': res.tipo_pago,'reserva_cerrada': res.reserva_cerrada,'cod_reserva': res.reserva_uuid,'id_usuario': usuario.id})
        return Response({'reserva':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_reserva_panel_secretaria(request, id_reserva):
    try:
        print(id_reserva)
        #
        id_usuario = None
        #
        reserva = ReservaModel.objects.get(pk=id_reserva)
        arr = []
        id_usuario = reserva.fk_usuario.id
        reserva.delete()
        print("Prueba 1")
        print(id_usuario)
        print("Prueba 1")
        reserva_usuarios = ReservaModel.objects.filter(fk_usuario=id_usuario)
        print(reserva_usuarios)
        for res in reserva_usuarios:
            arr.append({'id_reserva': res.id,'especialidad': res.especialidad, 'nombre_doctor':res.nombre_doctor,'nombre_clinica': res.nombre_clinica, 'comuna_clinica':res.comuna_clinica, 'direccion_clinica':res.direccion_clinica,'fecha_reserva': res.fecha_reserva,'hora_inicio':res.hora_inicio, 'hora_termino':res.hora_termino, 'fecha_creacion_reserva':res.fecha_creacion_reserva, 'cod_reserva': res.reserva_uuid, 'pago_realizado': res.pago_realizado,'id_usuario': id_usuario})
        print("Array")
        print(arr)
        print("Array")
        return Response({'reserva':arr},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_reserva_pac(request, id_usuario):
    try:
        print(id_usuario)
        reserva = ReservaModel.objects.filter(fk_usuario=id_usuario)
        arr = []
        for res in reserva:
            arr.append({
                'id_reserva': res.id,
                'id_usuario': id_usuario,
                'fecha_creacion_reserva': res.fecha_creacion_reserva,
                'fecha_reserva': res.fecha_reserva,
                'hora_inicio': res.hora_inicio,
                'hora_termino': res.hora_termino,
                'especialidad': res.especialidad,
                'nombre_doctor': res.nombre_doctor,
                'reserva_uuid': res.reserva_uuid,
                'nombre_clinica': res.nombre_clinica,
                'comuna_clinica': res.comuna_clinica,
                'direccion_clinica': res.direccion_clinica,
                'reserva_cerrada': res.reserva_cerrada,
            })
        return Response({'reserva':arr},
                    # Específicamos el status.
                    status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

#
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnostico_historial_pac(request, id_usuario, cod_reserva):
    try:
        #
        paciente = PacienteModel.objects.filter(fk_user=id_usuario)
        #
        arr = []
        print(cod_reserva)
        #
        cod_reserva = str(cod_reserva)
        for pac in paciente:
            print(pac.id)
            try:
                diagnostico = HistorialClinicoModel.objects.get(fk_paciente=pac.id, reserva_uuid=cod_reserva)
                print(diagnostico)
                print("-****----///")
                arr.append({
                    'id_historial': diagnostico.id,
                    'diagnostico': diagnostico.diagnostico,
                    'sintoma': diagnostico.sintoma,
                    'observacion': diagnostico.observacion,
                    'fecha_creacion_historial': diagnostico.fecha_creacion_historial
                })
                return Response({'diagnostico':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
            except:
                print("No se encontró ningún diagnóstico con esos parámetros.")
                diagnostico = None
                return Response({'diagnostico':0},
                        # Específicamos el status.
                        status=status.HTTP_404_NOT_FOUND)


    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cod_reserva_verificacion(request):
    try:
        print(request.data)
        veri_cod = request.data["reserva_uuid"]
        usuario = request.user.id
        fk_paciente = ReservaModel.objects.filter(reserva_uuid=veri_cod, fk_usuario=usuario)
        if not fk_paciente.exists():
            return Response({'error': 2}, status=status.HTTP_404_NOT_FOUND)
        cod_reserva = ReservaModel.objects.filter(reserva_uuid=veri_cod, pago_realizado=0)
        arr = []
        #
        if cod_reserva.exists():
            for cod in cod_reserva:
                paciente = PacienteModel.objects.filter(fk_user=cod.fk_usuario)
                valor_especialidad = Especialidad.objects.get(nombre_especialidad=cod.especialidad)
                for pac in paciente:
                    nombre_paciente = pac.primer_nombre + ' ' + pac.segundo_nombre + ' ' + pac.ap_paterno + ' ' + pac.ap_materno
                    fk_user = pac.fk_user.id
                    arr.append({
                        'nombre_doctor': cod.nombre_doctor,
                        'cod_reserva': cod.reserva_uuid,
                        'fecha_reserva': cod.fecha_reserva,
                        'fecha_creacion_reserva': cod.fecha_creacion_reserva,
                        'hora_inicio': cod.hora_inicio,
                        'hora_termino': cod.hora_termino,
                        'nombre_clinica': cod.nombre_clinica,
                        'comuna_clinica': cod.comuna_clinica,
                        'direccion_clinica': cod.direccion_clinica,
                        'especialidad': cod.especialidad,
                        'reserva_cerrada': cod.reserva_cerrada,
                        'pago_realizado': cod.pago_realizado,
                        'nombre_paciente': nombre_paciente,
                        'rut_paciente': pac.rut,
                        'valor_especialidad': valor_especialidad.valor_especialidad,
                        'pago_realizado': cod.pago_realizado,
                        'fk_user': fk_user,
                    })
            return Response({'datos':arr},
                        # Específicamos el status.
                        status=status.HTTP_200_OK)
        else:
            return Response({'error': 1}, status=status.HTTP_404_NOT_FOUND)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 0}, status=400)

#
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_pago_debito_reserva(request, reserva_uuid):
    try:
        data = request.data
        veri_cod = request.data["reserva_uuid"]
        debito = request.data["debito"]
        cod_desc = None
        try:
            cod_desc = request.data["codigo"]
            print(cod_desc)
        except:
            pass
        #
        debito_uuid = str(uuid.uuid4())
        dato_reserva = ReservaModel.objects.filter(reserva_uuid=reserva_uuid)
        valor_especialidad = ""
        for dato in dato_reserva:
            valor_especialidad = Especialidad.objects.get(nombre_especialidad=dato.especialidad)
        #
        id_descuento = "";
        valor_desc_aplicado = "";
        id_paciente = "";
        nombre_paciente = "";
        aplicar_desc_bd = 0;
        update_res_data = "";
        aplicar_desc = "";
        #
        if dato_reserva.exists():
            #
            cod_ver = DescuentoModel.objects.filter(cod_descuento=cod_desc)
            if cod_ver.exists():
                for dato in dato_reserva:
                    paciente = PacienteModel.objects.get(fk_user=dato.fk_usuario)
                    id_paciente = paciente.id
                # Obtenemos la fecha Actual.
                fecha_actual = date.today()
                for cod in cod_ver:
                    id_descuento = cod.id
                    asignado = DescuentoPaciente.objects.filter(fk_descuento=cod.id, fk_paciente=cod.id)
                    if asignado.exists():
                        return Response({'error': 3}, status=400)
                    #
                    if fecha_actual > cod.fecha_termino:
                        return Response({'error': 4}, status=400)
                    # Verificar Fecha de caducación Descuentos.
                    if fecha_actual <= cod.fecha_termino:
                        aplicar_desc_bd = 1
                        porcentaje = cod.descuento / 100
                        valor_desc_aplicado = int(valor_especialidad.valor_especialidad * porcentaje)
                        aplicar_desc = int(valor_especialidad.valor_especialidad - valor_desc_aplicado)
                    #
                    if aplicar_desc_bd == 1:
                        print("Aplica Descuento")
                        # Actualizamos el pago de la reserva.
                        update_res_data = {
                            'tipo_pago': '0',
                            'pago_realizado': 1,
                        }
                        #
                        instancia_reserva = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                        update_res = ReservaSerializer(instancia_reserva, data=update_res_data, partial=True)
                        #
                        if update_res.is_valid():
                            id_reserva = update_res.save()
                            data_debito= {
                                'debito': debito,
                                'monto': valor_especialidad.valor_especialidad,
                                'monto_total': aplicar_desc,
                                'debito_uuid': debito_uuid,
                                'fk_reserva': id_reserva.id,
                            }
                            insert_debito = DebitoSerializer(data=data_debito)
                            if insert_debito.is_valid():
                                insert_debito.save()
                                # Insertamos en la tabla intermedia el fk del pac y el fk del descuento.
                                data_pac_desc = {
                                    'total_pagar': valor_especialidad.valor_especialidad,
                                    'total_pagar_descuento': aplicar_desc,
                                    'fk_descuento': id_descuento,
                                    'fk_paciente': id_paciente,
                                }
                                #
                                insertar_desc = DescuentoPacienteSerializer(data=data_pac_desc)
                                if insertar_desc.is_valid():
                                    insertar_desc.save()
                                    correo_res_pagada(reserva_uuid, cod.id)
                                    return Response({'success':1},
                                            # Específicamos el status.
                                            status=status.HTTP_200_OK)
            if aplicar_desc_bd == 0:
                #
                dato_reserva_sin_descuento = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                # Actualizamos el pago de la reserva.
                update_res_data = {
                    'tipo_pago': 0,
                    'pago_realizado': 1,
                }
                #
                update_res = ReservaSerializer(dato_reserva_sin_descuento, data=update_res_data, partial=True)
                #
                if update_res.is_valid():
                    id_reserva = update_res.save()
                    data_debito= {
                        'debito': debito,
                        'monto': valor_especialidad.valor_especialidad,
                        'monto_total': valor_especialidad.valor_especialidad,
                        'debito_uuid': debito_uuid,
                        'fk_reserva': id_reserva.id,
                    }
                    #
                    # Verificamos si el pago ya fue realizado.
                    pago_realizado = DebitoModel.objects.filter(fk_reserva=id_reserva.id)
                    if pago_realizado.exists():
                        return Response({'error': 5}, status=400)
                    insert_debito = DebitoSerializer(data=data_debito)
                    dato_reserva_debito = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                    if insert_debito.is_valid():
                        insert_debito.save()
                        # Dato para crear el email.
                        correo_res_pagada(reserva_uuid, 0)
                        return Response({'success':1},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
                    else:
                        print("Errores Debito:", insert_debito.errors)
                        return Response(insert_debito.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("Error....")
            return Response({'error': 2}, status=400)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 0}, status=400)
#
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_pago_credito_reserva(request, reserva_uuid):
    try:
        data = request.data
        veri_cod = request.data["reserva_uuid"]
        credito = request.data["credito"]
        cod_desc = None
        try:
            cod_desc = request.data["codigo"]
            print(cod_desc)
        except:
            pass
        cuotas = request.data["cant_cuotas"]
        cant_cuota = int(cuotas)
        #
        credito_uuid = str(uuid.uuid4())
        dato_reserva = ReservaModel.objects.filter(reserva_uuid=reserva_uuid)
        valor_especialidad = None
        for dato in dato_reserva:
            valor_especialidad = Especialidad.objects.get(nombre_especialidad=dato.especialidad)
        #
        id_descuento = None;
        valor_desc_aplicado = None;
        id_paciente = None;
        nombre_paciente = None;
        aplicar_desc_bd = 0;
        update_res_data = None;
        aplicar_desc = None;
        #
        if dato_reserva.exists():
            #
            cod_ver = DescuentoModel.objects.filter(cod_descuento=cod_desc)
            if cod_ver.exists():
                for dato in dato_reserva:
                    paciente = PacienteModel.objects.get(fk_user=dato.fk_usuario)
                    id_paciente = paciente.id
                # Obtenemos la fecha Actual.
                fecha_actual = date.today()
                for cod in cod_ver:
                    id_descuento = cod.id
                    asignado = DescuentoPaciente.objects.filter(fk_descuento=cod.id, fk_paciente=cod.id)
                    if asignado.exists():
                        return Response({'error': 3}, status=400)
                    #
                    if fecha_actual > cod.fecha_termino:
                        return Response({'error': 4}, status=400)
                    # Verificar Fecha de caducación Descuentos.
                    if fecha_actual <= cod.fecha_termino:
                        aplicar_desc_bd = 1
                        porcentaje = cod.descuento / 100
                        valor_desc_aplicado = int(valor_especialidad.valor_especialidad * porcentaje)
                        aplicar_desc = int(valor_especialidad.valor_especialidad - valor_desc_aplicado)
                    #
                    if aplicar_desc_bd == 1:
                        print("Aplica Descuento")
                        # Actualizamos el pago de la reserva.
                        update_res_data = {
                            'tipo_pago': '1',
                            'pago_realizado': 1,
                        }
                        reserva_instance = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                        #
                        update_res = ReservaSerializer(reserva_instance, data=update_res_data, partial=True)
                        #
                        if update_res.is_valid():
                            id_reserva = update_res.save()
                            monto_cuotas = aplicar_desc / cant_cuota
                            data_credito= {
                                'credito': credito,
                                'monto': valor_especialidad.valor_especialidad,
                                'monto_total': aplicar_desc,
                                'monto_cuotas': int(monto_cuotas),
                                'credito_uuid': credito_uuid,
                                'cant_cuotas': cant_cuota,
                                'fk_reserva': id_reserva.id,
                            }
                            insert_credito = CreditoSerializer(data=data_credito)
                            print("Pasamos...")
                            if insert_credito.is_valid():
                                insert_credito.save()
                                print("Pasamos el UPDATE Reserva")
                                # Insertamos en la tabla intermedia el fk del pac y el fk del descuento.
                                data_pac_desc = {
                                    'total_pagar': valor_especialidad.valor_especialidad,
                                    'total_pagar_descuento': aplicar_desc,
                                    'fk_descuento': id_descuento,
                                    'fk_paciente': id_paciente,
                                }
                                #
                                insertar_desc = DescuentoPacienteSerializer(data=data_pac_desc)
                                if insertar_desc.is_valid():
                                    insertar_desc.save()
                                    correo_res_pagada(reserva_uuid, id_descuento)
                                    return Response({'success':1},
                                            # Específicamos el status.
                                          status=status.HTTP_200_OK)
                            else:
                                # Aquí capturamos los errores del serializer.
                                errores = insert_credito.errors
                                print("Errores de validación:", errores)
            if aplicar_desc_bd == 0:
                #
                dato_reserva_sin_descuento = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                # Actualizamos el pago de la reserva.
                update_res_data = {
                    'tipo_pago': 1,
                    'pago_realizado': 1,
                }
                #
                update_res = ReservaSerializer(dato_reserva_sin_descuento, data=update_res_data, partial=True)
                #
                valor_esp = int(valor_especialidad.valor_especialidad)
                monto_cuota = valor_esp / cant_cuota
                monto_cuota = int(monto_cuota)
                if update_res.is_valid():
                    id_reserva = update_res.save()
                    data_credito= {
                        'credito': credito,
                        'monto_total': valor_especialidad.valor_especialidad,
                        'monto_cuotas': monto_cuota,
                        'credito_uuid': credito_uuid,
                        'cant_cuotas': cant_cuota,
                        'fk_reserva': id_reserva.id,
                        'monto': valor_especialidad.valor_especialidad,
                    }
                    # Verificamos si el pago ya fue realizado.
                    pago_realizado = CreditoModel.objects.filter(fk_reserva=id_reserva.id)
                    if pago_realizado.exists():
                        return Response({'error': 5}, status=400)
                    insert_credito = CreditoSerializer(data=data_credito)
                    dato_reserva_debito = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                    if insert_credito.is_valid():
                        insert_credito.save()
                        # Dato para crear el email.
                        correo_res_pagada(reserva_uuid, 0)
                        return Response({'success':1},
                                # Específicamos el status.
                                status=status.HTTP_200_OK)
                    else:
                        print("Errores Crédito:", insert_credito.errors)
                        return Response(insert_credito.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("Error....")
            return Response({'error': 2}, status=400)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 0}, status=400)

# Reserva creada por la SECRETARIA y pagada desde el panel PACIENTE.
def correo_res_pagada(reserva_uuid, fk_descuento):
    try:
        print("RESERVA_UUID")
        print("fk_descuento")
        print(fk_descuento)
        reserva = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
        metodo_pago = reserva.tipo_pago
        usuario = reserva.fk_usuario
        usuario = CustomersUsers.objects.get(username=usuario)
        print(usuario.email)
        paciente = PacienteModel.objects.get(fk_user=usuario.id)
        print(paciente.fk_user.id)

        id_usuario = paciente.fk_user.id
        # Datos del usuario.
        nombre_completo = paciente.primer_nombre + " " + paciente.segundo_nombre + " " + paciente.ap_paterno + " " + paciente.ap_materno
        rut = paciente.rut
        fono = paciente.fono
        email = usuario.email
        fecha_reserva = reserva.fecha_reserva
        especialidad = reserva.especialidad
        valor_esp = Especialidad.objects.get(nombre_especialidad=reserva.especialidad)
        valor_base = valor_esp.valor_especialidad
        nombre_doctor = reserva.nombre_doctor
        reserva_uuid = reserva.reserva_uuid
        nombre_clinica = reserva.nombre_clinica
        comuna_clinica = reserva.comuna_clinica
        direccion_clinica = reserva.direccion_clinica
        nombre_doctor = reserva.nombre_doctor
        hora_inicio = reserva.hora_inicio
        hora_termino = reserva.hora_termino
        fecha_creacion_reserva = reserva.fecha_creacion_reserva
        tipo_pago = reserva.tipo_pago
        aplica_descuento = None
        debito = ""
        credito = ""
        if tipo_pago == "0":
            debito = "Débito"
        if tipo_pago == "1":
            credito = "Crédito"
        # Si existe descuento, guardamos los datos en estas variables.
        total_pagar = None;
        total_pagar_descuento = None;
        fecha_utilizacion = None;
        print(metodo_pago)
        descuento = None;
        #
        if metodo_pago == "0":
            if fk_descuento == 0:
                debito = DebitoModel.objects.get(fk_reserva=reserva.id)
                total_pagar = "No Existen Datos"
                total_pagar_descuento = "No Existen Datos"
                fecha_utilizacion = "No Existen Datos"
                aplica_descuento = "No"
                # Creación del correo.
                subject = "Correo Verificación Reserva"
                # Crearemos el envío de correos.
                template = render_to_string("pacientes/correo_reserva.html",{
                    'nombre_paciente': nombre_completo,
                    'rut_paciente': rut,
                    'email_paciente': email,
                    'fono_paciente': fono,
                    'fecha_reserva': fecha_reserva,
                    'especialidad': especialidad,
                    'nombre_doctor': nombre_doctor,
                    'reserva_uuid': reserva_uuid,
                    'comuna_clinica': comuna_clinica,
                    'direccion_clinica': direccion_clinica,
                    'nombre_clinica': nombre_clinica,
                    'hora_inicio': hora_inicio,
                    'hora_termino': hora_termino,
                    'fecha_creacion_reserva': fecha_creacion_reserva,
                    'total_pagar': valor_base,
                    'tipo_pago': "Débito",
                    'monto': debito.monto,
                    'aplica_descuento': "No",
                    'valor_especialidad': valor_base,
                    'monto_total': debito.monto_total,
                    'total_pagar_descuento': "No aplica",
                    'fecha_utilizacion': "No aplica",
                    'descuento': "No aplica",
                    'reserva_pagada': 'Sí',
                    'valor_base': valor_base,
                })
                # # Generar el PDF
                # nombre_carpeta = "Boleta_PDF_PACIENTES"
                # ruta = f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}"
                # if not os.path.exists(ruta):
                #     os.makedirs(ruta)
                #     print(f"Carpeta creada en: {ruta}")
                # else:
                #     pass
                # now = datetime.now()
                # filename = f"Boleta_Reserva_Cita_{nombre_completo}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # # Creación del PDF.
                # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
                # # Configuración de pdfkit
                # options = {
                #     'enable-local-file-access': None,
                #     # 'orientation': 'Landscape',
                #     # 'page-size': 'A4',
                #     # 'margin-top': '0.2in',
                #     # 'margin-bottom': '0.2in',
                #     # 'encoding': "UTF-8",
                # }
                # print("Adjunto..........")
                # # template; Pertenece
                # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}\\{filename}", configuration=config, options=options)
                # # Envío del mensaje. Debemos pasar el template.
                # emailSender = EmailMessage(
                #     subject,
                #     template,
                #     settings.EMAIL_HOST_USER,
                #     ["matiasfamilycrew@gmail.com"],
                # )
                # # print("Creacion del correo ")
                # # Formato del mensaje en HTML.
                # emailSender.content_subtype = "html"
                # emailSender.fail_silently = False
                # # Agregamos el PDF que hemos creado como adjunto al correo.
                # emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\{nombre_carpeta}\\{filename}")
                # # Enviamos el correo.
                # emailSender.send()
                # --- Generar el PDF ---
                nombre_carpeta = "Boleta_PDF_PACIENTES"

                # Usamos BASE_DIR para que la ruta se adapte automáticamente al servidor
                ruta_base = os.path.join(settings.BASE_DIR, nombre_carpeta)

                if not os.path.exists(ruta_base):
                    os.makedirs(ruta_base)
                    print(f"Carpeta verificada/creada en: {ruta_base}")

                now = datetime.now()
                # Limpiamos el nombre para evitar problemas con espacios en sistemas Linux
                nombre_archivo_limpio = nombre_completo.replace(" ", "_")
                filename = f"Boleta_Reserva_Cita_{nombre_archivo_limpio}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

                # Definimos la ruta completa del archivo de forma dinámica
                ruta_pdf_final = os.path.join(ruta_base, filename)

                # --- Configuración de pdfkit ---
                # Detectamos el sistema para no buscar un .exe en Linux
                if os.name == 'nt':  # Windows
                    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                else:  # Linux (PythonAnywhere)
                    # En Linux, pdfkit busca el binario directamente en el sistema
                    config = pdfkit.configuration()

                options = {
                    'enable-local-file-access': None,
                }

                print("Adjuntando y generando PDF...")

                # Generar el PDF usando la ruta dinámica (sin C:\\Users...)
                pdfkit.from_string(template, ruta_pdf_final, configuration=config, options=options)

                # --- Envío del mensaje ---
                emailSender = EmailMessage(
                    subject,
                    template,
                    settings.EMAIL_HOST_USER,
                    ["matiasfamilycrew@gmail.com"],
                )

                emailSender.content_subtype = "html"
                emailSender.fail_silently = False

                # Agregamos el PDF adjunto usando la ruta dinámica universal
                emailSender.attach_file(ruta_pdf_final)

                # Enviamos el correo
                emailSender.send()
            if fk_descuento != 0:
                print("Ingresamos Correctamente")
                reserva = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
                debito_uuid = DebitoModel.objects.get(fk_reserva= reserva.id)
                desc_pac = DescuentoPaciente.objects.filter(fk_paciente=paciente.id, fk_descuento=fk_descuento)
                desc = DescuentoModel.objects.get(pk=fk_descuento)
                # Realizamos la operacion de descuento para mostrar en el Correo.
                pagar = valor_base * desc.descuento / 100
                total_pagar_descuento = valor_base - pagar
                print("Datos de Descuento Alicado")
                print(desc.descuento)
                print(debito_uuid.monto_total)
                print(total_pagar_descuento)
                print(desc.descuento)
                print("Datos de Descuento Alicado")
                for des_paciente in desc_pac:
                    total_pagar = des_paciente.total_pagar
                    total_pagar_descuento = des_paciente.total_pagar_descuento
                    fecha_utilizacion = des_paciente.fecha_utilizacion
                    aplica_descuento = "Sí"
                    # Creación del correo.
                    subject = "Correo Verificación Reserva"
                    # Crearemos el envío de correos.
                    template = render_to_string("pacientes/correo_reserva.html",{
                        'nombre_paciente': nombre_completo,
                        'rut_paciente': rut,
                        'email_paciente': email,
                        'fono_paciente': fono,
                        'fecha_reserva': fecha_reserva,
                        'especialidad': especialidad,
                        'nombre_doctor': nombre_doctor,
                        'reserva_uuid': reserva_uuid,
                        'comuna_clinica': comuna_clinica,
                        'direccion_clinica': direccion_clinica,
                        'nombre_clinica': nombre_clinica,
                        'hora_inicio': hora_inicio,
                        'hora_termino': hora_termino,
                        'fecha_creacion_reserva': fecha_creacion_reserva,
                        'total_pagar': total_pagar,
                        'tipo_pago': "Débito",
                        'monto': debito_uuid.monto,
                        'aplica_descuento': aplica_descuento,
                        'valor_descuento': desc.descuento,
                        'monto_total': debito_uuid.monto_total,
                        'total_pagar': total_pagar_descuento,
                        'fecha_utilizacion': fecha_utilizacion,
                        'descuento': desc.descuento,
                        'reserva_pagada': 'Sí',
                        'valor_base': valor_base,
                        'valor_especialidad': valor_base,
                    })
                    # Envío del mensaje. Debemos pasar el template.
                    emailSender = EmailMessage(
                        subject,
                        template,
                        settings.EMAIL_HOST_USER,
                        ["matiasfamilycrew@gmail.com"],
                    )
                #
                emailSender.content_subtype = "html"
                emailSender.fail_silently = False
                # Método para la creación del PDF.
                pdf_res_pagada_pac(template, nombre_completo, emailSender)
                # Enviamos el correo.
                emailSender.send()
        #
        if metodo_pago == "1":
            print("Ingresamos al Crédito")
            metodo_credito = CreditoModel.objects.get(fk_reserva=reserva.id)
            if fk_descuento != 0:
                descuento = DescuentoModel.objects.get(pk=fk_descuento)
                descuento_aplicado = DescuentoPaciente.objects.filter(fk_paciente=paciente.id, fk_descuento=fk_descuento)
                #
                if descuento_aplicado.exists():
                    for desc_apli in descuento_aplicado:
                        descuento_apl = descuento.descuento
                        total_pagar = desc_apli.total_pagar
                        total_pagar_descuento = desc_apli.total_pagar_descuento
                        fecha_utilizacion = desc_apli.fecha_utilizacion
                #
                if not descuento_aplicado.exists():
                    total_pagar = "No hay Datos";
                    total_pagar_descuento = "No hay Datos";
                    fecha_utilizacion = "No hay Datos";
                # Creación del correo.
                subject = "Correo Verificación Reserva"
                # Crearemos el envío de correos.
                template = render_to_string("pacientes/correo_reserva.html",{
                    'nombre_paciente': nombre_completo,
                    'rut_paciente': rut,
                    'email_paciente': email,
                    'fono_paciente': fono,
                    'fecha_reserva': fecha_reserva,
                    'especialidad': especialidad,
                    'nombre_doctor': nombre_doctor,
                    'reserva_uuid': reserva_uuid,
                    'comuna_clinica': comuna_clinica,
                    'direccion_clinica': direccion_clinica,
                    'nombre_clinica': nombre_clinica,
                    'hora_inicio': hora_inicio,
                    'hora_termino': hora_termino,
                    'fecha_creacion_reserva': fecha_creacion_reserva,
                    'tipo_pago': 'Crédito',
                    'credito_uuid': metodo_credito.credito_uuid,
                    'total_pagar': total_pagar_descuento,
                    'valor_especialidad': valor_base,
                    'valor_base': valor_base,
                    'descuento': descuento.descuento,
                    'fecha_utilizacion': fecha_utilizacion,
                    'fecha_pago': metodo_credito.fecha_pago,
                    'cant_cuotas': metodo_credito.cant_cuotas,
                    'monto_total': metodo_credito.monto_total,
                    'monto_cuotas': metodo_credito.monto_cuotas,
                    'monto': metodo_credito.monto,
                    'reserva_pagada': 'Sí',
                })
            else:
                # Creación del correo.
                subject = "Correo Verificación Reserva"
                # Crearemos el envío de correos.
                template = render_to_string("pacientes/correo_reserva.html",{
                    'nombre_paciente': nombre_completo,
                    'rut_paciente': rut,
                    'email_paciente': email,
                    'fono_paciente': fono,
                    'fecha_reserva': fecha_reserva,
                    'especialidad': especialidad,
                    'nombre_doctor': nombre_doctor,
                    'reserva_uuid': reserva_uuid,
                    'comuna_clinica': comuna_clinica,
                    'direccion_clinica': direccion_clinica,
                    'nombre_clinica': nombre_clinica,
                    'hora_inicio': hora_inicio,
                    'hora_termino': hora_termino,
                    'fecha_creacion_reserva': fecha_creacion_reserva,
                    'tipo_pago': 'Crédito',
                    'credito_uuid': metodo_credito.credito_uuid,
                    'total_pagar': valor_base,
                    'valor_especialidad': valor_base,
                    'valor_base': valor_base,
                    'descuento': "No aplica",
                    'fecha_utilizacion': "No aplica",
                    'fecha_pago': metodo_credito.fecha_pago,
                    'cant_cuotas': metodo_credito.cant_cuotas,
                    'monto_total': metodo_credito.monto_total,
                    'monto_cuotas': metodo_credito.monto_cuotas,
                    'monto': metodo_credito.monto,
                    'reserva_pagada': 'Sí',
                })
            # Envío del mensaje. Debemos pasar el template.
            emailSender = EmailMessage(
                subject,
                template,
                settings.EMAIL_HOST_USER,
                ["matiasfamilycrew@gmail.com"],
            )
            emailSender.content_subtype = "html"
            emailSender.fail_silently = False
            #
            pdf_res_pagada_pac(template, nombre_completo, emailSender)
            # Enviamos el correo.
            emailSender.send()
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 0}, status=400)

# Creación PDF pago resrva creada por la SECRETARIA y pagada desde el panel PACIENTE.
def pdf_res_pagada_pac(template, nombre_paciente, emailSender):
    try:
        # print("Creación PDF.")
        # print("Creación PDF Paciente Panel Paciente")
        # print("Ingresamos al PDF.")
        # print(nombre_paciente)
        # # Ruta base de la carpeta donde se almacenan los PDF.
        # carpeta_destino = "C:\\Users\\Plask91\\Documents\\Clinica\\clinica\\Clinica_DRF\\BOLETA_PDF_PACIENTES"
        # # Verificar si la carpeta existe, si no, la debemos crear.
        # if not os.path.exists(carpeta_destino):
        #     os.makedirs(carpeta_destino)
        #     print(f"Carpeta creada: {carpeta_destino}")
        # # Generación del nombre de archivo único
        # now = datetime.now()
        # filename = f"Boleta_Compra_{nombre_paciente}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        # # Creación del PDF.
        # # Configuración de pdfkit
        # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        # options = {'enable-local-file-access': None}
        # # Generar el PDF
        # # template; Pertenece
        # pdf = pdfkit.from_string(template, f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}", configuration=config, options=options)
        # #Envío del mensaje. Debemos pasar el template.
        # emailSender.attach_file(f"C:\\Users\\Plask91\\Documents\\Clinica\\clinica\Clinica_DRF\\BOLETA_PDF_PACIENTES\\{filename}")
        # --- Lógica de Generación de PDF ---
        print("Creación PDF Paciente Panel Paciente")
        print(f"Ingresamos al PDF para: {nombre_paciente}")

        # 1. Definimos la carpeta de destino usando BASE_DIR para que funcione en Linux y Windows
        carpeta_destino = os.path.join(settings.BASE_DIR, 'BOLETA_PDF_PACIENTES')

        # Verificar si la carpeta existe, si no, la creamos
        if not os.path.exists(carpeta_destino):
            os.makedirs(carpeta_destino)
            print(f"Carpeta creada en: {carpeta_destino}")

        # 2. Generación del nombre de archivo único (limpiando espacios para Linux)
        now = datetime.now()
        nombre_archivo_paciente = nombre_paciente.replace(" ", "_")
        filename = f"Boleta_Compra_{nombre_archivo_paciente}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.pdf"

        # 3. Ruta completa final del PDF
        ruta_final_pdf = os.path.join(carpeta_destino, filename)

        # 4. Configuración de pdfkit (Detección de Sistema Operativo)
        # Esto evita errores al buscar el .exe en servidores Linux
        if os.name == 'nt':  # Si es Windows
            path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else:  # Si es Linux (PythonAnywhere)
            config = pdfkit.configuration()

        options = {'enable-local-file-access': None}

        # 5. Generar el PDF usando la ruta dinámica universal
        # Eliminamos las rutas fijas C:\\Users...
        pdfkit.from_string(template, ruta_final_pdf, configuration=config, options=options)

        # 6. Envío del mensaje adjuntando el archivo
        # Usamos la misma variable dinámica para asegurar que encuentre el archivo
        emailSender.attach_file(ruta_final_pdf)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 0}, status=400)


# Este método es solo de prueba de consumo de microservicio por parte de un proyecto aparte el cual le realiza la petición.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_reservas(request):
    try:
        print("Recibiendo peticion de MICROSERVICIOSDRF")
        # Obtener la fecha actual.
        fecha_today = date.today()
        # Realizamos el filtro para obtener las reservas del día actual.
        all_reservas = ReservaModel.objects.filter(fecha_reserva=fecha_today)
        serializer = ReservaSerializer(all_reservas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def confirmar_correo_reservas(request, reserva_uuid):
    try:
        print("Obteniendo la Reserva_uuid de correo para actualizar la BD de confirmación.")
        print(f"Reserva_uuid: {reserva_uuid}")
        token = request.GET.get('token')
        signer = TimestampSigner()
        try:
            unsigned_value = signer.unsign(token, max_age=60*60*24)  # El token es válido por 24 horas
            print(f"Token válido. Valor sin firmar: {unsigned_value}")
            # Aquí puedes actualizar la base de datos para marcar la reserva como confirmada
            reserva = ReservaModel.objects.get(reserva_uuid=reserva_uuid)
            reserva.reser_confirmada = 1
            reserva.save()
            # USAMOS RENDER DIRECTO PARA EVITAR ERRORES DE REDIRECCIÓN.
            return render(request, 'pacientes/web_confirmacion.html')
        except SignatureExpired:
            print("El token ha expirado.")
            return Response({'error': 'El enlace ha expirado.'}, status=400)
        except BadSignature:
            print("El token no es válido.")
            return Response({'error': 'Enlace no válido.'}, status=400)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 1}, status=400)