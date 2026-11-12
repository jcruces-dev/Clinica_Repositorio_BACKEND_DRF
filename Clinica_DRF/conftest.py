import uuid

import pytest
from django.contrib.auth.models import Group

# Importamos tus modelos
from especialidad.models import Especialidad
from reserva.models import ReservaModel
from usuarios.models import CustomersUsers
from comuna_clinica.models import ComunaClinicaModel
from secretaria.models import SecretariaModel
from doctor.models import DoctorModel
from paciente.models import PacienteModel
from paciente_no_registrado.models import PacienteNoRegisterModel

# Importamos tu instancia de Faker configurada con los providers chilenos
from utils.providers import fake

# Importamos make_password para encriptar contraseñas.
from django.contrib.auth.hashers import make_password

#
from django.utils import timezone

#
from datetime import date, datetime, time

# ==========================================
# 1. FIXTURES BASE (Crean los cimientos relacionales)
# ==========================================

# Crearemos los rut para los distintos tipos de usuarios
# (Secretaria, Doctor, Paciente Registrado y Paciente No Registrado).
RUTS_SECRETARIA = ["75.982.953-0", "81.661.739-1", "81.734.896-3"]
RUTS_DOCTOR = ["84.334.678-2", "86.879.070-9", "88.987.278-0"]
RUTS_PACIENTE = ["89.629.418-0", "94.448.358-6", "97.950.353-9"]
RUTS_PACIENTE_NO_REGISTRADO = ["98.757.278-7", "98.355.043-6", "96.100.398-9"]

# Creamos los teléfonos para los distintos tipos de usuarios.
FONOS_SECRETARIA = ["974699961", "974699962", "974699950"]
FONOS_DOCTOR = ["974699970", "974699950", "974699980"]
FONOS_PACIENTE = ["974699990", "974699900", "974699910"]
FONOS_PACIENTE_NO_REGISTRADO = ["974699950", "974698950", "974698951"]


@pytest.fixture
def crear_clinica(db):
    """Crea una clínica de prueba reutilizable."""
    return ComunaClinicaModel.objects.create(
        nombre_clinica="Clinica Test",
        comuna_clinica="Santiago",
        direccion_clinica="Calle Falsa 123",
    )


# Creamos los grupos de usuarios (Secretaria, Doctor, Paciente) para asignarlos a los usuarios en los tests.
@pytest.fixture
def crear_grupo_secretaria(db):
    return Group.objects.create(name="Secretaria")


# Creamos los grupos de usuarios (Secretaria, Doctor, Paciente) para asignarlos a los usuarios en los tests.
@pytest.fixture
def crear_grupo_doctor(db):
    return Group.objects.create(name="Doctor")


# Creamos los grupos de usuarios (Secretaria, Doctor, Paciente) para asignarlos a los usuarios en los tests.
@pytest.fixture
def crear_grupo_paciente(db):
    return Group.objects.create(name="Paciente")


# ==========================================
# 2. FIXTURES DE USUARIOS (Encadenados a los grupos)
# ==========================================
@pytest.fixture
def crear_user_secretaria(db, crear_grupo_secretaria):
    # Usamos fake.unique para evitar errores si un test llama al fixture varias veces
    user = CustomersUsers.objects.create_user(
        username=fake.unique.user_name(),
        is_staff=False,
        is_active=True,
        date_joined=timezone.now(),
        password="123",
        email=fake.unique.email(),
    )
    user.groups.add(crear_grupo_secretaria)
    return user


@pytest.fixture
def crear_user_doctor(db, crear_grupo_doctor):
    user = CustomersUsers.objects.create_user(
        username=fake.unique.user_name(),
        is_staff=False,
        is_active=True,
        date_joined=timezone.now(),
        password="123",
        email=fake.unique.email(),
    )
    user.groups.add(crear_grupo_doctor)
    return user


@pytest.fixture
def crear_user_paciente(db, crear_grupo_paciente):
    user = CustomersUsers.objects.create_user(
        username=fake.unique.user_name(),
        is_staff=False,
        is_active=True,
        date_joined=timezone.now(),
        password="123",
        email=fake.unique.email(),
    )
    user.groups.add(crear_grupo_paciente)
    return user


# ==========================================
# 3. FIXTURES DE PERFILES INDIVIDUALES
# ==========================================
@pytest.fixture
def crear_secretaria(db, crear_user_secretaria, crear_clinica):
    # Creamos una secretaria asociada a un usuario y a una clínica.
    secre = SecretariaModel.objects.create(
        fk_user_id=crear_user_secretaria.id,
        primer_nombre=fake.first_name(),
        segundo_nombre=fake.first_name(),
        ap_paterno=fake.last_name(),
        ap_materno=fake.last_name(),
        edad=fake.random_int(min=20, max=60),
        sexo="F",
        rut=fake.random_element(elements=RUTS_SECRETARIA),
        fono=fake.random_element(elements=FONOS_SECRETARIA),
    )
    # Obtenemos la clinica de la SECRETARIA.
    secre.secretaria_clinica.add(crear_clinica)
    #
    return secre


@pytest.fixture
def crear_doctor(db, crear_user_doctor, crear_clinica):
    return DoctorModel.objects.create(
        fk_user_id=crear_user_doctor.id,
        primer_nombre=fake.first_name(),
        segundo_nombre=fake.first_name(),
        ap_paterno=fake.last_name(),
        ap_materno=fake.last_name(),
        edad=45,
        sexo="M",
        fono="74699987",
        rut="71.306.146-8",
    )


@pytest.fixture
def crear_paciente(db, crear_user_paciente):
    return PacienteModel.objects.create(
        fk_user_id=crear_user_paciente.id,
        primer_nombre=fake.first_name(),
        segundo_nombre=fake.first_name(),
        ap_paterno=fake.last_name(),
        ap_materno=fake.last_name(),
        edad=45,
        sexo="M",
        fono="74699987",
        rut="72.606.703-1",
    )


@pytest.fixture
def crear_paciente_no_registrado(db):
    return PacienteNoRegisterModel.objects.create(
        primer_nombre=fake.first_name(),
        segundo_nombre=fake.first_name(),
        ap_paterno=fake.last_name(),
        ap_materno=fake.last_name(),
        edad=45,
        sexo="M",
        fono="74699987",
        rut="84.837.425-3",
    )


# ==========================================
# 4. FIXTURES MASIVOS (Crean 3 registros usando un bucle)
# ==========================================
@pytest.fixture
def crear_3_secretarias(db, crear_clinica, crear_grupo_secretaria):
    """Crea 3 secretarias usando RUTs únicos de la lista."""
    secretarias = []
    # Recorremos la lista de RUTs directamente (así garantizamos que no se repitan)
    for i, rut_unico in enumerate(RUTS_SECRETARIA):
        # Creamos un usuario para la secretaria.
        user = CustomersUsers.objects.create_user(
            username=fake.unique.user_name(),
            password="123",
            email=fake.unique.email(),
        )
        # Asignamos el grupo de secretaria al usuario
        user.groups.add(crear_grupo_secretaria)
        # Creamos la secretaria con el RUT específico de la lista
        secre = SecretariaModel.objects.create(
            fk_user_id=user.id,
            primer_nombre=fake.first_name(),
            segundo_nombre=fake.first_name(),
            ap_paterno=fake.last_name(),
            ap_materno=fake.last_name(),
            edad=fake.random_int(min=20, max=60),
            sexo=fake.random_element(elements=("M", "F")),
            # 👈 Aquí asignamos el RUT exacto de la lista
            rut=rut_unico,
            fono=fake.random_element(elements=FONOS_SECRETARIA),
        )
        secre.secretaria_clinica.add(crear_clinica)
        secretarias.append(secre)

    return secretarias


@pytest.fixture
def crear_3_doctores(db, crear_clinica, crear_grupo_doctor):
    """Crea 3 doctores con datos aleatorios para pruebas de volumen."""
    doctores = []
    for _ in range(3):
        user = CustomersUsers.objects.create_user(
            username=fake.unique.user_name(), password="123", email=fake.unique.email()
        )
        user.groups.add(crear_grupo_doctor)
        doc = DoctorModel.objects.create(
            fk_user_id=user.id, primer_nombre=fake.first_name(), rut="76.841.557-9"
        )
        doctores.append(doc)
    return doctores


@pytest.fixture
def crear_3_pacientes_no_registrados(db):
    """Crea 3 pacientes no registrados (sin usuario asociado)."""
    pacientes = []
    for _ in range(3):
        pac = PacienteNoRegisterModel.objects.create(
            primer_nombre=fake.first_name(), rut=fake.rut(), email=fake.unique.email()
        )
        pacientes.append(pac)
    return pacientes


@pytest.fixture
def crear_reserva(db, crear_paciente, crear_clinica, crear_doctor):
    """Crea una reserva asociada a un paciente y un doctor."""
    return ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Paciente Test",
        fecha_reserva="2026-11-15",
        # pasamos la hora en STRING para no tener problemas.
        hora_inicio="10:00:00",
        hora_termino="11:00:00",
        especialidad="Medicina General",
        nombre_doctor=f"{crear_doctor.primer_nombre} {crear_doctor.ap_paterno}",
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=1,
        # Asociada al paciente del fixture
        fk_usuario=crear_paciente.fk_user,
    )


#
@pytest.fixture
def crear_reserva_no_registrado(
    db, crear_paciente_no_registrado, crear_clinica, crear_doctor
):
    """Crea una reserva asociada a un paciente no registrado y un doctor."""
    return ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Invitado",
        fecha_reserva=date(2026, 11, 10),
        hora_inicio=time(15, 0),
        hora_termino=time(15, 30),
        especialidad="Medicina General",
        nombre_doctor=f"{crear_doctor.primer_nombre} {crear_doctor.ap_paterno}",
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=0,
        # Asociada al paciente no registrado del fixture.
        fk_pac_no_register=crear_paciente_no_registrado,
    )


#
@pytest.fixture
def crear_especialidad(db):
    """Crea una especialidad en la BD para que las reservas puedan usarla."""
    return Especialidad.objects.create(
        nombre_especialidad="Medicina General", valor_especialidad=20000
    )


@pytest.fixture
def crear_reserva(db, crear_paciente, crear_clinica, crear_doctor, crear_especialidad):
    # Agregamos 'crear_especialidad' al final de los parámetros para utilizarlo mas facil en los test.

    return ReservaModel.objects.create(
        fecha_creacion_reserva="2026-11-04T10:00:00Z",
        usuario_creacion_reserva="Paciente Test",
        # STRING
        fecha_reserva="2026-11-15",
        # STRING
        hora_inicio="10:00:00",
        hora_termino="11:00:00",
        # Debe coincidir con el nombre del fixture
        especialidad="Medicina General",
        nombre_doctor=f"{crear_doctor.primer_nombre} {crear_doctor.ap_paterno}",
        tipo_pago="0",
        reserva_uuid=str(uuid.uuid4()),
        nombre_clinica=crear_clinica.nombre_clinica,
        direccion_clinica=crear_clinica.direccion_clinica,
        comuna_clinica=crear_clinica.comuna_clinica,
        pago_realizado=1,
        fk_usuario=crear_paciente.fk_user,
    )


#
@pytest.fixture
def crear_doctor_completo(db, crear_user_doctor, crear_clinica, crear_especialidad):
    from doctor.models import DoctorModel

    doctor = DoctorModel.objects.create(
        fk_user=crear_user_doctor,
        primer_nombre="Gregory",
        segundo_nombre="John",
        ap_paterno="House",
        ap_materno="Test",
        rut="73.126.463-5",
    )
    doctor.doctor_clinica.add(crear_clinica)
    doctor.especialidades.add(crear_especialidad)
    return doctor
