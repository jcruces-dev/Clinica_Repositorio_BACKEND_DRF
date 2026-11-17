from django.core.management.base import BaseCommand

# Hasheador oficial y seguro de Django
from django.contrib.auth.hashers import make_password

# Para manejar las fechas de las reservas según la zona horaria chilena.
from django.utils import timezone
import uuid
import hashlib
import random
from datetime import datetime, timedelta

# Importamos environ para leer el archivo .env
import environ
import os

# Librerías instaladas en tu entorno
import pandas as pd
from faker import Faker

# Modelos necesarios.
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

# Este es un PROVIDERS, para crear el diagnostico, síntoma y observación con una lista COHERENTE que tenemos
# en el archivo que se encuentra en la carpeta, utils->providers.py, con esto creamos los datos coherentes con Faker.
from utils.providers import fake

# Esto nos permite redondear siempre hacia arriba y no hacia abajo. (Cuotas).
import math

# Esto se utiliza para creación de GRUPOS con la tabla que provee DRF.
from django.contrib.auth.models import Group

# Buena práctica, se debe inicializar afuera de la clase.
# Inicializamos environ
env = environ.Env()


# Esta clase debe existir para que encuentre el archivo cuando coloque el comando.
class Command(BaseCommand):
    help = "Script de Carga Masiva (Pandas + Faker + bulk_create) para poblar el sistema BuenPaciente"

    def handle(self, *args, **kwargs):
        # Imprime un mensaje de advertencia (amarillo) en la consola indicando que el proceso inicia.
        self.stdout.write(
            self.style.WARNING(
                "⚡ Iniciando el proceso de sembrado de datos (Seeding)..."
            )
        )

        # -----------------------------------------------------------------
        # Borramos primero lo que depende de otras tablas (Hijos) para evitar errores de FK
        # -----------------------------------------------------------------
        DireccionModel.objects.all().delete()  # Borra todas las direcciones.
        DoctorModel.objects.all().delete()  # Borra todos los perfiles de doctor.
        SecretariaModel.objects.all().delete()  # Borra todos los perfiles de secretaria.
        PacienteModel.objects.all().delete()  # Borra todos los perfiles de paciente.
        HistorialClinicoModel.objects.all().delete()  # Borra historiales de registrados.
        PacienteNoRegisterModel.objects.all().delete()  # Borra pacientes no registrados.
        HistorialPacNoRegistradoModel.objects.all().delete()  # Borra historiales de no registrados.
        ReservaModel.objects.all().delete()  # Borra todas las reservas.
        CreditoModel.objects.all().delete()  # Borra todos los pagos a crédito.
        DebitoModel.objects.all().delete()  # Borra todos los pagos a débito.

        # Borramos las tablas maestras independientes
        Especialidad.objects.all().delete()  # Borra todas las especialidades.
        ComunaClinicaModel.objects.all().delete()  # Borra todas las clínicas.

        # Barremos los usuarios base y grupos (Padres globales), pero preservando superusuarios (como plask).
        CustomersUsers.objects.filter(
            is_superuser=False
        ).delete()  # Borra usuarios que no sean superuser.
        Group.objects.all().delete()  # Borra todos los grupos de permisos.

        # Imprime un mensaje de éxito (verde) indicando que la base está limpia.
        self.stdout.write(
            self.style.SUCCESS("  🗑️ Base de datos limpia y lista para la siembra.")
        )

        # -----------------------------------------------------------------
        # Llamada a los métodos en el orden correcto de ejecución.
        # -----------------------------------------------------------------
        self.insertar_grupos()  # Crea los grupos Paciente, Doctor, Secretaria.
        self.insertar_clinicas()  # Crea las 5 clínicas.
        self.insertar_especialidad()  # Crea las 12 especialidades.
        self.insertar_usuario_doctor()  # Crea 40 doctores.
        self.insertar_usuario_secretaria()  # Crea 10 secretarias.
        self.insertar_usuario_paciente()  # Crea 3500 pacientes registrados.

        # =========================================================================
        # CONTROL DE AGENDAS GLOBAL UNIFICADO (AQUÍ ESTÁ LA MAGIA PARA NO DUPLICAR HORAS)
        # =========================================================================
        # Se crea un set vacío aquí en el método padre que se pasará a ambos métodos de reserva.
        # Esto garantiza que las reservas de registrados y no registrados compartan la misma memoria.
        horarios_globales = set()

        # Genera 2000 reservas para pacientes registrados pasando el set global.
        self.insertar_reserva_paciente_registrado(horarios_ocupados=horarios_globales)
        # Genera historiales para las reservas cerradas de registrados.
        self.insertar_historial_paciente_registrado()

        # Crea 2500 pacientes no registrados (sin cuenta de usuario).
        self.insertar_paciente_no_registrado()

        # Genera 2000 reservas para pacientes no registrados, leyendo el mismo set global.
        self.insertar_reserva_paciente_no_registrado(
            horarios_ocupados=horarios_globales
        )

        # Descomenta esta línea si quieres generar historiales para no registrados también.
        # self.insertar_historial_paciente_no_registrado()

        # Imprime el mensaje final de éxito.
        self.stdout.write(self.style.SUCCESS("¡Proceso finalizado con éxito!"))

    # Método para insertar los grupos en DRF.
    def insertar_grupos(self):
        # Imprime un mensaje indicando el inicio del proceso.
        self.stdout.write("Procesando grupos de permisos con Pandas...")

        # Limpiamos la tabla para evitar duplicados de GRUPO.
        Group.objects.all().delete()

        # Creamos un DataFrame de Pandas con los 3 roles.
        df_grupos = pd.DataFrame({"name": ["Paciente", "Doctor", "Secretaria"]})

        # Convertimos el DataFrame a una lista de diccionarios.
        registros = df_grupos.to_dict("records")

        # Instanciamos cada diccionario en un objeto Group de Django.
        objetos_grupos = [Group(**reg) for reg in registros]

        # Guardamos todos los grupos en la base de datos en una sola consulta.
        Group.objects.bulk_create(objetos_grupos)

        # Imprime mensaje de éxito.
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 3 Grupos (Paciente, Doctor, Secretaria) creados correctamente."
            )
        )

    # Método para insertar las Clínicas.
    def insertar_clinicas(self):
        # 1. Creamos un diccionario con los datos de las clínicas.
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
        # Inicializamos una lista vacía.
        lista = []
        # Iteramos sobre la cantidad de clínicas (5).
        for i in range(len(datos_clinica["nombre_clinica"])):
            # Creamos un diccionario por cada clínica.
            registro = {
                "nombre_clinica": datos_clinica["nombre_clinica"][i],
                "comuna_clinica": datos_clinica["comuna_clinica"][i],
                "direccion_clinica": datos_clinica["direccion_clinica"][i],
            }
            # Lo agregamos a la lista.
            lista.append(registro)
        # Convertimos los diccionarios en instancias del modelo.
        objetos_clinica = [ComunaClinicaModel(**reg) for reg in lista]
        # Inserción masiva en la BD.
        ComunaClinicaModel.objects.bulk_create(objetos_clinica)
        # Mensaje de éxito.
        self.stdout.write(
            self.style.SUCCESS("  ✅ 5 Clínicas insertadas correctamente.")
        )

    # Método para insertar las Especialidades.
    def insertar_especialidad(self):
        # Diccionario con las especialidades y sus precios.
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

        # Convertimos a DataFrame.
        df_especialidad = pd.DataFrame(datos_especialidad)
        # Convertimos a diccionarios.
        registro_especialidad = df_especialidad.to_dict("records")
        # Instanciamos el modelo.
        objetos_especialidad = [Especialidad(**reg) for reg in registro_especialidad]
        # Guardamos en bloque.
        Especialidad.objects.bulk_create(objetos_especialidad)
        # Mensaje de éxito.
        self.stdout.write(
            self.style.SUCCESS("  ✅ Especialidades insertadas correctamente.")
        )

    # Método para insertar usuarios Doctores.
    def insertar_usuario_doctor(self):
        # Buscamos el grupo "Doctor" creado previamente.
        grupo_doctor = Group.objects.get(name="Doctor")
        # Instanciamos Faker.
        fake = Faker("es_CL")
        # Inicializamos listas.
        lista_usuarios_data = []
        lista_doctores_data = []
        # Hasheamos la contraseña "123" una sola vez para ahorrar tiempo.
        password_hash = make_password("123")

        # Creamos 40 doctores.
        for i in range(1, 41):
            # Elegimos sexo al azar.
            sexo = random.choice(["M", "F"])
            # Generamos edad al azar.
            edad_doctor = fake.random_int(min=25, max=60)

            # Si es hombre...
            if sexo == "M":
                # Generamos nombres.
                primer_nombre_doctor = fake.first_name_male()
                segundo_nombre_doctor = fake.first_name_male()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                # Generamos teléfono.
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "M"
                # Generamos un username único basado en el nombre.
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                # Generamos un email.
                email = f"{username_doctor}@gmail.com"
                # Preparamos los datos del usuario.
                data_user = {
                    "username": username_doctor,
                    "password": password_hash,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                # Si el usuario no existe, lo agregamos.
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    lista_usuarios_data.append(data_user)
                    # Preparamos los datos del perfil de doctor.
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
            # Si es mujer...
            else:
                # Generamos nombres.
                primer_nombre_doctor = fake.first_name_female()
                segundo_nombre_doctor = fake.first_name_female()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                # Generamos teléfono.
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "F"
                # Generamos un username único.
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                # Generamos email.
                email = f"{username_doctor}@gmail.com"
                # Preparamos datos de usuario.
                data_user = {
                    "username": username_doctor,
                    "password": password_hash,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                # Si no existe, lo agregamos.
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    lista_usuarios_data.append(data_user)
                    # Preparamos datos de doctor.
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

        # Guardamos todos los usuarios en la BD y obtenemos sus IDs.
        instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(self.style.SUCCESS("  ✅ 40 Usuarios base creados."))

        # Asignamos a todos los usuarios al grupo "Doctor".
        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_doctor.id)
            for user in usuarios_creados
        ]
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Usuarios asignados al Grupo 'Doctor' exitosamente."
            )
        )

        # Enlazamos el ID del usuario recién creado con el perfil de doctor.
        for idx, user in enumerate(usuarios_creados):
            lista_doctores_data[idx]["fk_user_id"] = user.id

        # Guardamos los perfiles de doctores en la BD.
        instancias_doctores = [DoctorModel(**reg) for reg in lista_doctores_data]
        doctores_creados = DoctorModel.objects.bulk_create(instancias_doctores)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Perfiles de Doctores creados en la base de datos."
            )
        )

        # =========================================================================
        # RELACIÓN DOCTOR <-> CLÍNICA
        # =========================================================================
        self.stdout.write("Asociando doctores a sus clínicas de forma aleatoria...")
        DoctorClinica = DoctorModel._meta.get_field(
            "doctor_clinica"
        ).remote_field.through
        lista_relaciones_clinicas = []
        clinicas_disponibles = list(
            ComunaClinicaModel.objects.values_list("id", flat=True)
        )

        # Si no hay clínicas, asignamos IDs por defecto para evitar errores.
        if not clinicas_disponibles:
            clinicas_disponibles = [1, 2, 3, 4, 5]

        # Asignamos a cada doctor 1 o 2 clínicas al azar.
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
        # Guardamos las relaciones en la tabla intermedia.
        DoctorClinica.objects.bulk_create(lista_relaciones_clinicas)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Clínica inyectadas correctamente."
            )
        )

        # =========================================================================
        # RELACIÓN DOCTOR <-> ESPECIALIDAD
        # =========================================================================
        lista_relaciones_especialidades = []
        DoctorEspecialidad = DoctorModel._meta.get_field(
            "especialidades"
        ).remote_field.through
        listado_especialidades = list(Especialidad.objects.values_list("id", flat=True))

        # Validación de seguridad.
        if not listado_especialidades:
            self.stdout.write(
                self.style.ERROR(
                    "❌ No se encontraron especialidades creadas en la base de datos."
                )
            )
            return

        # Asignamos a cada doctor 1 o 2 especialidades al azar.
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
        # Guardamos las relaciones.
        DoctorEspecialidad.objects.bulk_create(lista_relaciones_especialidades)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Especialidad inyectadas correctamente."
            )
        )

    # Método para insertar usuarios Secretarias.
    def insertar_usuario_secretaria(self):
        # Buscamos el grupo "Secretaria".
        grupo_secretaria = Group.objects.get(name="Secretaria")
        fake = Faker("es_CL")
        lista_usuarios_data = []
        lista_secretaria_data = []

        # Creamos 10 secretarias.
        for i in range(1, 11):
            # Generamos sus datos personales.
            primer_nombre_doctor = fake.first_name()
            segundo_nombre_doctor = fake.first_name()
            ap_paterno_doctor = fake.last_name()
            ap_materno_doctor = fake.last_name()
            edad_secretaria = fake.random_int(min=25, max=60)
            sexo_secretaria = fake.random_element(elements=("M", "F"))
            telefono_secretaria = f"+56 9{fake.random_int(min=10000000, max=99999999)}"

            # Generamos username.
            primer_nombre_corto = primer_nombre_doctor[:3].lower()
            ap_paterno_corto = ap_paterno_doctor[:3].lower()
            username_secretaria = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
            email = f"{username_secretaria}@gmail.com"
            # Hasheamos la password.
            password = make_password("123")

            # Preparamos usuario.
            data_user = {
                "username": username_secretaria,
                "password": password,
                "email": email,
                "usuario_uuid": str(uuid.uuid4()),
            }
            if not CustomersUsers.objects.filter(username=username_secretaria).exists():
                lista_usuarios_data.append(data_user)

            # Preparamos perfil de secretaria.
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

        # Guardamos usuarios.
        df_usuarios = pd.DataFrame(lista_usuarios_data)
        instancias_usuarios = [
            CustomersUsers(**reg) for reg in df_usuarios.to_dict("records")
        ]
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(self.style.SUCCESS("  ✅ 10 Usuarios base creados."))

        # Asignamos al grupo "Secretaria".
        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_secretaria.id)
            for user in usuarios_creados
        ]
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 10 Usuarios asignados al Grupo 'Secretaria' exitosamente."
            )
        )

        # Enlazamos ID de usuario con perfil.
        for idx, user in enumerate(usuarios_creados):
            lista_secretaria_data[idx]["fk_user_id"] = user.id

        # Guardamos perfiles.
        df_secretaria = pd.DataFrame(lista_secretaria_data)
        instancias_secretaria = [
            SecretariaModel(**reg) for reg in df_secretaria.to_dict("records")
        ]
        secretarias_creados = SecretariaModel.objects.bulk_create(instancias_secretaria)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 10 Perfiles de Secretarias creados en la base de datos."
            )
        )

        # =========================================================================
        # RELACIÓN SECRETARIA <-> CLÍNICA
        # =========================================================================
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

        # Asignamos 1 o 2 clínicas.
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

    # Método para insertar Pacientes Registrados.
    def insertar_usuario_paciente(self):
        try:
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método para insertar a Usuarios Pacientes.")
            )

            # Buscamos el grupo Paciente.
            grupo_paciente = Group.objects.get(name="Paciente")
            generador_faker = Faker("es_CL")

            # Inicializamos listas.
            lista_usuarios_data = []
            lista_paciente_data = []
            lista_direccion_data = []
            # Hasheamos password una sola vez.
            password_hash = make_password("123")

            # Set para evitar duplicados.
            usernames_existentes = set(
                CustomersUsers.objects.values_list("username", flat=True)
            )

            # Creamos 3500 pacientes.
            for i in range(1, 3501):
                sexo = random.choice(["M", "F"])
                if sexo == "M":
                    # Datos hombre.
                    primer_nombre_paciente = generador_faker.first_name_male()
                    segundo_nombre_paciente = generador_faker.first_name_male()
                    ap_paterno_paciente = generador_faker.last_name()
                    ap_materno_paciente = generador_faker.last_name()
                    edad_paciente = generador_faker.random_int(min=0, max=95)
                    sexo_paciente = "M"
                    telefono_paciente = (
                        f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                    )
                    # Datos de login.
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"

                    # Preparamos usuario.
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    # Si no existe, preparamos el perfil.
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
                    # Datos mujer.
                    primer_nombre_paciente = generador_faker.first_name_female()
                    segundo_nombre_paciente = generador_faker.first_name_female()
                    ap_paterno_paciente = generador_faker.last_name()
                    ap_materno_paciente = generador_faker.last_name()
                    edad_paciente = generador_faker.random_int(min=0, max=100)
                    sexo_paciente = "F"
                    telefono_paciente = (
                        f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                    )
                    # Datos de login.
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"

                    # Preparamos usuario.
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    # Si no existe, preparamos perfil.
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

            # Guardamos usuarios.
            instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
            usuarios_creados = CustomersUsers.objects.bulk_create(
                instancias_usuarios, batch_size=1000
            )
            self.stdout.write(
                self.style.SUCCESS("  ✅ Usuarios Pacientes creados exitosamente.")
            )

            # Asignamos al grupo Paciente.
            UserGroupThrough = CustomersUsers.groups.through
            relaciones_grupos = [
                UserGroupThrough(customersusers_id=user.id, group_id=grupo_paciente.id)
                for user in usuarios_creados
            ]
            UserGroupThrough.objects.bulk_create(relaciones_grupos)
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ Usuarios asignados al Grupo 'Paciente' exitosamente."
                )
            )

            # Enlazamos ID de usuario con perfil de paciente.
            for idx, user in enumerate(usuarios_creados):
                lista_paciente_data[idx]["fk_user_id"] = user.id

            # Guardamos perfiles.
            instancias_paciente = [PacienteModel(**reg) for reg in lista_paciente_data]
            paciente_creados = PacienteModel.objects.bulk_create(
                instancias_paciente, batch_size=1000
            )

            # Lista de comunas de Chile.
            comunas_chile = [
                "Cerrillos",
                "Cerro Navia",
                "Colina",
                "Conchalí",
                "El Bosque",
                "Estación Central",
                "Huechuraba",
                "Independencia",
                "La Cisterna",
                "La Florida",
                "La Granja",
                "La Pintana",
                "La Reina",
                "Las Condes",
                "Lo Barnechea",
                "Lo Espejo",
                "Lo Prado",
                "Macul",
                "Maipú",
                "Ñuñoa",
                "Pedro Aguirre Cerda",
                "Peñaflor",
                "Peñalolén",
                "Providencia",
                "Puente Alto",
                "Pudahuel",
                "Quilicura",
                "Quinta Normal",
                "Recoleta",
                "Renca",
                "San Bernardo",
                "San Joaquín",
                "San Miguel",
                "San Ramón",
                "Santiago Centro",
                "Vitacura",
            ]

            # Generamos direcciones para cada paciente.
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
                    self.style.ERROR(
                        f"⚠️ Error inesperado en Python al armar direcciones: {e}"
                    )
                )

            # Guardamos direcciones.
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
            self.stdout.write(
                self.style.SUCCESS(
                    "  ✅ Proceso de inyección de pacientes finalizado con éxito."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    # Método para insertar reservas de pacientes REGISTRADOS.
    def insertar_reserva_paciente_registrado(self, horarios_ocupados=None):
        try:
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método Insertar las Reservas Iniciando.......")
            )

            # Si no se pasó un set desde el padre, creamos uno (por seguridad).
            if horarios_ocupados is None:
                horarios_ocupados = set()

            # Obtenemos datos en memoria.
            listado_doctores = list(
                DoctorModel.objects.prefetch_related(
                    "doctor_clinica", "especialidades"
                ).all()
            )
            listado_pacientes_ids = list(
                CustomersUsers.objects.filter(pacientemodel__isnull=False)
            )

            # Inicializamos listas para insertar en bloque.
            listas_reservas = []
            lista_debito = []
            lista_credito = []

            # 🚨 AQUÍ ESTABA EL ERROR: Se eliminó 'horarios_ocupados = set()'
            # Ahora usa el set que viene desde el handle().

            # Definimos la cantidad de reservas a generar (2000 como pediste).
            objetivo = 2000

            # Iteramos hasta generar 2000 reservas.
            while len(listas_reservas) < objetivo:
                # Obtenemos la hora actual con zona horaria.
                ahora = timezone.now()

                # Fechas aleatorias.
                dias_aleatorios = random.randint(-60, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_aleatorios)
                fecha_formateada = objeto_fecha_reserva.date()

                # Validaciones de pago.
                tipo_pago = ""
                pago_realizado = 0
                reserva_cerrada = random.choice([1, 0])

                if reserva_cerrada == 1:
                    tipo_pago = random.choice(["Crédito", "Débito"])
                    pago_realizado = 1

                if reserva_cerrada == 0:
                    tipo_pago = random.choice(["Crédito", "Débito", ""])
                    if tipo_pago == "":
                        pago_realizado = 0
                    if tipo_pago != "":
                        pago_realizado = 1

                # Fecha de creación de la reserva (coherente, no en el futuro).
                dias_antes = random.randint(1, 20)
                fecha_creacion_dt = objeto_fecha_reserva - timedelta(days=dias_antes)
                if fecha_creacion_dt > ahora:
                    fecha_creacion_dt = ahora - timedelta(days=random.randint(0, 5))

                reser_anulada = random.choice([1, 0])
                reser_confirmada = 0 if reser_anulada == 1 else 1

                # Elegimos doctor y sus datos.
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

                # ================================================================
                # BUSCADOR DE HORARIOS DISPONIBLES
                # ================================================================
                hora_encontrada = False
                intentos_hora = 0

                # Intentamos hasta 15 veces buscar una hora libre.
                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)  # Horas de 8 a 22.
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")

                    # Clave única: Doctor + Fecha + Hora.
                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    # Si NO está en el set global de horarios, está libre.
                    if clave_reserva not in horarios_ocupados:
                        horarios_ocupados.add(clave_reserva)  # Ocupamos la hora.
                        objeto_hora_termino = objeto_hora_inicio + timedelta(
                            hours=1
                        )  # Termina 1 hora después.
                        hora_encontrada = True
                        break  # Salimos del while interno.

                    intentos_hora += 1

                # Si no encontramos hora, pasamos a la siguiente iteración (otro doctor/fecha).
                if not hora_encontrada:
                    continue
                # ================================================================

                # Preparamos los datos de la reserva.
                datos_reservas = {
                    "fecha_creacion_reserva": fecha_creacion_dt,  # Datetime aware.
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
                    "fk_usuario_id": random.choice(
                        listado_pacientes_ids
                    ).id,  # FIX: Usamos fk_usuario_id.
                }

                listas_reservas.append(datos_reservas)

            # INSERT MASIVO DE RESERVAS.
            if listas_reservas:
                instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
                ReservaModel.objects.bulk_create(instancias_reserva, batch_size=1000)

                # Obtener los IDs recién generados para crear los pagos.
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

                # Generamos pagos (Crédito o Débito).
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
                    # Fecha de pago aware.
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

                # Insertamos los pagos.
                instancias_credito = [CreditoModel(**reg) for reg in lista_credito]
                CreditoModel.objects.bulk_create(instancias_credito, batch_size=1000)

                instancias_debito = [DebitoModel(**reg) for reg in lista_debito]
                DebitoModel.objects.bulk_create(instancias_debito, batch_size=1000)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ 2000 Reservas pagadas con DÉBITO o CRÉDITO inyectadas con éxito."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  ⚠️ No se generaron reservas válidas para insertar."
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    # Método para insertar el historial a Pacientes REGISTRADOS.
    def insertar_historial_paciente_registrado(self):
        # 1. Traemos las reservas.
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

        # 2. Extraemos los doctores y especialidades para crear un mapa.
        medicos_con_especialidades = DoctorModel.objects.values_list(
            "primer_nombre",
            "segundo_nombre",
            "ap_paterno",
            "ap_materno",
            "especialidades__nombre_especialidad",
        )

        # 3. Construimos el diccionario de especialidades por doctor.
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

        # 4. Mapeamos los IDs de usuario a IDs de paciente.
        mapa_pacientes_raw = PacienteModel.objects.values_list("id", "fk_user_id")
        diccionario_pacientes = {
            fk_user: id_paciente for id_paciente, fk_user in mapa_pacientes_raw
        }

        historial_pac_registrado = []
        # Set para evitar duplicados (mismo paciente, misma especialidad).
        pacientes_especialidades = set()

        # 5. Iteramos sobre las reservas para crear los historiales.
        for (
            id,
            reserva_cerrada,
            reserva_uuid,
            fk_usuario_id,
            nombre_doctor,
            fecha_reserva,
            especialidad_reserva,
        ) in reservas:
            # Solo historiales para citas completadas/cerradas.
            if reserva_cerrada == 0:
                continue

            # Buscamos el ID real del paciente.
            id_paciente_real = diccionario_pacientes.get(fk_usuario_id)
            if id_paciente_real is None:
                continue

            # Buscamos la especialidad.
            medico_limpio = nombre_doctor.strip() if nombre_doctor else ""
            nombre_especialidad = mapa_medico_especialidad.get(
                medico_limpio, "Medicina General"
            )

            # Validamos que no exista ya un historial para ese paciente y especialidad.
            clave_historial = (id_paciente_real, nombre_especialidad)
            if clave_historial in pacientes_especialidades:
                continue

            # Llamamos a Faker para generar el historial.
            datos_medicos = fake.historial_por_especialidad(nombre_especialidad)

            # Armamos el registro.
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

        # Si no hay nada que insertar, avisamos.
        if not historial_pac_registrado:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No se encontraron historiales aptos para insertar."
                )
            )
            return

        # Insertamos en bloque.
        instancias_historial = [
            HistorialClinicoModel(**reg) for reg in historial_pac_registrado
        ]
        HistorialClinicoModel.objects.bulk_create(instancias_historial, batch_size=1000)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES REGISTRADOS inyectados con coherencia total."
            )
        )

    # Método para insertar a PACIENTES NO REGISTRADOS.
    def insertar_paciente_no_registrado(self):
        self.stdout.write(
            self.style.SUCCESS("  ✅ Método para insertar a Pacientes NO REGISTRADOS.")
        )
        generador_faker = Faker("es_CL")
        lista_paciente_data = []

        # Creamos 2500 pacientes no registrados.
        for i in range(1, 2501):
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

        # Guardamos en bloque.
        instancias_paciente = [
            PacienteNoRegisterModel(**reg) for reg in lista_paciente_data
        ]
        PacienteNoRegisterModel.objects.bulk_create(
            instancias_paciente, batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS("  ✅ PACIENTE NO REGISTRADO INSERTADOS CORRECTAMENTE")
        )

    # Método para insertar reservas de pacientes NO REGISTRADOS.
    def insertar_reserva_paciente_no_registrado(self, horarios_ocupados=None):
        try:
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método Insertar las Reservas Iniciando.......")
            )

            if horarios_ocupados is None:
                horarios_ocupados = set()

            listado_doctores = list(
                DoctorModel.objects.prefetch_related(
                    "doctor_clinica", "especialidades"
                ).all()
            )
            paciente_registrado = list(
                PacienteNoRegisterModel.objects.values_list("id", flat=True)
            )

            listas_reservas = []
            lista_debito = []
            lista_credito = []

            # 🚨 AQUÍ ESTABA EL ERROR: Se eliminó 'horarios_ocupados = set()'
            # Ahora usa el set compartido del handle().

            # Objetivo en 2000.
            objetivo = 2000

            while len(listas_reservas) < objetivo:
                ahora = timezone.now()
                dias_aleatorios = random.randint(-60, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_aleatorios)
                fecha_formateada = objeto_fecha_reserva.date()

                tipo_pago = ""
                pago_realizado = 0
                reserva_cerrada = random.choice([1, 0])

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

                # Buscador de horas.
                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")
                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    # Verificamos en el SET GLOBAL (que ahora sí tiene las horas del método anterior).
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
                ReservaModel.objects.bulk_create(instancias_reserva, batch_size=1000)

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
                        f"  ✅ 2000 Reservas pagadas con DÉBITO o CRÉDITO inyectadas con éxito PACIENTE NO REGISTRADO."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  ⚠️ No se generaron reservas válidas para insertar."
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    # Método para insertar el historial a Pacientes NO REGISTRADOS.
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
        # Set para evitar duplicados por (paciente, especialidad).
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
        HistorialPacNoRegistradoModel.objects.bulk_create(
            instancias_historial, batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES NO REGISTRADOS inyectados con coherencia total."
            )
        )
