# RECORDAR QUE ACÁ SOLO VÁ LA CONFIGURACION DEL TASK, OSEA LA HORA A LA CUAL
# YO QUIERO QUE EJECUTE MI ARCHIVO QUE SE ENCUENTRA EN VIEWS.PY DE LA CARPETA
# APP RESERVA LA CUAL CONTIENE EL CÓDIGO PARA OBTENER LAS RESERVAS.
# BaseCommand: Es la clase "padre" de la que debe heredar tu comando para que Django lo reconozca como una herramienta de gestión.
from django.core.management.base import BaseCommand
from django.conf import settings
# Importamos environ para leer el archivo .env
import environ
import os
import requests
# Obtenemos la Fecha de Hoy.
from datetime import date, datetime, timedelta
import pytz
from django.utils import timezone
from reserva.models import ReservaModel
from reserva.serializers import ReservaSerializer
# Adjuntar imagen al correo.
from email.mime.image import MIMEImage
# render_to_string; Sirve para enviar el HTML del correo.-------------------
from django.template.loader import render_to_string
# Mensaje del E-mail.
from django.core.mail import EmailMessage, EmailMultiAlternatives,send_mail
# Este es laimportación del metodo de encriptacion de la reserva_uuid que se envía por URL.
from reserva.utils import generar_link_confirmacion
from paciente.models import PacienteModel
from paciente.serializers import PacienteSerializer
from paciente_no_registrado.models import PacienteNoRegisterModel
from paciente_no_registrado.serializers import PacienteNoRegisterSerializer


# Buena práctica, se debe inicializar afuera de la clase.
# Inicializamos environ
env = environ.Env()

# Calculamos la ruta a la raíz del proyecto (3 niveles arriba de este archivo)
# management/commands/obtener_reservas.py -> commands -> management -> Reservas -> RAIZ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

class Command(BaseCommand):
    help = 'Pide las reservas a la API de la Clínica a las 06:00 AM'

    def handle(self, *args, **options):
        try:
            print("Recibiendo peticion de MICROSERVICIOS")
            # Obtener la fecha actual.
            fecha_today = date.today()
            # Obtener la hora actual de Chile
            chile_tz = pytz.timezone('America/Santiago')
            ahora_chile = timezone.now().astimezone(chile_tz)
            # 1. Definimos el inicio del rango (ahora mismo)
            inicio_rango = ahora_chile
            # 2. Definimos el fin del rango (ejemplo: en 60 minutos más)
            fin_rango = ahora_chile + timedelta(minutes=60)
            print(f"Buscando reservas entre las {inicio_rango.time()} y las {fin_rango.time()}")
            # Ajustamos el filtro en la base de datos
            reservas_por_notificar = ReservaModel.objects.filter(
                fecha_reserva=ahora_chile.date(),
                hora_inicio__gte=inicio_rango.time(),
                hora_inicio__lt=fin_rango.time()
            )
            # Declaramos una variable para almacenar el nombre del paciente.
            nombre_pac_completo = ""
            # Adjuntar imagen al correo.
            for reserva in reservas_por_notificar:
                print("Ingresamos")
                if reserva.reser_confirmada == 0 and reserva.reser_anulada == 0:
                    self.stdout.write(f"Reserva ID: {reserva.id}, Hora Inicio: {reserva.hora_inicio}")
                    # Obtenemos el nombre del paciente para el correo.
                    print(reserva.fk_pac_no_register)
                    print(reserva.fk_usuario.id)
                    if reserva.fk_pac_no_register is not None:
                        paciente_no_registrado = PacienteNoRegisterModel.objects.filter(id=reserva.fk_pac_no_register.id).first()
                        nombre_pac_completo = paciente_no_registrado.primer_nombre + " " + paciente_no_registrado.segundo_nombre + " " + paciente_no_registrado.ap_paterno + " " + paciente_no_registrado.ap_materno
                        print(f"Paciente No Registrado: {nombre_pac_completo}")
                    # Obtenemos el nombre del paciente Registrado.
                    if reserva.fk_usuario is not None:
                        print("Ingresamos al Paciente Registrado")
                        paciente_registrado = PacienteModel.objects.filter(id=reserva.fk_usuario.id).first()
                        nombre_pac_completo = paciente_registrado.primer_nombre + " " + paciente_registrado.segundo_nombre + " " + paciente_registrado.ap_paterno + " " + paciente_registrado.ap_materno
                    print(f"Nombre del paciente para el correo: {nombre_pac_completo}")
                    # Esta es la ruta donde se encuentra la imagen del correo de confirmación de serva.
                    path_img = os.path.join(settings.BASE_DIR, 'static', 'img', 'img_confirmacion', 'Banner_confirmacion.png')
                    # Este es el método que encripta la reserva_uuid y genera el link de confirmación para el correo.
                    # El archivo se encuentra en reserva/utils.py.
                    link = generar_link_confirmacion(reserva.reserva_uuid)
                    print(f"Verificamos el links con el token encriptado: {link}")
                    # Necesitamos obtener el nombre del paciente completo.
                    # Preparar el contexto (Renderizamos primero)
                    html_content = render_to_string('pacientes/confirmacion_reserva_pac.html', {
                        'nombre_paciente': nombre_pac_completo,
                        'hora_inicio': reserva.hora_inicio,
                        'fecha_reserva': reserva.fecha_reserva,
                        'especialidad': reserva.especialidad,
                        'nombre_doctor': reserva.nombre_doctor,
                        'nombre_clinica': reserva.nombre_clinica,
                        'url_confirmar': link,
                        'url_anular': f"https://tu-dominio.com/reserva/anular/{reserva.reserva_uuid}",
                    })
                    print("Pasamos")
                    #'url_confirmar': f"https://jacruces91.pythonanywhere.com/reserva/api/confirmar_correo_reservas/{link}",
                    # 2. Crear el objeto de correo (Luego instanciamos)
                    email = EmailMultiAlternatives(
                        subject="Confirmación de su Reserva - Clínica",
                        body="Contenido en HTML",
                        from_email=settings.EMAIL_HOST_USER,
                        # Esto se debe modificar cuando este funcionando para que tome el correo correcto del usuario.
                        #to=[reserva.paciente.email]
                        to=["matiasfamilycrew@gmail.com"]
                    )
                    email.attach_alternative(html_content, "text/html")

                    # Adjuntar la imagen (Al final, usando el objeto email ya creado)
                    path_img = os.path.join(settings.BASE_DIR, 'static', 'img', 'img_confirmacion', 'Banner_confirmacion.png')
                    with open(path_img, 'rb') as f:
                        banner = MIMEImage(f.read())
                        banner.add_header('Content-ID', '<banner_clinica>')
                        email.attach(banner)
                    try:
                        print("Intentando enviar correo...")
                        email.send()
                        print("Correo enviado exitosamente.")
                    except Exception as err:
                        print(f"Aviso: No se pudo enviar el correo físico por restricciones de red del servidor: {err}")
                        print(f"PRUEBA ESTE LINK EN TU NAVEGADOR: {link}")
                    print("Final Correo")
                else:
                    print(f"Reserva ID: {reserva.id} ya confirmada o anulada, no se envía correo.")
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.stdout.write(self.style.ERROR(f"Error de conexión: {str(err)}"))