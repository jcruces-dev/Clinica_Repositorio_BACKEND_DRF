import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from reserva.models import ReservaModel
import uuid
from django.core.signing import TimestampSigner


@pytest.mark.django_db
def test_rechazar_sobre_reserva_mismo_doctor_y_hora(
    crear_clinica,
    crear_especialidad,
    crear_doctor_completo,
    mocker,  # 👈 Agregamos mocker
):
    # ==========================================
    # 1. ARRANGE (Preparar el escenario)
    # ==========================================
    nombre_completo_doc = f"{crear_doctor_completo.primer_nombre} {crear_doctor_completo.segundo_nombre} {crear_doctor_completo.ap_paterno} {crear_doctor_completo.ap_materno}"

    # Creamos la reserva que ya ocupa el cupo (usando strings para evitar problemas de formato)
    ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Paciente 1",
        fecha_reserva="2026-11-15",
        hora_inicio="10:00:00",
        hora_termino="10:30:00",
        especialidad=crear_especialidad.nombre_especialidad,
        nombre_doctor=nombre_completo_doc,
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=1,
    )

    # ==========================================
    # 2. ACT (Intentar pagar/agendar a la misma hora)
    # ==========================================
    client = APIClient()

    # 👈 AQUÍ CAMBIAMOS AL ENDPOINT DE PAGO QUE TIENE LA VALIDACIÓN
    url = reverse("pago_stripe_reserva_index")

    # 👈 AGREGAMOS LOS NOMBRES EXACTOS QUE ESPERA EL FILTRO DE LA VISTA
    data = {
        "id_clinica": crear_clinica.id,
        "id_especialidad": crear_especialidad.id,
        "id_doctor": crear_doctor_completo.id,
        "especialidad": crear_especialidad.nombre_especialidad,  # Requerido por el filtro
        "nombre_clinica": crear_clinica.nombre_clinica,  # Requerido por el filtro
        "nombre_doctor": nombre_completo_doc,  # Requerido por el filtro
        "primer_nombre": "Paciente",
        "segundo_nombre": "Dos",
        "ap_paterno": "Test",
        "ap_materno": "Test",
        "email": "paciente2@test.com",
        "edad": 25,
        "fono": "912345678",
        "sexo": "F",
        "rut": "73.492.412-1",
        "fecha_reserva": "15-11-2026",  # La vista lo convierte a "2026-11-15"
        "hora_inicio": "10:00:00",
        "hora_termino": "11:00:00",
        "nombre_paciente": "Paciente Dos",
        "valor_especialidad": 20000,
        "direccion_clinica": crear_clinica.direccion_clinica,
        "comuna_clinica": crear_clinica.comuna_clinica,
    }

    # Mockeamos Stripe por si la validación falla (aunque si funciona, no llega a Stripe)
    mocker.patch("reserva.views.stripe.PaymentIntent.create")

    response = client.post(url, data, format="json")
    print("RESPUESTA DEL SERVIDOR:", response.json())

    # ==========================================
    # 3. ASSERT (Verificar que fue bloqueado)
    # ==========================================
    assert response.status_code == 400
    assert response.json() == {"error": 8}
    assert ReservaModel.objects.count() == 1


#
@pytest.mark.django_db
def test_anulacion_reserva_con_tokens(crear_reserva):
    """
    Prueba la seguridad y el flujo de anulación de una reserva mediante tokens.
    """
    client = APIClient()
    # El endpoint de anulación no requiere autenticación (AllowAny)

    url = reverse("anular_reserva", kwargs={"reserva_uuid": crear_reserva.reserva_uuid})

    # ==========================================
    # CASO 1: Token Inválido o Falso (Intento de hackeo)
    # ==========================================
    token_falso = "esto-es-un-token-falso-inventado-por-un-hacker"
    response_falso = client.get(f"{url}?token={token_falso}")

    print("RESPUESTA TOKEN FALSO:", response_falso.json())

    # Verificamos que la seguridad bloquee el intento
    assert response_falso.status_code == 400
    assert response_falso.json() == {"error": "Enlace no válido."}

    # La reserva NO debe haber cambiado
    crear_reserva.refresh_from_db()
    assert crear_reserva.reser_anulada == 0  # Asumiendo que 0 es "no anulada"

    # ==========================================
    # CASO 2: Token Real (El paciente hace clic en el correo)
    # ==========================================
    # Usamos el mismo mecanismo que tu aplicación para firmar el token
    signer = TimestampSigner()
    token_real = signer.sign(crear_reserva.reserva_uuid)

    response_real = client.get(f"{url}?token={token_real}")

    # Como tu vista devuelve un render() de HTML, verificamos el status y el contenido
    assert response_real.status_code == 200
    assert "text/html" in response_real["Content-Type"]

    # Verificamos que la base de datos se actualizó correctamente
    crear_reserva.refresh_from_db()
    assert crear_reserva.reser_anulada == 1  # Ahora está anulada
    assert crear_reserva.fecha_reserva is None
    assert crear_reserva.hora_inicio is None
    assert crear_reserva.hora_termino is None


@pytest.mark.django_db
def test_dashboard_doctor_multi_modelo(
    crear_doctor_completo, crear_paciente, crear_clinica, crear_especialidad
):
    """
    Prueba que un doctor pueda ver a sus pacientes en su dashboard.
    Cruza 4 tablas: User (Doctor) -> Doctor -> Reserva -> Paciente.
    """
    # ==========================================
    # 1. ARRANGE (Preparar el escenario)
    # ==========================================
    # Armamos el nombre exactamente como lo hace la vista del doctor
    nombre_doctor_completo = f"{crear_doctor_completo.primer_nombre} {crear_doctor_completo.segundo_nombre} {crear_doctor_completo.ap_paterno} {crear_doctor_completo.ap_materno}"

    # Creamos la reserva vinculada al paciente y al doctor
    ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Paciente Test",
        fecha_reserva="2026-11-15",
        hora_inicio="10:00:00",
        hora_termino="11:00:00",
        especialidad=crear_especialidad.nombre_especialidad,
        nombre_doctor=nombre_doctor_completo,  # 👈 Debe coincidir con el nombre del doctor
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=1,
        # Crucial para que mi vista o views donde se encuentra el código lo encuentre.
        fk_usuario=crear_paciente.fk_user,
    )

    # ==========================================
    # 2. ACT (El doctor se loguea y pide sus pacientes)
    # ==========================================
    client = APIClient()
    # Autenticamos como el DOCTOR (no como el paciente)
    client.force_authenticate(user=crear_doctor_completo.fk_user)

    url = reverse("listar_paciente_doctor_cita")
    response = client.get(url)

    print("RESPUESTA DEL DASHBOARD DOCTOR:", response.json())

    # ==========================================
    # 3. ASSERT (Verificar el cruce de datos)
    # ==========================================
    assert response.status_code == 200
    data = response.json()

    # La vista devuelve una llave 'paciente'
    assert "paciente" in data
    assert len(data["paciente"]) == 1

    # Verificamos que los datos cruzados entre las tablas sean correctos
    reserva_data = data["paciente"][0]

    nombre_paciente_esperado = f"{crear_paciente.primer_nombre} {crear_paciente.segundo_nombre} {crear_paciente.ap_paterno} {crear_paciente.ap_materno}"

    assert reserva_data["nombre_paciente"] == nombre_paciente_esperado
    assert reserva_data["rut"] == crear_paciente.rut
    assert reserva_data["tipo_paciente"] == "registrado"
