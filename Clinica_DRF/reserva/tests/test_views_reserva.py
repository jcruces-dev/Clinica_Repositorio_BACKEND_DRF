from rest_framework.test import APIClient
from django.urls import reverse
from httpx import Response
import pytest

from comuna_clinica.models import ComunaClinicaModel


#
@pytest.mark.django_db
def test_listar_clinicas(crear_clinica):
    print("ID DE LA CLÍNICA CREADA:", crear_clinica.id)
    # Realizar una solicitud GET a la vista listar_clinica_index
    client = APIClient()
    url = reverse("listar_clinica_index")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    print("RESPUESTA DEL SERVIDOR:", data)
    # Verificar que la respuesta contiene la lista de clínicas
    assert "list_clinica" in data
    assert len(data["list_clinica"]) == 1
    assert data["list_clinica"][0]["nombre_clinica"] == "Clinica Test"


#
@pytest.mark.django_db
def test_historial_reserva_paciente(crear_reserva):
    """
    Prueba que un paciente autenticado pueda ver su propio historial de reservas.
    """
    client = APIClient()
    # Autenticamos al paciente dueño de la reserva
    client.force_authenticate(user=crear_reserva.fk_usuario)
    print("ID DEL USUARIO PACIENTE AUTENTICADO")
    # La URL espera el ID del usuario
    url = reverse(
        "historial_reserva_pac", kwargs={"id_usuario": crear_reserva.fk_usuario.id}
    )

    response = client.get(url)
    print("RESPUESTA DEL SERVIDOR:", response.json())

    # Verificaciones
    assert response.status_code == 200
    data = response.json()
    print("DATOS DEVUELTOS POR LA API; test_historial_reserva_paciente:", data)
    # Comprobamos que la respuesta tenga la llave 'reserva' y traiga 1 registro
    assert "reserva" in data
    assert len(data["reserva"]) == 1

    # Comprobamos que los datos coincidan
    assert data["reserva"][0]["nombre_doctor"] == crear_reserva.nombre_doctor
    assert data["reserva"][0]["especialidad"] == "Medicina General"
