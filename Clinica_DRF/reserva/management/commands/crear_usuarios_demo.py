import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from direccion.models import DireccionModel
from usuarios.models import CustomersUsers
from doctor.models import DoctorModel
from secretaria.models import SecretariaModel
from paciente.models import PacienteModel
from comuna_clinica.models import ComunaClinicaModel
import random


# Utilizamos la clase BaseCommand para crear un comando personalizado de Django que permita crear usuarios de prueba de manera segura.
# Este comando crea un superusuario, un doctor, una secretaria y un paciente, asignándoles contraseñas  y asociándolos a grupos y
# clínicas según corresponda.
class Command(BaseCommand):
    help = (
        "Crea usuarios de prueba (Admin, Doctor, Secretaria, Paciente) de forma segura"
    )

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING("🚀 Iniciando creación de usuarios demo...")
        )
        # Inicializamos Faker para generar datos aleatorios en español (Chile).
        # fake = Faker("es_CL")

        # Creamos los grupos si no existen.
        grupo_doctor, _ = Group.objects.get_or_create(name="Doctor")
        grupo_secretaria, _ = Group.objects.get_or_create(name="Secretaria")
        grupo_paciente, _ = Group.objects.get_or_create(name="Paciente")

        # Creamos una Clínica base, es necesaria para probar las relaciones.
        clinica, _ = ComunaClinicaModel.objects.get_or_create(
            nombre_clinica="Clínica Demo Maipú",
            defaults={
                "comuna_clinica": "Maipú",
                "direccion_clinica": "Av. Demo Maipú #123",
            },
        )

        # Función auxiliar para hashear la contraseña.
        # Esta es la contraseña común que se asignará a todos los usuarios para la demostración.
        pwd_hash = make_password("1234")

        # Ahora devemos crear el Usuario Admin (plask) - Superusuario
        if not CustomersUsers.objects.filter(username="plask").exists():
            admin = CustomersUsers.objects.create_superuser(
                username="plask",
                password=pwd_hash,
                email="plask@demo.com",
                usuario_uuid=str(uuid.uuid4()),
            )
            self.stdout.write(self.style.SUCCESS("✅ Admin 'plask' creado."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Admin 'plask' ya existe."))

        # Verificamos que el usuario Doctor no exista.
        if not CustomersUsers.objects.filter(username="doctor_1").exists():
            user_doc = CustomersUsers.objects.create(
                username="doctor_1", password=pwd_hash, email="doc@demo.com"
            )
            # Agregamos al Doctor al grupo correspondiente.
            user_doc.groups.add(grupo_doctor)
            # Creamos el modelo Doctor asociado al usuario.
            doc = DoctorModel.objects.create(
                fk_user=user_doc,
                primer_nombre="Gregory",
                segundo_nombre="Isaac",
                ap_paterno="House",
                ap_materno="Smith",
                edad=45,
                sexo="M",
                rut="75.555.812-5",
                fono=f"+569{random.randint(10000000, 99999999)}",
                doctor_uuid=str(uuid.uuid4()),
            )
            # Asociamos el doctor a la clínica utilizando la relación (ManyToMany).
            doc.doctor_clinica.add(clinica)
            # Enviamos un mensaje de éxito a la consola indicando que el doctor ha sido creado.
            self.stdout.write(self.style.SUCCESS("✅ Doctor 'doctor_1' creado."))

        # Verificamos que el usuario Secretaria no exista.
        if not CustomersUsers.objects.filter(username="secre_1").exists():
            user_sec = CustomersUsers.objects.create(
                username="secre_1", password=pwd_hash, email="sec@demo.com"
            )
            user_sec.groups.add(grupo_secretaria)
            sec = SecretariaModel.objects.create(
                primer_nombre="Ana",
                segundo_nombre="María",
                ap_paterno="Perez",
                ap_materno="Gonzalez",
                edad=45,
                sexo="F",
                rut="77.183.814-6",
                fono=f"+569{random.randint(10000000, 99999999)}",
                secretaria_uuid=str(uuid.uuid4()),
                fk_user=user_sec,
            )
            # Asociar secretaria a la clínica
            sec.secretaria_clinica.add(clinica)
            self.stdout.write(self.style.SUCCESS("✅ Secretaria 'secre_1' creada."))

        # Verificamos que el usuario Paciente no exista.
        if not CustomersUsers.objects.filter(username="paciente_1").exists():
            # 1. Creamos el usuario base
            user_pac = CustomersUsers.objects.create(
                username="paciente_1", password=pwd_hash, email="pac@demo.com"
            )
            user_pac.groups.add(grupo_paciente)

            # 2. Creamos el perfil del Paciente (Llenamos todos los campos del diagrama)
            paciente_demo = PacienteModel.objects.create(
                fk_user=user_pac,
                primer_nombre="Juan",
                segundo_nombre="Carlos",
                ap_paterno="Gomez",
                ap_materno="Perez",
                edad=35,
                sexo="M",
                rut="92.272.361-3",
                fono=f"+569{random.randint(10000000, 99999999)}",
                paciente_uuid=str(uuid.uuid4()),
            )

            # 3. Creamos una Dirección para el paciente (Para que el dashboard no esté vacío)
            DireccionModel.objects.create(
                region="Metropolitana",
                comuna="Providencia",
                vivienda="Departamento",
                num_vivienda="123",
                fk_paciente=paciente_demo,
            )

            self.stdout.write(
                self.style.SUCCESS("✅ Paciente 'paciente_1' y su dirección creados.")
            )
