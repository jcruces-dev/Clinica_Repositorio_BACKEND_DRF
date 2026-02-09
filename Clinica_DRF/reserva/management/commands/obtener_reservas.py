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
            print(f"Hora actual en Chile: {ahora_chile}")
            # Calcular qué hora será en 60 minutos más (ignorando minutos/segundos)
            # Ejemplo: Si son las 07:05, buscaremos citas de las 08:00
            hora_objetivo = (ahora_chile + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            print(f"Buscando reservas para la hora: {hora_objetivo.time()}")
            # Filtrar en la BD de la Clínica Por la fecha actual y las reservas que comiencn en una hora más.
            reservas_por_notificar = ReservaModel.objects.filter(
                fecha_reserva=ahora_chile.date(),
                hora_inicio=hora_objetivo.time() 
            )
            # Adjuntar imagen al correo.
            for reserva in reservas_por_notificar:
                self.stdout.write(f"Reserva ID: {reserva.id}, Hora Inicio: {reserva.hora_inicio}")
                # Esta es la ruta donde se encuentra la imagen del correo de confirmación de serva.
                path_img_confirmacion = os.path.join(settings.BASE_DIR, 'static', 'img_confirmacion', 'Banner_confirmacion.png')
                # Este es el método que encripta la reserva_uuid y genera el link de confirmación para el correo.
                # El archivo se encuentra en reserva/utils.py.
                link = generar_link_confirmacion(reserva.reserva_uuid)
                # Preparar el contexto (Renderizamos primero)
                html_content = render_to_string('confirmacion_reserva.html', {
                    'nombre_paciente': f"{reserva.paciente.primer_nombre} {reserva.paciente.ap_paterno}",
                    'hora_inicio': reserva.hora_inicio,
                    'fecha_reserva': reserva.fecha_reserva,
                    'url_confirmar': f"https://jacruces91.pythonanywhere.com/reserva/api/confirmar_correo_reservas/{link}",
                    'url_anular': f"https://tu-dominio.com/reserva/anular/{reserva.reserva_uuid}",
                })
                #'url_confirmar': f"https://jacruces91.pythonanywhere.com/reserva/api/confirmar_correo_reservas/{link}",
                # 2. Crear el objeto de correo (Luego instanciamos)
                email = EmailMultiAlternatives(
                    subject="Confirmación de su Reserva - Clínica",
                    body="Contenido en HTML",
                    from_email=settings.EMAIL_HOST_USER,
                    to=[reserva.paciente.email]
                )
                email.attach_alternative(html_content, "text/html")

                # 3. Adjuntar la imagen (Al final, usando el objeto email ya creado)
                path_img = os.path.join(settings.BASE_DIR, 'static', 'img_confirmacion', 'Banner_confirmacion.png')
                with open(path_img, 'rb') as f:
                    banner = MIMEImage(f.read())
                    banner.add_header('Content-ID', '<banner_clinica>')
                    email.attach(banner)

                # email.send() # Descomenta para enviar
                #email.send()
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            self.stdout.write(self.style.ERROR(f"Error de conexión: {str(err)}"))
            
            