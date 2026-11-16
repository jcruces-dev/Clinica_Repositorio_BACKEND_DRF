from django.core.management.base import BaseCommand

from django.contrib.auth.hashers import make_password
from django.utils import timezone
import uuid
import hashlib
import random
from datetime import datetime, timedelta

import environ
import os

import pandas as pd

from faker import Faker
from utils.providers import fake

from usuarios.models import CustomersUsers
from especialidad.models import Especialidad
from comuna_clinica.models import ComunaClinicaModel
from direccion.models import DireccionModel
from paciente_no_registrado.models import PacienteNoRegisterModel
from doctor.models import DoctorModel
from paciente.models import PacienteModel
from historial_clinico.models import HistorialClinicoModel
from secretaria.models import SecretariaModel
from reserva.models import ReservaModel
from debito.models import DebitoModel
from credito.models import CreditoModel
from historial_pac_no_registrado.models import HistorialPacNoRegistradoModel

import math
from django.contrib.auth.models import Group

env = environ.Env()


class Command(BaseCommand):
    help = "Script de Carga Masiva para poblar el sistema BuenPaciente en TEST"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING(
                "⚡ Iniciando el proceso de sembrado de datos (Seeding) para TEST..."
            )
        )
        DireccionModel.objects.all().delete()
        DoctorModel.objects.all().delete()
        SecretariaModel.objects.all().delete()
        PacienteModel.objects.all().delete()
        HistorialClinicoModel.objects.all().delete()
        PacienteNoRegisterModel.objects.all().delete()
        HistorialPacNoRegistradoModel.objects.all().delete()
        ReservaModel.objects.all().delete()
        CreditoModel.objects.all().delete()
        DebitoModel.objects.all().delete()
        Especialidad.objects.all().delete()
        ComunaClinicaModel.objects.all().delete()

        CustomersUsers.objects.filter(is_superuser=False).delete()
        Group.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("  🗑️ Base de datos limpia y lista para la siembra.")
        )

        self.insertar_grupos()
        self.insertar_usuario_admin()
        self.insertar_clinicas()
        self.insertar_especialidad()
        self.insertar_usuario_doctor()
        self.insertar_usuario_secretaria()
        self.insertar_usuario_paciente()

        horarios_globales = set()

        self.insertar_reserva_paciente_registrado(horarios_ocupados=horarios_globales)
        self.insertar_historial_paciente_registrado()

        self.insertar_paciente_no_registrado()

        self.insertar_reserva_paciente_no_registrado(
            horarios_ocupados=horarios_globales
        )
        self.insertar_historial_paciente_no_registrado()

        self.stdout.write(self.style.SUCCESS("¡Proceso finalizado con éxito!"))

    def insertar_grupos(self):
        self.stdout.write("Procesando grupos de permisos con Pandas...")
        Group.objects.all().delete()
        df_grupos = pd.DataFrame({"name": ["Paciente", "Doctor", "Secretaria"]})
        registros = df_grupos.to_dict("records")
        objetos_grupos = [Group(**reg) for reg in registros]
        Group.objects.bulk_create(objetos_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 3 Grupos (Paciente, Doctor, Secretaria) creados correctamente."
            )
        )

    def insertar_usuario_admin(self):
        self.stdout.write("Creando usuario superusuario (admin de Django)...")

        if CustomersUsers.objects.filter(username="plask").exists():
            admin_user = CustomersUsers.objects.get(username="plask")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ Usuario 'plask' ya existía. Flags de superusuario asegurados."
                )
            )
            return

        admin_user = CustomersUsers.objects.create_superuser(
            username="plask",
            email="admin@buenpaciente.cl",
            password="1234",
            usuario_uuid=str(uuid.uuid4()),
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Superusuario 'plask' creado con password '1234' (sin grupo asignado)."
            )
        )

    def insertar_clinicas(self):
        datos_clinica = {
            "nombre_clinica": [
                "Clínica BuenPaciente - Sede Providencia",
                "Clínica BuenPaciente - Sede Las Condes",
                "Clínica BuenPaciente - Sede Maipú",
                "Clínica BuenPaciente - Sede Vitacura",
                "Clínica BuenPaciente - Sede Santiago Centro",
            ],
            "comuna_clinica": [
                "Providencia",
                "Las Condes",
                "Maipú",
                "Vitacura",
                "Santiago Centro",
            ],
            "direccion_clinica": [
                "Av. Providencia #1234",
                "Esquina Álvarez con Roberto #456",
                "Av. Pajaritos #5678",
                "Av. Vitacura #5678",
                "Santiago Centro #5812",
            ],
        }
        lista = []
        for i in range(len(datos_clinica["nombre_clinica"])):
            registro = {
                "nombre_clinica": datos_clinica["nombre_clinica"][i],
                "comuna_clinica": datos_clinica["comuna_clinica"][i],
                "direccion_clinica": datos_clinica["direccion_clinica"][i],
            }
            lista.append(registro)
        objetos_clinica = [ComunaClinicaModel(**reg) for reg in lista]
        ComunaClinicaModel.objects.bulk_create(objetos_clinica)
        self.stdout.write(
            self.style.SUCCESS("  ✅ 5 Clínicas insertadas correctamente.")
        )

    def insertar_especialidad(self):
        datos_especialidad = {
            "nombre_especialidad": [
                "Medicina General",
                "Pediatría",
                "Ginecología",
                "Traumatología",
                "Cardiología",
                "Dermatología",
                "Oftalmología",
                "Odontología",
                "Neurología",
                "Psiquiatría",
                "Oncología",
                "Nutrición",
            ],
            "valor_especialidad": [
                30000,
                40000,
                40000,
                50000,
                50000,
                45000,
                45000,
                18000,
                60000,
                80000,
                56000,
                35000,
            ],
        }
        df_especialidad = pd.DataFrame(datos_especialidad)
        registro_especialidad = df_especialidad.to_dict("records")
        objetos_especialidad = [Especialidad(**reg) for reg in registro_especialidad]
        Especialidad.objects.bulk_create(objetos_especialidad)
        self.stdout.write(
            self.style.SUCCESS("  ✅ Especialidades insertadas correctamente.")
        )

    def insertar_usuario_doctor(self):
        grupo_doctor = Group.objects.get(name="Doctor")
        fake = Faker("es_CL")
        lista_usuarios_data = []
        lista_doctores_data = []
        password_hash = make_password("123")

        for i in range(1, 6):
            sexo = random.choice(["M", "F"])
            edad_doctor = fake.random_int(min=25, max=60)

            if sexo == "M":
                primer_nombre_doctor = fake.first_name_male()
                segundo_nombre_doctor = fake.first_name_male()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "M"
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                email = f"{username_doctor}@gmail.com"
                password = password_hash

                data_user = {
                    "username": username_doctor,
                    "password": password,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    lista_usuarios_data.append(data_user)
                    data_doctor = {
                        "primer_nombre": primer_nombre_doctor,
                        "segundo_nombre": segundo_nombre_doctor,
                        "ap_paterno": ap_paterno_doctor,
                        "ap_materno": ap_materno_doctor,
                        "edad": edad_doctor,
                        "sexo": sexo_doctor,
                        "fono": telefono_doctor,
                        "doctor_uuid": str(uuid.uuid4()),
                    }
                    lista_doctores_data.append(data_doctor)
            else:
                primer_nombre_doctor = fake.first_name_female()
                segundo_nombre_doctor = fake.first_name_female()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "F"
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                email = f"{username_doctor}@gmail.com"
                password = password_hash

                data_user = {
                    "username": username_doctor,
                    "password": password,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    lista_usuarios_data.append(data_user)
                    data_doctor = {
                        "primer_nombre": primer_nombre_doctor,
                        "segundo_nombre": segundo_nombre_doctor,
                        "ap_paterno": ap_paterno_doctor,
                        "ap_materno": ap_materno_doctor,
                        "edad": edad_doctor,
                        "sexo": sexo_doctor,
                        "fono": telefono_doctor,
                        "doctor_uuid": str(uuid.uuid4()),
                    }
                    lista_doctores_data.append(data_doctor)

        instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(
            self.style.SUCCESS("  ✅ 5 Usuarios base (Doctores) creados.")
        )

        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_doctor.id)
            for user in usuarios_creados
        ]
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 5 Usuarios asignados al Grupo 'Doctor' exitosamente."
            )
        )

        for idx, user in enumerate(usuarios_creados):
            lista_doctores_data[idx]["fk_user_id"] = user.id

        instancias_doctores = [DoctorModel(**reg) for reg in lista_doctores_data]
        doctores_creados = DoctorModel.objects.bulk_create(instancias_doctores)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 5 Perfiles de Doctores creados en la base de datos."
            )
        )

        self.stdout.write("Asociando doctores a sus clínicas de forma aleatoria...")
        DoctorClinica = DoctorModel._meta.get_field(
            "doctor_clinica"
        ).remote_field.through
        lista_relaciones_clinicas = []
        clinicas_disponibles = list(
            ComunaClinicaModel.objects.values_list("id", flat=True)
        )

        if not clinicas_disponibles:
            clinicas_disponibles = [1, 2, 3, 4, 5]

        for doc in doctores_creados:
            cantidad_clinicas = random.randint(1, 2)
            clinicas_asignadas = random.sample(
                clinicas_disponibles, min(len(clinicas_disponibles), cantidad_clinicas)
            )
            for clinica_id in clinicas_asignadas:
                lista_relaciones_clinicas.append(
                    DoctorClinica(
                        doctormodel_id=doc.id,
                        comunaclinicamodel_id=clinica_id,
                    )
                )
        DoctorClinica.objects.bulk_create(lista_relaciones_clinicas)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Clínica inyectadas correctamente."
            )
        )

        lista_relaciones_especialidades = []
        DoctorEspecialidad = DoctorModel._meta.get_field(
            "especialidades"
        ).remote_field.through
        listado_especialidades = list(Especialidad.objects.values_list("id", flat=True))

        if not listado_especialidades:
            self.stdout.write(
                self.style.ERROR("❌ No se encontraron especialidades creadas.")
            )
            return

        for doc in doctores_creados:
            cantidad_especialidades = random.randint(1, 2)
            especialidades_asignadas = random.sample(
                listado_especialidades,
                min(len(listado_especialidades), cantidad_especialidades),
            )
            for esp_id in especialidades_asignadas:
                lista_relaciones_especialidades.append(
                    DoctorEspecialidad(
                        doctormodel_id=doc.id,
                        especialidad_id=esp_id,
                    )
                )
        DoctorEspecialidad.objects.bulk_create(lista_relaciones_especialidades)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Especialidad inyectadas correctamente."
            )
        )

    def insertar_usuario_secretaria(self):
        grupo_secretaria = Group.objects.get(name="Secretaria")
        fake = Faker("es_CL")
        lista_usuarios_data = []
        lista_secretaria_data = []

        for i in range(1, 6):
            primer_nombre_doctor = fake.first_name()
            segundo_nombre_doctor = fake.first_name()
            ap_paterno_doctor = fake.last_name()
            ap_materno_doctor = fake.last_name()
            edad_secretaria = fake.random_int(min=25, max=60)
            sexo_secretaria = fake.random_element(elements=("M", "F"))
            telefono_secretaria = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
            primer_nombre_corto = primer_nombre_doctor[:3].lower()
            ap_paterno_corto = ap_paterno_doctor[:3].lower()
            username_secretaria = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
            email = f"{username_secretaria}@gmail.com"
            password = make_password("123")

            data_user = {
                "username": username_secretaria,
                "password": password,
                "email": email,
                "usuario_uuid": str(uuid.uuid4()),
            }
            if not CustomersUsers.objects.filter(username=username_secretaria).exists():
                lista_usuarios_data.append(data_user)

            data_secreatria = {
                "primer_nombre": primer_nombre_doctor,
                "segundo_nombre": segundo_nombre_doctor,
                "ap_paterno": ap_paterno_doctor,
                "ap_materno": ap_materno_doctor,
                "edad": edad_secretaria,
                "sexo": sexo_secretaria,
                "fono": telefono_secretaria,
                "secretaria_uuid": str(uuid.uuid4()),
            }
            lista_secretaria_data.append(data_secreatria)

        df_usuarios = pd.DataFrame(lista_usuarios_data)
        instancias_usuarios = [
            CustomersUsers(**reg) for reg in df_usuarios.to_dict("records")
        ]
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(
            self.style.SUCCESS("  ✅ 5 Usuarios base (Secretarias) creados.")
        )

        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_secretaria.id)
            for user in usuarios_creados
        ]
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 5 Usuarios asignados al Grupo 'Secretaria' exitosamente."
            )
        )

        for idx, user in enumerate(usuarios_creados):
            lista_secretaria_data[idx]["fk_user_id"] = user.id

        df_secretaria = pd.DataFrame(lista_secretaria_data)
        instancias_secretaria = [
            SecretariaModel(**reg) for reg in df_secretaria.to_dict("records")
        ]
        secretarias_creados = SecretariaModel.objects.bulk_create(instancias_secretaria)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 5 Perfiles de Secretarias creados en la base de datos."
            )
        )

        self.stdout.write("Asociando secretarias a sus clínicas de forma aleatoria...")
        SecretariaClinica = SecretariaModel._meta.get_field(
            "secretaria_clinica"
        ).remote_field.through
        lista_relaciones_clinicas = []
        clinicas_disponibles = list(
            ComunaClinicaModel.objects.values_list("id", flat=True)
        )

        if not clinicas_disponibles:
            clinicas_disponibles = [1, 2, 3, 4, 5]

        for doc in secretarias_creados:
            cantidad_clinicas = random.randint(1, 2)
            clinicas_asignadas = random.sample(
                clinicas_disponibles, min(len(clinicas_disponibles), cantidad_clinicas)
            )
            for clinica_id in clinicas_asignadas:
                lista_relaciones_clinicas.append(
                    SecretariaClinica(
                        secretariamodel_id=doc.id,
                        comunaclinicamodel_id=clinica_id,
                    )
                )
        SecretariaClinica.objects.bulk_create(lista_relaciones_clinicas)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Secretaria-Clínica inyectadas correctamente."
            )
        )

    def insertar_usuario_paciente(self):
        try:
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método para insertar a Usuarios Pacientes.")
            )
            grupo_paciente = Group.objects.get(name="Paciente")
            generador_faker = Faker("es_CL")
            lista_usuarios_data = []
            lista_paciente_data = []
            lista_direccion_data = []
            password_hash = make_password("123")
            usernames_existentes = set(
                CustomersUsers.objects.values_list("username", flat=True)
            )

            for i in range(1, 6):
                sexo = random.choice(["M", "F"])
                if sexo == "M":
                    primer_nombre_paciente = generador_faker.first_name_male()
                    segundo_nombre_paciente = generador_faker.first_name_male()
                    ap_paterno_paciente = generador_faker.last_name()
                    ap_materno_paciente = generador_faker.last_name()
                    edad_paciente = generador_faker.random_int(min=0, max=95)
                    sexo_paciente = "M"
                    telefono_paciente = (
                        f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                    )
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    if username_paciente not in usernames_existentes:
                        lista_usuarios_data.append(data_user)
                        usernames_existentes.add(username_paciente)
                        data_paciente = {
                            "primer_nombre": primer_nombre_paciente,
                            "segundo_nombre": segundo_nombre_paciente,
                            "ap_paterno": ap_paterno_paciente,
                            "ap_materno": ap_materno_paciente,
                            "edad": edad_paciente,
                            "sexo": sexo_paciente,
                            "fono": telefono_paciente,
                            "paciente_uuid": str(uuid.uuid4()),
                        }
                        lista_paciente_data.append(data_paciente)
                else:
                    primer_nombre_paciente = generador_faker.first_name_female()
                    segundo_nombre_paciente = generador_faker.first_name_female()
                    ap_paterno_paciente = generador_faker.last_name()
                    ap_materno_paciente = generador_faker.last_name()
                    edad_paciente = generador_faker.random_int(min=0, max=100)
                    sexo_paciente = "F"
                    telefono_paciente = (
                        f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                    )
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    if username_paciente not in usernames_existentes:
                        lista_usuarios_data.append(data_user)
                        usernames_existentes.add(username_paciente)
                        data_paciente = {
                            "primer_nombre": primer_nombre_paciente,
                            "segundo_nombre": segundo_nombre_paciente,
                            "ap_paterno": ap_paterno_paciente,
                            "ap_materno": ap_materno_paciente,
                            "edad": edad_paciente,
                            "sexo": sexo_paciente,
                            "fono": telefono_paciente,
                            "paciente_uuid": str(uuid.uuid4()),
                        }
                        lista_paciente_data.append(data_paciente)

            instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
            usuarios_creados = CustomersUsers.objects.bulk_create(
                instancias_usuarios, batch_size=1000
            )
            self.stdout.write(
                self.style.SUCCESS("  ✅ 5 Usuarios Pacientes creados exitosamente.")
            )

            UserGroupThrough = CustomersUsers.groups.through
            relaciones_grupos = [
                UserGroupThrough(customersusers_id=user.id, group_id=grupo_paciente.id)
                for user in usuarios_creados
            ]
            UserGroupThrough.objects.bulk_create(relaciones_grupos)
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ 5 Usuarios asignados al Grupo 'Paciente' exitosamente."
                )
            )

            for idx, user in enumerate(usuarios_creados):
                lista_paciente_data[idx]["fk_user_id"] = user.id

            instancias_paciente = [PacienteModel(**reg) for reg in lista_paciente_data]
            paciente_creados = PacienteModel.objects.bulk_create(
                instancias_paciente, batch_size=1000
            )

            comunas_chile = [
                "Cerrillos",
                "Providencia",
                "Las Condes",
                "Maipú",
                "Santiago Centro",
                "Vitacura",
            ]
            try:
                for paciente in paciente_creados:
                    data_direccion = {
                        "region": "Metropolitana",
                        "comuna": random.choice(comunas_chile),
                        "vivienda": generador_faker.random_element(
                            elements=("Casa", "Departamento", "Condominio")
                        ),
                        "num_vivienda": str(
                            generador_faker.random_int(min=1, max=9999)
                        ),
                        "fk_paciente_id": paciente.id,
                    }
                    lista_direccion_data.append(data_direccion)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"⚠️ Error al armar direcciones: {e}")
                )

            instancias_direccion = [
                DireccionModel(**reg) for reg in lista_direccion_data
            ]
            direcciones_creadas = DireccionModel.objects.bulk_create(
                instancias_direccion, batch_size=1000
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✅ {len(direcciones_creadas)} Direcciones inyectadas correctamente."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    def insertar_reserva_paciente_registrado(self, horarios_ocupados=None):
        try:
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ Método Insertar las Reservas de Registrados Iniciando..."
                )
            )
            if horarios_ocupados is None:
                horarios_ocupados = set()
            listado_doctores = list(
                DoctorModel.objects.prefetch_related(
                    "doctor_clinica", "especialidades"
                ).all()
            )
            listado_pacientes_ids = list(
                CustomersUsers.objects.filter(pacientemodel__isnull=False).values_list(
                    "id", flat=True
                )
            )
            listado_clinicas = list(
                ComunaClinicaModel.objects.values_list(
                    "id", "nombre_clinica", "comuna_clinica", "direccion_clinica"
                )
            )
            especialidades = list(
                Especialidad.objects.values_list(
                    "id", "nombre_especialidad", "valor_especialidad"
                )
            )
            paciente_registrado = list(
                PacienteModel.objects.values_list("id", flat=True)
            )

            listas_reservas = []
            lista_debito = []
            lista_credito = []

            objetivo = 25

            while len(listas_reservas) < objetivo:
                ahora = timezone.now()

                dias_aleatorios = random.randint(-60, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_aleatorios)
                fecha_formateada = objeto_fecha_reserva.date()

                if fecha_formateada > ahora.date():
                    reserva_cerrada = 0
                else:
                    reserva_cerrada = random.choice([1, 0])

                tipo_pago = ""
                pago_realizado = 0

                if reserva_cerrada == 1:
                    tipo_pago = random.choice(["Crédito", "Débito"])
                    pago_realizado = 1

                if reserva_cerrada == 0:
                    tipo_pago = random.choice(["Crédito", "Débito", ""])
                    if tipo_pago == "":
                        pago_realizado = 0
                    if tipo_pago != "":
                        pago_realizado = 1

                dias_antes = random.randint(1, 20)
                fecha_creacion_dt = objeto_fecha_reserva - timedelta(days=dias_antes)
                if fecha_creacion_dt > ahora:
                    fecha_creacion_dt = ahora - timedelta(days=random.randint(0, 5))

                reser_anulada = random.choice([1, 0])
                reser_confirmada = 0 if reser_anulada == 1 else 1

                doctor = random.choice(listado_doctores)
                nombre_completo_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"

                clinicas_del_doctor = list(doctor.doctor_clinica.all())
                if not clinicas_del_doctor:
                    continue
                clinica_elegida = random.choice(clinicas_del_doctor)

                especialidades_del_doctor = list(doctor.especialidades.all())
                if not especialidades_del_doctor:
                    continue
                especialidad_elegida = random.choice(especialidades_del_doctor)

                hora_encontrada = False
                intentos_hora = 0

                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")

                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    if clave_reserva not in horarios_ocupados:
                        horarios_ocupados.add(clave_reserva)
                        objeto_hora_termino = objeto_hora_inicio + timedelta(hours=1)
                        hora_encontrada = True
                        break

                    intentos_hora += 1

                if not hora_encontrada:
                    continue

                datos_reservas = {
                    "fecha_creacion_reserva": fecha_creacion_dt,
                    "usuario_creacion_reserva": "Admin",
                    "fecha_reserva": fecha_formateada,
                    "hora_inicio": objeto_hora_inicio.strftime("%H:%M:%S"),
                    "hora_termino": objeto_hora_termino.strftime("%H:%M:%S"),
                    "especialidad": especialidad_elegida.nombre_especialidad,
                    "nombre_doctor": nombre_completo_doctor,
                    "nombre_clinica": clinica_elegida.nombre_clinica,
                    "comuna_clinica": clinica_elegida.comuna_clinica,
                    "direccion_clinica": clinica_elegida.direccion_clinica,
                    "tipo_pago": tipo_pago,
                    "reserva_uuid": str(uuid.uuid4()),
                    "reserva_cerrada": reserva_cerrada,
                    "pago_realizado": pago_realizado,
                    "reser_anulada": reser_anulada,
                    "reser_confirmada": reser_confirmada,
                    "fk_usuario_id": random.choice(listado_pacientes_ids),
                }

                listas_reservas.append(datos_reservas)

            if listas_reservas:
                instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
                reservas_creadas = ReservaModel.objects.bulk_create(
                    instancias_reserva, batch_size=1000
                )

                uuids_creados = [r["reserva_uuid"] for r in listas_reservas]
                reservas = list(
                    ReservaModel.objects.filter(
                        reserva_uuid__in=uuids_creados
                    ).values_list(
                        "id",
                        "tipo_pago",
                        "pago_realizado",
                        "especialidad",
                        "fecha_reserva",
                    )
                )

                dict_especialidades = {
                    e.nombre_especialidad: e for e in Especialidad.objects.all()
                }

                for (
                    id,
                    tipo_pago,
                    pago_realizado,
                    especialidad,
                    fecha_reserva,
                ) in reservas:
                    valor_especialidad = dict_especialidades.get(especialidad)
                    if not valor_especialidad:
                        continue

                    precio_int = int(valor_especialidad.valor_especialidad)
                    fecha_pago_dt = timezone.make_aware(
                        datetime.combine(fecha_reserva, datetime.min.time())
                    )

                    if pago_realizado == 1 and tipo_pago == "Crédito":
                        cant_cuotas = random.choice([3, 6, 9])
                        monto_cuotas = math.ceil(precio_int / cant_cuotas)
                        credito = {
                            "credito": 1,
                            "fecha_pago": fecha_pago_dt,
                            "credito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "cant_cuotas": cant_cuotas,
                            "monto_total": precio_int,
                            "monto_cuotas": monto_cuotas,
                            "fk_reserva_id": id,
                        }
                        lista_credito.append(credito)

                    if pago_realizado == 1 and tipo_pago == "Débito":
                        debito = {
                            "debito": 0,
                            "fecha_pago": fecha_pago_dt,
                            "debito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "monto_total": precio_int,
                            "fk_reserva_id": id,
                        }
                        lista_debito.append(debito)

                instancias_credito = [CreditoModel(**reg) for reg in lista_credito]
                CreditoModel.objects.bulk_create(instancias_credito, batch_size=1000)

                instancias_debito = [DebitoModel(**reg) for reg in lista_debito]
                DebitoModel.objects.bulk_create(instancias_debito, batch_size=1000)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ 25 Reservas pagadas con DÉBITO o CRÉDITO (Registrados) inyectadas."
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    def insertar_historial_paciente_registrado(self):
        reservas = list(
            ReservaModel.objects.values_list(
                "id",
                "reserva_cerrada",
                "reserva_uuid",
                "fk_usuario_id",
                "nombre_doctor",
                "fecha_reserva",
                "especialidad",
            )
        )

        medicos_con_especialidades = DoctorModel.objects.values_list(
            "primer_nombre",
            "segundo_nombre",
            "ap_paterno",
            "ap_materno",
            "especialidades__nombre_especialidad",
        )

        mapa_medico_especialidad = {}
        for (
            primer_nombre,
            segundo_nombre,
            ap_paterno,
            ap_materno,
            nombre_esp,
        ) in medicos_con_especialidades:
            p_nombre = primer_nombre if primer_nombre else ""
            s_nombre = segundo_nombre if segundo_nombre else ""
            ape_paterno = ap_paterno if ap_paterno else ""
            ape_materno = ap_materno if ap_materno else ""
            nombre_completo = (
                f"{p_nombre} {s_nombre} {ape_paterno} {ape_materno}".strip()
            )
            mapa_medico_especialidad[nombre_completo] = nombre_esp

        mapa_pacientes_raw = PacienteModel.objects.values_list("id", "fk_user_id")
        diccionario_pacientes = {
            fk_user: id_paciente for id_paciente, fk_user in mapa_pacientes_raw
        }
        historial_pac_registrado = []

        pacientes_especialidades = set()

        for (
            id,
            reserva_cerrada,
            reserva_uuid,
            fk_usuario_id,
            nombre_doctor,
            fecha_reserva,
            especialidad_reserva,
        ) in reservas:
            if reserva_cerrada == 0:
                continue

            id_paciente_real = diccionario_pacientes.get(fk_usuario_id)
            if id_paciente_real is None:
                continue

            medico_limpio = nombre_doctor.strip() if nombre_doctor else ""
            nombre_especialidad = mapa_medico_especialidad.get(
                medico_limpio, "Medicina General"
            )

            clave_historial = (id_paciente_real, nombre_especialidad)
            if clave_historial in pacientes_especialidades:
                continue

            datos_medicos = fake.historial_por_especialidad(nombre_especialidad)

            dato_historial = {
                "fecha_creacion_historial": fecha_reserva.strftime("%Y-%m-%d"),
                "diagnostico": datos_medicos["diagnostico"],
                "sintoma": datos_medicos["sintoma"],
                "observacion": datos_medicos["observacion"],
                "reserva_uuid": reserva_uuid,
                "fk_paciente_id": id_paciente_real,
            }
            historial_pac_registrado.append(dato_historial)

            pacientes_especialidades.add(clave_historial)

        if not historial_pac_registrado:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No se encontraron historiales aptos para insertar."
                )
            )
            return

        instancias_historial = [
            HistorialClinicoModel(**reg) for reg in historial_pac_registrado
        ]
        # 👈 ignore_conflicts=True para evitar crash si el modelo aún tiene unique constraint
        HistorialClinicoModel.objects.bulk_create(
            instancias_historial, batch_size=1000, ignore_conflicts=True
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES REGISTRADOS inyectados con coherencia total."
            )
        )

    def insertar_paciente_no_registrado(self):
        self.stdout.write(
            self.style.SUCCESS("  ✅ Método para insertar a Pacientes NO REGISTRADOS.")
        )
        generador_faker = Faker("es_CL")
        lista_paciente_data = []

        for i in range(1, 6):
            sexo = random.choice(["M", "F"])
            edad = fake.random_int(min=25, max=95)
            if sexo == "M":
                primer_nombre_paciente = generador_faker.first_name_male()
                segundo_nombre_paciente = generador_faker.first_name_male()
                ap_paterno_paciente = generador_faker.last_name()
                ap_materno_paciente = generador_faker.last_name()
                edad_paciente = edad
                sexo_paciente = "M"
                telefono_paciente = (
                    f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                )
                primer_nombre_corto = primer_nombre_paciente[:3].lower()
                ap_paterno_corto = ap_paterno_paciente[:3].lower()
                username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                email = f"{username_paciente}@gmail.com"

                data_paciente_no_registrado = {
                    "primer_nombre": primer_nombre_paciente,
                    "segundo_nombre": segundo_nombre_paciente,
                    "ap_paterno": ap_paterno_paciente,
                    "ap_materno": ap_materno_paciente,
                    "edad": edad_paciente,
                    "sexo": sexo_paciente,
                    "fono": telefono_paciente,
                    "email": email,
                    "paciente_uuid": str(uuid.uuid4()),
                }
                lista_paciente_data.append(data_paciente_no_registrado)
            else:
                primer_nombre_paciente = generador_faker.first_name_female()
                segundo_nombre_paciente = generador_faker.first_name_female()
                ap_paterno_paciente = generador_faker.last_name()
                ap_materno_paciente = generador_faker.last_name()
                edad_paciente = edad
                sexo_paciente = "F"
                telefono_paciente = (
                    f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                )
                primer_nombre_corto = primer_nombre_paciente[:3].lower()
                ap_paterno_corto = ap_paterno_paciente[:3].lower()
                username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                email = f"{username_paciente}@gmail.com"

                data_paciente_no_registrado = {
                    "primer_nombre": primer_nombre_paciente,
                    "segundo_nombre": segundo_nombre_paciente,
                    "ap_paterno": ap_paterno_paciente,
                    "ap_materno": ap_materno_paciente,
                    "edad": edad_paciente,
                    "sexo": sexo_paciente,
                    "fono": telefono_paciente,
                    "email": email,
                    "paciente_uuid": str(uuid.uuid4()),
                }
                lista_paciente_data.append(data_paciente_no_registrado)

        instancias_paciente = [
            PacienteNoRegisterModel(**reg) for reg in lista_paciente_data
        ]
        PacienteNoRegisterModel.objects.bulk_create(
            instancias_paciente, batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 5 PACIENTES NO REGISTRADOS INSERTADOS CORRECTAMENTE"
            )
        )

    def insertar_reserva_paciente_no_registrado(self, horarios_ocupados=None):
        try:
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ Método Insertar las Reservas de NO Registrados Iniciando..."
                )
            )
            if horarios_ocupados is None:
                horarios_ocupados = set()
            listado_doctores = list(
                DoctorModel.objects.prefetch_related(
                    "doctor_clinica", "especialidades"
                ).all()
            )
            listado_clinicas = list(
                ComunaClinicaModel.objects.values_list(
                    "id", "nombre_clinica", "comuna_clinica", "direccion_clinica"
                )
            )
            especialidades = list(
                Especialidad.objects.values_list(
                    "id", "nombre_especialidad", "valor_especialidad"
                )
            )
            paciente_registrado = list(
                PacienteNoRegisterModel.objects.values_list("id", flat=True)
            )
            listas_reservas = []
            lista_debito = []
            lista_credito = []

            objetivo = 25

            while len(listas_reservas) < objetivo:
                ahora = timezone.now()

                dias_aleatorios = random.randint(-60, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_aleatorios)
                fecha_formateada = objeto_fecha_reserva.date()

                if fecha_formateada > ahora.date():
                    reserva_cerrada = 0
                else:
                    reserva_cerrada = random.choice([1, 0])

                tipo_pago = ""
                pago_realizado = 0

                if reserva_cerrada == 1:
                    tipo_pago = random.choice(["Crédito", "Débito"])
                    pago_realizado = 1

                if reserva_cerrada == 0:
                    tipo_pago = random.choice(["Crédito", "Débito", ""])
                    if tipo_pago == "":
                        pago_realizado = 0
                    if tipo_pago != "":
                        pago_realizado = 1

                dias_antes = random.randint(1, 20)
                fecha_creacion_dt = objeto_fecha_reserva - timedelta(days=dias_antes)
                if fecha_creacion_dt > ahora:
                    fecha_creacion_dt = ahora - timedelta(days=random.randint(0, 5))

                reser_anulada = random.choice([1, 0])
                reser_confirmada = 0 if reser_anulada == 1 else 1

                doctor = random.choice(listado_doctores)
                nombre_completo_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"

                clinicas_del_doctor = list(doctor.doctor_clinica.all())
                if not clinicas_del_doctor:
                    continue
                clinica_elegida = random.choice(clinicas_del_doctor)

                especialidades_del_doctor = list(doctor.especialidades.all())
                if not especialidades_del_doctor:
                    continue
                especialidad_elegida = random.choice(especialidades_del_doctor)

                hora_encontrada = False
                intentos_hora = 0

                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")
                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    if clave_reserva not in horarios_ocupados:
                        horarios_ocupados.add(clave_reserva)
                        objeto_hora_termino = objeto_hora_inicio + timedelta(hours=1)
                        hora_encontrada = True
                        break

                    intentos_hora += 1

                if not hora_encontrada:
                    continue

                datos_reservas = {
                    "fecha_creacion_reserva": fecha_creacion_dt,
                    "usuario_creacion_reserva": "Admin",
                    "fecha_reserva": fecha_formateada,
                    "hora_inicio": objeto_hora_inicio.strftime("%H:%M:%S"),
                    "hora_termino": objeto_hora_termino.strftime("%H:%M:%S"),
                    "especialidad": especialidad_elegida.nombre_especialidad,
                    "nombre_doctor": nombre_completo_doctor,
                    "nombre_clinica": clinica_elegida.nombre_clinica,
                    "comuna_clinica": clinica_elegida.comuna_clinica,
                    "direccion_clinica": clinica_elegida.direccion_clinica,
                    "tipo_pago": tipo_pago,
                    "reserva_uuid": str(uuid.uuid4()),
                    "reserva_cerrada": reserva_cerrada,
                    "pago_realizado": pago_realizado,
                    "reser_anulada": reser_anulada,
                    "reser_confirmada": reser_confirmada,
                    "fk_pac_no_register_id": random.choice(paciente_registrado),
                    "fk_usuario_id": None,
                }
                listas_reservas.append(datos_reservas)

            if listas_reservas:
                instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
                reservas_creadas = ReservaModel.objects.bulk_create(
                    instancias_reserva, batch_size=1000
                )

                uuids_creados = [r["reserva_uuid"] for r in listas_reservas]
                reservas = list(
                    ReservaModel.objects.filter(
                        reserva_uuid__in=uuids_creados
                    ).values_list(
                        "id",
                        "tipo_pago",
                        "pago_realizado",
                        "especialidad",
                        "fecha_reserva",
                    )
                )
                dict_especialidades = {
                    e.nombre_especialidad: e for e in Especialidad.objects.all()
                }

                for (
                    id,
                    tipo_pago,
                    pago_realizado,
                    especialidad,
                    fecha_reserva,
                ) in reservas:
                    valor_especialidad = dict_especialidades.get(especialidad)
                    if not valor_especialidad:
                        continue
                    precio_int = int(valor_especialidad.valor_especialidad)

                    fecha_pago_dt = timezone.make_aware(
                        datetime.combine(fecha_reserva, datetime.min.time())
                    )

                    if pago_realizado == 1 and tipo_pago == "Crédito":
                        cant_cuotas = random.choice([3, 6, 9])
                        monto_cuotas = math.ceil(precio_int / cant_cuotas)
                        credito = {
                            "credito": 1,
                            "fecha_pago": fecha_pago_dt,
                            "credito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "cant_cuotas": cant_cuotas,
                            "monto_total": precio_int,
                            "monto_cuotas": monto_cuotas,
                            "fk_reserva_id": id,
                        }
                        lista_credito.append(credito)

                    if pago_realizado == 1 and tipo_pago == "Débito":
                        debito = {
                            "debito": 0,
                            "fecha_pago": fecha_pago_dt,
                            "debito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "monto_total": precio_int,
                            "fk_reserva_id": id,
                        }
                        lista_debito.append(debito)

                instancias_credito = [CreditoModel(**reg) for reg in lista_credito]
                CreditoModel.objects.bulk_create(instancias_credito, batch_size=1000)

                instancias_debito = [DebitoModel(**reg) for reg in lista_debito]
                DebitoModel.objects.bulk_create(instancias_debito, batch_size=1000)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ 25 Reservas pagadas con DÉBITO o CRÉDITO (NO Registrados) inyectadas."
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    def insertar_historial_paciente_no_registrado(self):
        reservas = list(
            ReservaModel.objects.values_list(
                "id",
                "reserva_cerrada",
                "reserva_uuid",
                "fk_pac_no_register_id",
                "nombre_doctor",
                "fecha_reserva",
                "especialidad",
            )
        )

        medicos_con_especialidades = DoctorModel.objects.values_list(
            "primer_nombre",
            "segundo_nombre",
            "ap_paterno",
            "ap_materno",
            "especialidades__nombre_especialidad",
        )

        mapa_medico_especialidad = {}
        for (
            primer_nombre,
            segundo_nombre,
            ap_paterno,
            ap_materno,
            nombre_esp,
        ) in medicos_con_especialidades:
            p_nombre = primer_nombre if primer_nombre else ""
            s_nombre = segundo_nombre if segundo_nombre else ""
            ape_paterno = ap_paterno if ap_paterno else ""
            ape_materno = ap_materno if ap_materno else ""
            nombre_completo = (
                f"{p_nombre} {s_nombre} {ape_paterno} {ape_materno}".strip()
            )
            mapa_medico_especialidad[nombre_completo] = nombre_esp

        mapa_pacientes_raw = PacienteNoRegisterModel.objects.values_list(
            "id", flat=True
        )
        diccionario_pacientes = {
            id_paciente: id_paciente for id_paciente in mapa_pacientes_raw
        }
        historial_pac_no_registrado = []

        pacientes_especialidades = set()

        for (
            id,
            reserva_cerrada,
            reserva_uuid,
            fk_pac_no_register_id,
            nombre_doctor,
            fecha_reserva,
            especialidad_reserva,
        ) in reservas:
            if reserva_cerrada == 0:
                continue

            id_paciente_real = diccionario_pacientes.get(fk_pac_no_register_id)
            if id_paciente_real is None:
                continue

            medico_limpio = nombre_doctor.strip() if nombre_doctor else ""
            nombre_especialidad = mapa_medico_especialidad.get(
                medico_limpio, "Medicina General"
            )

            clave_historial = (id_paciente_real, nombre_especialidad)
            if clave_historial in pacientes_especialidades:
                continue

            datos_medicos = fake.historial_por_especialidad(nombre_especialidad)

            dato_historial = {
                "fecha_historial": fecha_reserva.strftime("%Y-%m-%d"),
                "diagnostico": datos_medicos["diagnostico"],
                "sintoma": datos_medicos["sintoma"],
                "observacion": datos_medicos["observacion"],
                "reserva_uuid": reserva_uuid,
                "fk_pac_no_registrado_id": id_paciente_real,
            }
            historial_pac_no_registrado.append(dato_historial)

            pacientes_especialidades.add(clave_historial)

        if not historial_pac_no_registrado:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No se encontraron historiales aptos para insertar."
                )
            )
            return

        df_historial = pd.DataFrame(historial_pac_no_registrado)
        instancias_historial = [
            HistorialPacNoRegistradoModel(**reg)
            for reg in df_historial.to_dict("records")
        ]
        # 👈 ignore_conflicts=True para evitar crash si el modelo aún tiene unique constraint
        HistorialPacNoRegistradoModel.objects.bulk_create(
            instancias_historial, batch_size=1000, ignore_conflicts=True
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES NO REGISTRADOS inyectados con coherencia total."
            )
        )
