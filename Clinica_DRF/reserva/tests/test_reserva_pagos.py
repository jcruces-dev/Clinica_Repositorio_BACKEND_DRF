from rest_framework.test import APIClient
from django.urls import reverse
from httpx import Response
import pytest
from comuna_clinica.models import ComunaClinicaModel


#
@pytest.mark.django_db
def test_pago_debito_desde_dashboard_registrado(
    crear_reserva, crear_especialidad, mocker
):
    client = APIClient()
    # Autenticamos al paciente (Simula que está en su dashboard)
    client.force_authenticate(user=crear_reserva.fk_usuario)

    # Endpoint del dashboard
    url = reverse(
        "update_pago_debito_reserva",
        kwargs={"reserva_uuid": crear_reserva.reserva_uuid},
    )
    data = {"reserva_uuid": crear_reserva.reserva_uuid, "debito": 1}

    # Mockeamos servicios externos
    mocker.patch("reserva.views.pdfkit")
    mocker.patch("reserva.views.EmailMessage")

    response = client.put(url, data, format="json")

    assert response.status_code == 200
    crear_reserva.refresh_from_db()
    assert crear_reserva.pago_realizado == 1


# La API rechaza la petición si no hay un usuario autenticado.
@pytest.mark.django_db
def test_pago_debito_desde_dashboard_no_registrado_falla(crear_reserva_no_registrado):
    client = APIClient()
    # NO autenticamos al usuario (Simula un intento de hackeo o acceso público)

    url = reverse(
        "update_pago_debito_reserva",
        kwargs={"reserva_uuid": crear_reserva_no_registrado.reserva_uuid},
    )
    data = {"reserva_uuid": crear_reserva_no_registrado.reserva_uuid, "debito": 1}

    response = client.put(url, data, format="json")

    # El sistema debe bloquearlo con un 401 Unauthorized o 403 Forbidden
    assert response.status_code in [401, 403]


# Paciente No Registrado paga desde el Index (Éxito).
@pytest.mark.django_db
def test_pago_debito_desde_index_no_registrado(
    crear_reserva_no_registrado, crear_especialidad, mocker
):
    client = APIClient()
    url = reverse("pago_debito_solo_reserva")
    data = {"cod_reserva_pagar": crear_reserva_no_registrado.reserva_uuid}

    # Mockeamos toda la clase EmailMessage, no solo el método send
    mock_pdf = mocker.patch("reserva.views.pdfkit")
    mock_email_class = mocker.patch("reserva.views.EmailMessage")

    response = client.post(url, data, format="json")

    assert response.status_code == 200

    crear_reserva_no_registrado.refresh_from_db()
    assert crear_reserva_no_registrado.pago_realizado == 1

    # Ajustamos los asserts al nuevo Mock
    # Verificamos que se llamó a la función que crea el string del PDF
    mock_pdf.from_string.assert_called_once()

    # Verificamos que se instanció la clase de correo y se llamó al método send de esa instancia
    mock_email_class.assert_called_once()
    mock_email_class.return_value.send.assert_called_once()
