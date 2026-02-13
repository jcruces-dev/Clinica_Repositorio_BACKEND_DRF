# reservas/utils.py
from django.core.signing import TimestampSigner
from django.utils.http import urlencode
from .models import ReservaModel
from .serializers import ReservaSerializer

# Este es un método de seguridadque sirve para encriptar lareserva_uuid y enviarla de forma segura en la URL.
def generar_link_confirmacion(reserva_uuid):
    signer = TimestampSigner()
    token = signer.sign(reserva_uuid)
    # Esto viene siuendo la reserva_uuid.
    params = urlencode({'token': token})
    url = f"https://jacruces91.pythonanywhere.com/reserva/api/confirmar_correo_reservas/{reserva_uuid}/?{params}"
    return url

# Este es un método de seguridadque sirve para encriptar lareserva_uuid y enviarla de forma segura en la URL.
def generar_link_anulacion(reserva_uuid):
    signer = TimestampSigner()
    token = signer.sign(reserva_uuid)
    # Esto viene siuendo la reserva_uuid.
    params = urlencode({'token': token})
    url = f"https://jacruces91.pythonanywhere.com/reserva/api/anular_reserva_paciente_correo/{reserva_uuid}/?{params}"
    return url