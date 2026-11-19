# Importa APIClient de DRF para simular peticiones HTTP a los endpoints de la API.
from rest_framework.test import APIClient

# Importa reverse para resolver las URLs de Django a partir del nombre de la vista.
from django.urls import reverse

# Importa Response desde httpx.
from httpx import Response

# Importa pytest para definir y ejecutar los casos de prueba.
import pytest

# Importa ComunaClinicaModel desde comuna_clinica.models.
from comuna_clinica.models import ComunaClinicaModel


# Marca el test para que pueda acceder a la base de datos de prueba de Django.
@pytest.mark.django_db
# Define el test de pago con débito desde el dashboard de un paciente registrado.
def test_pago_debito_desde_dashboard_registrado(crear_reserva, crear_especialidad):
    # Instancia un cliente HTTP de pruebas para hacer peticiones a la API.
    client = APIClient()
    # Autentica al cliente con el usuario asociado a la reserva creada.
    client.force_authenticate(user=crear_reserva.fk_usuario)

    # Obtiene la URL del endpoint para actualizar el pago con débito usando el UUID de la reserva.
    url = reverse(
        "update_pago_debito_reserva",
        kwargs={"reserva_uuid": crear_reserva.reserva_uuid},
    )
    # Prepara el payload indicando el UUID de la reserva y el pago con débito activado.
    data = {"reserva_uuid": crear_reserva.reserva_uuid, "debito": 1}

    # Se eliminaron los mocks de pdfkit y EmailMessage porque ya no se generan PDFs ni se envían correos.
    # Ejecuta una petición PUT al endpoint con los datos en formato JSON.
    response = client.put(url, data, format="json")

    # Verifica que la respuesta HTTP haya sido exitosa (200 OK).
    assert response.status_code == 200
    # Recarga la instancia de reserva desde la base de datos para reflejar cambios guardados.
    crear_reserva.refresh_from_db()
    # Verifica que el campo pago_realizado se haya actualizado a 1 tras el pago con débito.
    assert crear_reserva.pago_realizado == 1


# Marca el test para que pueda acceder a la base de datos de prueba de Django.
@pytest.mark.django_db
# Define el test de pago con crédito desde el dashboard de un paciente registrado.
def test_pago_credito_desde_dashboard_registrado(crear_reserva, crear_especialidad):
    # Instancia un cliente HTTP de pruebas para hacer peticiones a la API.
    client = APIClient()
    # Autentica al cliente con el usuario asociado a la reserva creada.
    client.force_authenticate(user=crear_reserva.fk_usuario)

    # Obtiene la URL del endpoint para actualizar el pago usando el UUID de la reserva.
    url = reverse(
        "update_pago_debito_reserva",
        kwargs={"reserva_uuid": crear_reserva.reserva_uuid},
    )
    # Prepara el payload indicando el UUID de la reserva y el pago con crédito activado.
    data = {"reserva_uuid": crear_reserva.reserva_uuid, "credito": 1}

    # Ejecuta una petición PUT al endpoint con los datos en formato JSON.
    response = client.put(url, data, format="json")

    # Verifica que la respuesta HTTP haya sido exitosa (200 OK).
    assert response.status_code == 200
    # Recarga la instancia de reserva desde la base de datos para reflejar cambios guardados.
    crear_reserva.refresh_from_db()
    # Verifica que el campo pago_realizado se haya actualizado a 1 tras el pago con crédito.
    assert crear_reserva.pago_realizado == 1


# Marca el test para permitir acceso a la base de datos de Django.
@pytest.mark.django_db
# Define el test que valida el rechazo de acceso sin autenticación al endpoint del dashboard.
def test_pago_debito_desde_dashboard_no_registrado_falla(crear_reserva_no_registrado):
    # Crea un cliente de pruebas sin autenticar ningún usuario.
    client = APIClient()

    # Resuelve la URL del endpoint usando el UUID de la reserva de paciente no registrado.
    url = reverse(
        "update_pago_debito_reserva",
        kwargs={"reserva_uuid": crear_reserva_no_registrado.reserva_uuid},
    )
    # Define el cuerpo de la petición con el UUID y el indicador de pago con débito.
    data = {"reserva_uuid": crear_reserva_no_registrado.reserva_uuid, "debito": 1}

    # Envía la petición PUT sin credenciales de autenticación.
    response = client.put(url, data, format="json")

    # Comprueba que el endpoint bloquee la petición con 401 (no autenticado) o 403 (prohibido).
    assert response.status_code in [401, 403]


# Marca el test para utilizar la base de datos de prueba de Django.
@pytest.mark.django_db
# Define el test de pago con débito desde el index para un paciente no registrado.
def test_pago_debito_desde_index_no_registrado(
    crear_reserva_no_registrado, crear_especialidad
):
    # Instancia el cliente de pruebas de DRF.
    client = APIClient()
    # Obtiene la URL del endpoint de pago con débito para reserva sin registro previo.
    url = reverse("pago_debito_solo_reserva")
    # Arma los datos enviados con el código UUID de la reserva a pagar.
    data = {"cod_reserva_pagar": crear_reserva_no_registrado.reserva_uuid}

    # Se eliminaron los mocks y aserciones de pdfkit y EmailMessage porque el envío de correo fue retirado.
    # Envía la petición POST al endpoint de pago en formato JSON.
    response = client.post(url, data, format="json")

    # Verifica que el endpoint responda con estado 200 OK.
    assert response.status_code == 200

    # Refresca el objeto de reserva desde la base de datos.
    crear_reserva_no_registrado.refresh_from_db()
    # Confirma que el pago quedó marcado como realizado (1).
    assert crear_reserva_no_registrado.pago_realizado == 1
