import uuid

import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from reserva.models import ReservaModel
from doctor.models import DoctorModel


@pytest.mark.django_db
def test_listar_doctores_masivo(crear_3_doctores):
    """
    Prueba que el endpoint de listar doctores devuelva
    los 3 registros creados dinámicamente por el fixture.
    """
    # 1. ARRANGE: El fixture 'crear_3_doctores' ya creó los 3 usuarios y doctores en la BD.

    # 2. ACT: Hacemos la petición HTTP
    client = APIClient()
    # Asegúrate de que el nombre de la URL coincida con tu archivo doctor/urls.py
    url = reverse("listar_doctor")
    response = client.get(url)

    print("RESPUESTA DEL SERVIDOR:", response.json())

    # 3. ASSERT: Verificamos
    assert response.status_code == 200
    data = response.json()

    # Validamos directamente la llave 'list_doctor'.
    assert "list_doctor" in data
    assert len(data["list_doctor"]) == 3

    # (Opcional) Validamos que los RUTs generados por Faker estén ahí
    assert data["list_doctor"][0]["rut"] is not None


@pytest.mark.django_db
def test_dashboard_doctor_query_optimization(
    crear_doctor_completo,
    crear_paciente,
    crear_clinica,
    crear_especialidad,
    django_assert_num_queries,  # 👈 ¡EL PARÁMETRO MÁGICO AQUÍ!
):
    """
    Prueba que el dashboard del doctor no haga consultas N+1 a la BD.
    """
    # 1. Preparamos los datos (igual que en tu test multi-modelo)
    nombre_doctor = f"{crear_doctor_completo.primer_nombre} {crear_doctor_completo.segundo_nombre} {crear_doctor_completo.ap_paterno} {crear_doctor_completo.ap_materno}"

    ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Paciente Test",
        fecha_reserva="2026-11-15",
        hora_inicio="10:00:00",
        hora_termino="11:00:00",
        especialidad=crear_especialidad.nombre_especialidad,
        nombre_doctor=nombre_doctor,
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=1,
        fk_usuario=crear_paciente.fk_user,
    )

    # 2. Aquí entra la magia del rendimiento
    # (Nota: El número 5 es una suposición. Si falla, el log te dirá el número real).
    with django_assert_num_queries(5):
        client = APIClient()
        client.force_authenticate(user=crear_doctor_completo.fk_user)
        url = reverse("listar_paciente_doctor_cita")
        response = client.get(url)
        assert response.status_code == 200
