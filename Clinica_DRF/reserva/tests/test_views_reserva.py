from rest_framework.test import APIClient
from django.urls import reverse
from httpx import Response
import pytest

from comuna_clinica.models import ComunaClinicaModel


@pytest.mark.django_db
def test_listar_clinicas():
    # Crear una clínica de prueba en la base de datos
    ComunaClinicaModel.objects.create(
        nombre_clinica="Clínica de Prueba",
        comuna_clinica="Santiago",
        direccion_clinica="Av. Siempre Viva 123",
    )
    # Realizar una solicitud GET a la vista listar_clinica_index
    client = APIClient()
    url = reverse("listar_clinica_index")
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    # Verificar que la respuesta contiene la lista de clínicas
    assert "list_clinica" in data
    assert len(data["list_clinica"]) == 1
    assert data["list_clinica"][0]["nombre_clinica"] == "Clínica de Prueba"
