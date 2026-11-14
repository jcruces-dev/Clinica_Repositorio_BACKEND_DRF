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
from Clinica_DRF.utils.providers import fake

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
        self.stdout.write(
            self.style.WARNING(
                "⚡ Iniciando el proceso de sembrado de datos (Seeding)..."
            )
        )
        # -----------------------------------------------------------------
        # Antes de insertar, debemos borrar los datos anteriores para evitar problemas.
        # Borramos primero lo que depende de otras tablas (Hijos)
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
        # Borramos las relaciones intermedias Many-to-Many nativas si es necesario
        # Borramos las tablas maestras independientes
        Especialidad.objects.all().delete()
        ComunaClinicaModel.objects.all().delete()

        # Finalmente barremos los usuarios base y grupos (Padres globales)
        CustomersUsers.objects.filter(is_superuser=False).delete()
        Group.objects.all().delete()
        #
        self.stdout.write(
            self.style.SUCCESS("  🗑️ Base de datos limpia y lista para la siembra.")
        )
        # Los métodos deben quedar en el orden correcto de ejecución.
        # -----------------------------------------------------------------
        self.insertar_grupos()
        self.insertar_clinicas()
        self.insertar_especialidad()
        self.insertar_usuario_doctor()
        self.insertar_usuario_secretaria()
        self.insertar_usuario_paciente()
        # =========================================================================
        # CONTROL DE AGENDAS GLOBAL UNIFICADO
        # =========================================================================
        horarios_globales = set()  # Se crea vacío aquí en el método padre

        # El primer método llena el set con las horas ocupadas por registrados
        self.insertar_reserva_paciente_registrado(horarios_ocupados=horarios_globales)
        self.insertar_historial_paciente_registrado()

        self.insertar_paciente_no_registrado()

        # El segundo método lee el set que YA TIENE horas guardadas y evita duplicarlas
        self.insertar_reserva_paciente_no_registrado(
            horarios_ocupados=horarios_globales
        )
        # self.insertar_historial_paciente_no_registrado()
        # =========================================================================
        # self.insertar_reserva_paciente_registrado()
        # self.insertar_historial_paciente_registrado()
        # self.insertar_paciente_no_registrado()
        # self.insertar_reserva_paciente_no_registrado()
        # self.insertar_historial_paciente_no_registrado()
        # -----------------------------------------------------------------
        #
        self.stdout.write(self.style.SUCCESS("¡Proceso finalizado con éxito!"))

    # Método para insertar los grupos en DRF.
    def insertar_grupos(self):
        self.stdout.write("Procesando grupos de permisos con Pandas...")

        # Limpiamos la tabla para evitar duplicados de GRUPO (Buena Práctica).
        Group.objects.all().delete()

        # Creamos el DataFrame con los 3 roles.
        df_grupos = pd.DataFrame({"name": ["Paciente", "Doctor", "Secretaria"]})

        # Convertimos a instancias del modelo y hacemos el bulk_create
        registros = df_grupos.to_dict("records")
        objetos_grupos = [Group(**reg) for reg in registros]
        # Realizamos la insercción.
        Group.objects.bulk_create(objetos_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 3 Grupos (Paciente, Doctor, Secretaria) creados correctamente."
            )
        )

    # Método para insertar as Clínicas.
    # Recordar que debe ir fuera del método HANDLE y lo ejecutamos adentro.
    def insertar_clinicas(self):
        # 1. Crear datos de ejemplo (un diccionario)
        # 1. Crear datos de ejemplo (un diccionario)
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
            #
            registro = {
                "nombre_clinica": datos_clinica["nombre_clinica"][i],
                "comuna_clinica": datos_clinica["comuna_clinica"][i],
                "direccion_clinica": datos_clinica["direccion_clinica"][i],
            }
            #
            lista.append(registro)
        objetos_clinica = [ComunaClinicaModel(**reg) for reg in lista]
        # 5. Inserción masiva limpia a PostgreSQL/SQLite en UNA SOLA CONSULTA
        ComunaClinicaModel.objects.bulk_create(objetos_clinica)
        #
        self.stdout.write(
            self.style.SUCCESS("  ✅ 5 Clínicas insertadas correctamente.")
        )

    # Método para insertar las Especialidades.
    # Recordar que debe ir fuera del método HANDLE y lo ejecutamos adentro.
    def insertar_especialidad(self):
        # 1. Crear datos de ejemplo (un diccionario)
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

        # 2. Convertirlo en un DataFrame de Pandas
        df_especialidad = pd.DataFrame(datos_especialidad)
        # Convertimos el DataFrame a Diccionario.
        registro_especialidad = df_especialidad.to_dict("records")
        # 4. Transformar los diccionarios en instancias del modelo real de Django.
        # Esto por que al realizar el BULK con pandas, solo se recibe la Instancias de los Modelos a insertar.
        # Transformamos los datos en argumentos nombrados directos para el modelo de Django.
        # Este código, lo que hace es ahorrar el tiempo.
        objetos_especialidad = [Especialidad(**reg) for reg in registro_especialidad]
        # 5. Inserción masiva limpia a PostgreSQL/SQLite en UNA SOLA CONSULTA
        Especialidad.objects.bulk_create(objetos_especialidad)
        #
        self.stdout.write(
            self.style.SUCCESS("  ✅ Especialidades insertadas correctamente.")
        )

    # Este es el método para insertar usuarios Doctor.
    def insertar_usuario_doctor(self):
        # 1. Eliminamos los registros previos de forma segura
        # Obtenemos el GRUPO creado anteriormente.
        grupo_doctor = Group.objects.get(name="Doctor")
        fake = Faker("es_CL")
        # Inicializamos las listas.
        lista_usuarios_data = []
        lista_doctores_data = []
        # Utilizamos una pass comun (solo prueba).
        password_hash = make_password("123")
        # Creamos del 1 al 41 que es la cantidad de DOCTORES a poblar.
        for i in range(1, 41):
            #
            sexo = random.choice(["M", "F"])
            edad_doctor = fake.random_int(min=25, max=60)
            #
            if sexo == "M":
                primer_nombre_doctor = fake.first_name_male()
                segundo_nombre_doctor = fake.first_name_male()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "M"
                # Generamos datos de acceso únicos como e username y gmail a partir de los nombres y apellidos.
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                email = f"{username_doctor}@gmail.com"
                # Utilizamos una pass comun (solo prueba).
                password = password_hash
                # Dejamos que la base de datos asigne el ID autoincremental real por ende NO la agregamos acá.
                data_user = {
                    "username": username_doctor,
                    "password": password,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                # Debemos revisar que no se repitan los username.
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    # Guardamos los datos en la lista.
                    lista_usuarios_data.append(data_user)

                    # En este punto no le ponemos "fk_user_id" todavía porque no sabemos qué ID le dará la BD.
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
                    # Volvemos a agregar los datos a la lista.
                    lista_doctores_data.append(data_doctor)
            else:
                primer_nombre_doctor = fake.first_name_female()
                segundo_nombre_doctor = fake.first_name_female()
                ap_paterno_doctor = fake.last_name()
                ap_materno_doctor = fake.last_name()
                telefono_doctor = f"+56 9{fake.random_int(min=10000000, max=99999999)}"
                sexo_doctor = "F"
                # Generamos datos de acceso únicos como e username y gmail a partir de los nombres y apellidos.
                primer_nombre_corto = primer_nombre_doctor[:3].lower()
                ap_paterno_corto = ap_paterno_doctor[:3].lower()
                username_doctor = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
                email = f"{username_doctor}@gmail.com"
                # Utilizamos una pass comun (solo prueba).
                password = password_hash
                # Dejamos que la base de datos asigne el ID autoincremental real por ende NO la agregamos acá.
                data_user = {
                    "username": username_doctor,
                    "password": password,
                    "email": email,
                    "usuario_uuid": str(uuid.uuid4()),
                }
                # Debemos revisar que no se repitan los username.
                if not CustomersUsers.objects.filter(username=username_doctor).exists():
                    # Guardamos los datos en la lista.
                    lista_usuarios_data.append(data_user)

                    # En este punto no le ponemos "fk_user_id" todavía porque no sabemos qué ID le dará la BD.
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
                    # Volvemos a agregar los datos a la lista.
                    lista_doctores_data.append(data_doctor)
        # INSERCIÓN EN LA BASE DE DATOS.
        # Creamos DataFrame con los datos de las listas.
        # df_usuarios = pd.DataFrame(lista_usuarios_data)
        # Utilizamos esta abreviatiura para ahorra sintaxis.
        # Convertimos la lista a diccionarios y luego lo utilizamos sus datos y las pasamos directamente a su instancia.
        instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
        # Bulk create de usuarios.
        # Django nos devuelve en 'usuarios_creados' la lista exacta con los IDs autoincrementales ya asignados.
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(self.style.SUCCESS("  ✅ 40 Usuarios base creados."))

        # Asignación masiva al Grupo.
        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_doctor.id)
            for user in usuarios_creados
        ]
        # Realizamos elbulk a nuestra tabla que viene por defecto en DRF.
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Usuarios asignados al Grupo 'Doctor' exitosamente."
            )
        )

        # ASIGNACIÓN PARA EL PERFIL MÉDICO.
        # Unimos cada perfil médico con su respectivo ID de usuario usando zip() ya que ambas
        # listas mantienen el mismo orden.
        for idx, user in enumerate(usuarios_creados):
            # Pasamos el ID al campo que faltaba anteriormente en doctores para la insercción.
            lista_doctores_data[idx]["fk_user_id"] = user.id

        # Ahora pasamos la lista definitiva por Pandas para instanciar los perfiles médicos
        # Pasamosla lista con los idgenerados arriba (for idx, user in enumerate(usuarios_creados):).
        # df_doctores = pd.DataFrame(lista_doctores_data)
        # Convertimos la lista a diccionario e instanciamos su modelo.
        instancias_doctores = [DoctorModel(**reg) for reg in lista_doctores_data]
        # Realizamos el insert.
        doctores_creados = DoctorModel.objects.bulk_create(instancias_doctores)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Perfiles de Doctores creados en la base de datos."
            )
        )

        # =========================================================================
        # RELACIÓN MUCHOS A MUCHOS (DOCTOR <-> CLÍNICA)
        # =========================================================================
        self.stdout.write("Asociando doctores a sus clínicas de forma aleatoria...")

        # Como no hay propiedad .clinicas en DoctorModel
        # (porqué generé yo mismo la tabla intermedia con datos extras que necesitaba), accedemos al modelo intermedio
        # que Django autogeneró basándose en mi estructura.
        DoctorClinica = DoctorModel._meta.get_field(
            "doctor_clinica"
        ).remote_field.through
        # Debemos crear la lista.
        lista_relaciones_clinicas = []

        # Obtenemos los IDs reales disponibles en la tabla de clínicas
        clinicas_disponibles = list(
            ComunaClinicaModel.objects.values_list("id", flat=True)
        )

        # Por defecto si no se encuentra disponibles los ID de las clínicas,
        # entonces las pasamos manualmente, porque sabemos que solo son 5.
        if not clinicas_disponibles:
            clinicas_disponibles = [1, 2, 3, 4, 5]

        # clinicas_disponibles: Muestrea directamente sobre los IDs reales que la base de datos
        # acaba de generar de forma autoincremental en el paso previo (self.insertar_clinicas()).
        # Ya no debo depender de números fijos o adivinados como [1, 2, 3, 4, 5].
        # Osea este for es la solucion para que no entre al if not y asignar manualmente los id.
        # Si en mi base de datos solo existe 1 clínica creada, pero random.randint(1, 2) pide elegir 2,
        # la función random.sample se caería con un error porque no puedo sacar dos elementos
        # de una bolsa que solo tiene uno. Al usar min(), el sistema dice:
        # "Ok, elijo el menor entre las 2 clínicas y no generar error.
        for doc in doctores_creados:
            cantidad_clinicas = random.randint(1, 2)
            clinicas_asignadas = random.sample(
                clinicas_disponibles, min(len(clinicas_disponibles), cantidad_clinicas)
            )
            # Realizamos el (poblamiento Many-to-Many) osea muchos a muchos.
            for clinica_id in clinicas_asignadas:
                # Acá unimos al Doctor con una o más clínicas disponible.
                lista_relaciones_clinicas.append(
                    # Instanciamos mi modelo Intermedio. Pero acá solamente obtendremos si IDs.
                    # Esto para armar el cruce.
                    DoctorClinica(
                        # Campo real de mi BD (doctormodel_id)
                        doctormodel_id=doc.id,
                        # Campo real de mi BD (comunaclinicamodel_id)
                        comunaclinicamodel_id=clinica_id,
                    )
                )
        # Inserción final en la tabla intermedia física
        DoctorClinica.objects.bulk_create(lista_relaciones_clinicas)
        # Enviamos el ultimo mensaje que los doctoresfueron INSERTADOS CORRECTAMENTE.
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Clínica inyectadas correctamente."
            )
        )

        # Creamos la lista vacía para acumular las instancias
        lista_relaciones_especialidades = []

        DoctorEspecialidad = DoctorModel._meta.get_field(
            "especialidades"
        ).remote_field.through
        listado_especialidades = list(Especialidad.objects.values_list("id", flat=True))
        # Nos aseguramos de tener una lista limpia de IDs reales de especialidades
        listado_especialidades = list(Especialidad.objects.values_list("id", flat=True))

        # Validación de seguridad por si la tabla maestra está vacía
        if not listado_especialidades:
            self.stdout.write(
                self.style.ERROR(
                    "❌ No se encontraron especialidades creadas en la base de datos."
                )
            )
            return

        # Recorremos los doctores creados para asignarles entre 1 y 2 especialidades
        for doc in doctores_creados:
            # Definimos cuántas especialidades tendrá este doctor al azar
            cantidad_especialidades = random.randint(1, 2)

            # Muestreamos de forma segura evitando errores de desbordamiento con min()
            especialidades_asignadas = random.sample(
                listado_especialidades,
                min(len(listado_especialidades), cantidad_especialidades),
            )

            # Creamos el cruce relacional en la tabla intermedia
            for esp_id in especialidades_asignadas:
                lista_relaciones_especialidades.append(
                    DoctorEspecialidad(
                        # Campo de la clave foránea que apunta al doctor
                        doctormodel_id=doc.id,
                        # Campo de la clave foránea que apunta a la especialidad
                        especialidad_id=esp_id,
                    )
                )

        # Inserción masiva ultra veloz directa a la base de datos
        DoctorEspecialidad.objects.bulk_create(lista_relaciones_especialidades)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Doctor-Especialidad inyectadas correctamente."
            )
        )

    # Este es el método para insertar usuarios Doctor.
    def insertar_usuario_secretaria(self):
        # 1. Eliminamos los registros previos de forma segura
        # SecretariaModel.objects.all().delete()
        # CustomersUsers.objects.filter(is_superuser=False).delete()

        # Obtenemos el GRUPO creado anteriormente.
        grupo_secretaria = Group.objects.get(name="Secretaria")
        fake = Faker("es_CL")

        # Inicializamos las listas.
        lista_usuarios_data = []
        lista_secretaria_data = []

        # Creamos del 1 al 41 que es la cantidad de DOCTORES a poblar.
        for i in range(1, 11):
            primer_nombre_doctor = fake.first_name()
            segundo_nombre_doctor = fake.first_name()
            ap_paterno_doctor = fake.last_name()
            ap_materno_doctor = fake.last_name()
            edad_secretaria = fake.random_int(min=25, max=60)
            sexo_secretaria = fake.random_element(elements=("M", "F"))
            telefono_secretaria = f"+56 9{fake.random_int(min=10000000, max=99999999)}"

            # Generamos datos de acceso únicos como e username y gmail a partir de los nombres y apellidos.
            primer_nombre_corto = primer_nombre_doctor[:3].lower()
            ap_paterno_corto = ap_paterno_doctor[:3].lower()
            username_secretaria = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{fake.random_int(100,999)}"
            email = f"{username_secretaria}@gmail.com"
            # Utilizamos una pass comun (solo prueba).
            password = make_password("123")
            # Dejamos que la base de datos asigne el ID autoincremental real por ende NO la agregamos acá.
            data_user = {
                "username": username_secretaria,
                "password": password,
                "email": email,
                "usuario_uuid": str(uuid.uuid4()),
            }
            # Debemos revisar que no se repitam los username.
            if not CustomersUsers.objects.filter(username=username_secretaria).exists():
                # Guardamos los datos en la lista.
                lista_usuarios_data.append(data_user)
            # En este punto no le ponemos "fk_user_id" todavía porque no sabemos qué ID le dará la BD.
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
            # Volvemos a agregar los datos a la lista.
            lista_secretaria_data.append(data_secreatria)

        # INSERCIÓN EN LA BASE DE DATOS.
        # Creamos DataFrame con los datos de las listas.
        df_usuarios = pd.DataFrame(lista_usuarios_data)
        # Utilizamos esta abreviatiura para ahorra sintaxis.
        # Convertimos la lista a diccionarios y luego lo utilizamos sus datos y las pasamos directamente a su instancia.
        instancias_usuarios = [
            CustomersUsers(**reg) for reg in df_usuarios.to_dict("records")
        ]

        # Bulk create de usuarios.
        # Django nos devuelve en 'usuarios_creados' la lista exacta con los IDs autoincrementales ya asignados.
        usuarios_creados = CustomersUsers.objects.bulk_create(instancias_usuarios)
        self.stdout.write(self.style.SUCCESS("  ✅ 10 Usuarios base creados."))

        # Asignación masiva al Grupo.
        UserGroupThrough = CustomersUsers.groups.through
        relaciones_grupos = [
            UserGroupThrough(customersusers_id=user.id, group_id=grupo_secretaria.id)
            for user in usuarios_creados
        ]
        # Realizamos elbulk a nuestra tabla que viene por defecto en DRF.
        UserGroupThrough.objects.bulk_create(relaciones_grupos)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Usuarios asignados al Grupo 'Doctor' exitosamente."
            )
        )

        # ASIGNACIÓN PARA EL PERFIL MÉDICO.
        # Unimos cada perfil médico con su respectivo ID de usuario usando zip() ya que ambas
        # listas mantienen el mismo orden.
        for idx, user in enumerate(usuarios_creados):
            # Pasamos el ID al campo que faltaba anteriormente en doctores para la insercción.
            lista_secretaria_data[idx]["fk_user_id"] = user.id

        # Ahora pasamos la lista definitiva por Pandas para instanciar los perfiles médicos
        # Pasamosla lista con los idgenerados arriba (for idx, user in enumerate(usuarios_creados):).
        df_secretaria = pd.DataFrame(lista_secretaria_data)
        # Convertimos la lista a diccionario e instanciamos su modelo.
        instancias_secretaria = [
            SecretariaModel(**reg) for reg in df_secretaria.to_dict("records")
        ]
        # Realizamos el insert.
        secretarias_creados = SecretariaModel.objects.bulk_create(instancias_secretaria)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ 40 Perfiles de Doctores creados en la base de datos."
            )
        )

        # =========================================================================
        # RELACIÓN MUCHOS A MUCHOS (SECRETARIA <-> CLÍNICA)
        # =========================================================================
        self.stdout.write("Asociando secretarias a sus clínicas de forma aleatoria...")

        # Como no hay propiedad .clinicas en SecretariaModel
        # (porqué generé yo mismo la tabla intermedia con datos extras que necesitaba), accedemos al modelo intermedio
        # que Django autogeneró basándose en mi estructura.
        SecretariaClinica = SecretariaModel._meta.get_field(
            "secretaria_clinica"
        ).remote_field.through
        # Debemos crear la lista.
        lista_relaciones_clinicas = []

        # Obtenemos los IDs reales disponibles en la tabla de clínicas
        clinicas_disponibles = list(
            ComunaClinicaModel.objects.values_list("id", flat=True)
        )

        # Por defecto si no se encuentra disponibles los ID de las clínicas,
        # entonces las pasamos manualmente, porque sabemos que solo son 5.
        if not clinicas_disponibles:
            clinicas_disponibles = [1, 2, 3, 4, 5]

        # clinicas_disponibles: Muestrea directamente sobre los IDs reales que la base de datos
        # acaba de generar de forma autoincremental en el paso previo (self.insertar_clinicas()).
        # Ya no debo depender de números fijos o adivinados como [1, 2, 3, 4, 5].
        # Osea este for es la solucion para que no entre al if not y asignar manualmente los id.
        # Si en mi base de datos solo existe 1 clínica creada, pero random.randint(1, 2) pide elegir 2,
        # la función random.sample se caería con un error porque no puedo sacar dos elementos
        # de una bolsa que solo tiene uno. Al usar min(), el sistema dice:
        # "Ok, elijo el menor entre las 2 clínicas y no generar error.
        for doc in secretarias_creados:
            cantidad_clinicas = random.randint(1, 2)
            clinicas_asignadas = random.sample(
                clinicas_disponibles, min(len(clinicas_disponibles), cantidad_clinicas)
            )
            # Realizamos el (poblamiento Many-to-Many) osea muchos a muchos.
            for clinica_id in clinicas_asignadas:
                # Acá unimos al Doctor con una o más clínicas disponible.
                lista_relaciones_clinicas.append(
                    # Instanciamos mi modelo Intermedio. Pero acá solamente obtendremos si IDs.
                    # Esto para armar el cruce.
                    SecretariaClinica(
                        # Campo real de mi BD (doctormodel_id)
                        secretariamodel_id=doc.id,
                        # Campo real de mi BD (comunaclinicamodel_id)
                        comunaclinicamodel_id=clinica_id,
                    )
                )
        # Inserción final en la tabla intermedia física
        SecretariaClinica.objects.bulk_create(lista_relaciones_clinicas)
        # Enviamos el ultimo mensaje que los doctoresfueron INSERTADOS CORRECTAMENTE.
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ Relaciones Secretaria-Clínica inyectadas correctamente."
            )
        )

    # Método para insertar reservas de pacientes registrados.
    def insertar_usuario_paciente(self):
        try:
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método para insertar a Usuarios Pacientes.")
            )

            # Obtenemos el GRUPO creado anteriormente, en este caso PACIENTE.
            grupo_paciente = Group.objects.get(name="Paciente")
            # Generamos la instancia de Faker.
            generador_faker = Faker("es_CL")

            # Inicializamos las listas.
            lista_usuarios_data = []
            lista_paciente_data = []
            lista_direccion_data = []
            # Hasheamos las pass antes del for si no, se demora en ejecutarse el script mas de 50 miutos. (OJO AHÍ).
            password_hash = make_password("123")
            # Usamos .values_list('username', flat=True) para traer solo strings, no objetos pesados.
            usernames_existentes = set(
                CustomersUsers.objects.values_list("username", flat=True)
            )
            # Creamos del 1 al 3501 que es la cantidad de PACIENTES a poblar.
            for i in range(1, 3501):
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
                    # Generamos datos de acceso únicos como el username y gmail a partir de los nombres y apellidos.
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"
                    # Dejamos que la base de datos asigne el ID autoincremental real por ende NO la agregamos acá.
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    # Aquí verificamos si NO está en el SET de Python y además cuidamos que no se duplique dentro del mismo ciclo
                    if username_paciente not in usernames_existentes:
                        lista_usuarios_data.append(data_user)
                        usernames_existentes.add(username_paciente)

                        # Acá NO agregamos el "fk_user_id" todavía, porque no sabemos qué ID le dará la BD.
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
                        # Volvemos a agregar los datos a la lista.
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
                    # Generamos datos de acceso únicos como el username y gmail a partir de los nombres y apellidos.
                    primer_nombre_corto = primer_nombre_paciente[:3].lower()
                    ap_paterno_corto = ap_paterno_paciente[:3].lower()
                    username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                    email = f"{username_paciente}@gmail.com"
                    # Dejamos que la base de datos asigne el ID autoincremental real por ende NO la agregamos acá.
                    data_user = {
                        "username": username_paciente,
                        "password": password_hash,
                        "email": email,
                        "usuario_uuid": str(uuid.uuid4()),
                    }
                    # Aquí verificamos si NO está en el SET de Python y además cuidamos que no se duplique dentro del mismo ciclo
                    if username_paciente not in usernames_existentes:
                        lista_usuarios_data.append(data_user)
                        usernames_existentes.add(username_paciente)

                        # Acá NO agregamos el "fk_user_id" todavía, porque no sabemos qué ID le dará la BD.
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
                        # Volvemos a agregar los datos a la lista.
                        lista_paciente_data.append(data_paciente)
            # INSERCIÓN EN LA BASE DE DATOS (USUARIOS).
            # Convertimos los diccionarios a instancias del modelo ANTES del bulk_create.
            instancias_usuarios = [CustomersUsers(**reg) for reg in lista_usuarios_data]
            # Pasamos la instancia y colocamos batch_size=1000, para qu inserte por lotes de 1000 registros,
            # haciendo que la ejecucion se demore muchos menos.
            usuarios_creados = CustomersUsers.objects.bulk_create(
                instancias_usuarios, batch_size=1000
            )
            self.stdout.write(
                self.style.SUCCESS("  ✅ Usuarios Pacientes creados exitosamente.")
            )

            # Asignación masiva al Grupo.
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

            # Asiganos a los pacientes creados al GRUPO PACIENTES.
            for idx, user in enumerate(usuarios_creados):
                lista_paciente_data[idx]["fk_user_id"] = user.id

            # Convertimos los diccionarios a instancias de PacienteModel.
            instancias_paciente = [PacienteModel(**reg) for reg in lista_paciente_data]
            # Insertamos en la BD por lotes de 1000.
            paciente_creados = PacienteModel.objects.bulk_create(
                instancias_paciente, batch_size=1000
            )
            # Definimos las comunas por defecto.
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

            # Convertimos los diccionarios a instancias de DireccionModel
            instancias_direccion = [
                DireccionModel(**reg) for reg in lista_direccion_data
            ]
            direcciones_creadas = DireccionModel.objects.bulk_create(
                instancias_direccion, batch_size=1000
            )
            # Mostramos los mensajes en la consola de depuración.
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

    # # Método para insertar las reservas.
    # def insertar_reserva_paciente_registrado(self):
    #     try:
    #         #
    #         self.stdout.write(self.style.SUCCESS("  ✅ Método Insertar las Reservas Iniciando......."))
    #         # Como este es una INSERCCIÓN MASIVA, no es buena práctica utilizar el metodo all y recorrer todo en
    #         # un for, esto sería interminable y a su vez lento, es un trabajo ineficiente para la insercción masiva.
    #         # Enotnces lo que debemos hacer, es obtener ese objeto de los modelos y convertirlo de inmediato a lista.
    #         # En esta lista solo guardamos los IDs necesarios.
    #         listado_doctores = list(DoctorModel.objects.prefetch_related('doctor_clinica', 'especialidades').all())
    #         #
    #         listado_pacientes_ids = list(CustomersUsers.objects.filter(pacientemodel__isnull=False))
    #         #print(listado_pacientes_ids)
    #         listado_clinicas = list(ComunaClinicaModel.objects.values_list('id', 'nombre_clinica', 'comuna_clinica', 'direccion_clinica'))
    #         #print(listado_clinicas)
    #         # Para las especialidades, si necesitas el nombre y el valor, podemos traer el QuerySet completo
    #         especialidades = list(Especialidad.objects.values_list('id', 'nombre_especialidad', 'valor_especialidad'))
    #         #print(especialidades)
    #         # IDs de los pacientes REGISTRADOS.
    #         paciente_registrado = list(PacienteModel.objects.values_list('id', flat=True))
    #         # Elegimos un Doctor al azar de la memoria.
    #         #print(especialidades)
    #         listas_reservas = []
    #         lista_debito = []
    #         lista_credito = []
    #         # Conjunto para controlar horarios únicos por doctor
    #         horarios_ocupados = set()
    #         objetivo = 34000
    #         # Realizamos los registros para los INSERT MASIVOS.
    #         while len(listas_reservas) < objetivo:
    #             #
    #             tipo_pago = ""
    #             pago_realizado = 0
    #             #
    #             reserva_cerrada = random.choice([1, 0])
    #             #
    #             if reserva_cerrada == 1:
    #                 #
    #                 tipo_pago = random.choice(["Crédito", "Débito"])
    #                 pago_realizado = 1
    #             #
    #             if reserva_cerrada == 0:
    #                 tipo_pago = random.choice(["Crédito", "Débito", ""])
    #                 #
    #                 if tipo_pago == "":
    #                     pago_realizado = 0
    #                 if tipo_pago != "":
    #                     pago_realizado = 1
    #             #
    #             reser_anulada = random.choice([1, 0])
    #             reser_confirmada = 0
    #             if reser_anulada == 1:
    #                 reser_confirmada = 0
    #             if reser_anulada == 0:
    #                 reser_confirmada = 1
    #             # Elegimos un Doctor al azar de la lista que tenemos en memoria
    #             doctor = random.choice(listado_doctores)
    #             nombre_completo_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"

    #             # Extraemos las clínicas asociadas a este doctor desde la memoria ram (gracias al prefetch_related)
    #             clinicas_del_doctor = list(doctor.doctor_clinica.all())
    #             if not clinicas_del_doctor:
    #                 continue # Si este doctor no tiene clínicas asignadas, saltamos al siguiente

    #             # Elegimos una clínica válida para el doctor (Este es un objeto completo del modelo)
    #             clinica_elegida = random.choice(clinicas_del_doctor)

    #             # Extraemos las especialidades reales del doctor
    #             especialidades_del_doctor = list(doctor.especialidades.all())
    #             if not especialidades_del_doctor:
    #                 continue # Si el doctor no tiene especialidades registradas, saltamos

    #             # Elegimos una especialidad válida para el doctor (Objeto completo del modelo)
    #             especialidad_elegida = random.choice(especialidades_del_doctor)

    #             # Obtenemos la Fecha y Hora actual.
    #             ahora = datetime.now()
    #             # Crea días en el futuro, esto para utilizar varias fechas de reservas a futuro.
    #             # Genera un número entero aleatorio entre 0 y 30.
    #             # Ese número representa cuántos días hacia adelante se moverá la fecha.
    #             # Ejemplo: dias_en_el_futuro = 12
    #             dias_en_el_futuro = random.randint(0, 90)
    #             # Suma estos días a la fecha actual usando timedelta.
    #             # Resultado: una fecha futura aleatoria entre hoy y dentro de 30 días.
    #             objeto_fecha_reserva = ahora + timedelta(days=dias_en_el_futuro)
    #             # Rango de 8 a 22 hrs de inicio.
    #             hora_random = random.randint(8, 22)
    #             # Forzamos el minuto en 00 para que sean HORAS COMPLETAS (no cada 30 min)
    #             objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
    #             # Sumas una hora, para el campo_hora_termino.
    #             objeto_hora_termino = objeto_hora_inicio + timedelta(hours=1)

    #             # Pasamos los datos al diccionario.
    #             datos_reservas = {
    #                 'fecha_creacion_reserva': datetime.now().strftime('%Y-%m-%d'),
    #                 'usuario_creacion_reserva': "Admin",
    #                 'fecha_reserva': objeto_fecha_reserva.date(),
    #                 # Dará "10:00:00"
    #                 'hora_inicio': objeto_hora_inicio.strftime('%H:%M:%S'),
    #                 # Dará "11:00:00"
    #                 'hora_termino': objeto_hora_termino.strftime('%H:%M:%S'),
    #                 # Accedemos de forma segura mediante objetos (.nombre_especialidad, .nombre_clinica)
    #                 'especialidad': especialidad_elegida.nombre_especialidad,
    #                 'nombre_doctor': nombre_completo_doctor,
    #                 'nombre_clinica': clinica_elegida.nombre_clinica,
    #                 'comuna_clinica': clinica_elegida.comuna_clinica,
    #                 'direccion_clinica': clinica_elegida.direccion_clinica,
    #                 'tipo_pago': tipo_pago,
    #                 'reserva_uuid': str(uuid.uuid4()),
    #                 'reserva_cerrada': reserva_cerrada,
    #                 'pago_realizado': pago_realizado,
    #                 'reser_anulada': reser_anulada,
    #                 'reser_confirmada': reser_confirmada,
    #                 # Asignamos el ID directo del paciente a la columna FK física
    #                 'fk_usuario': random.choice(listado_pacientes_ids),
    #             }
    #             # Validación: doctor no puede repetir hora en el mismo día.
    #             clave_reserva = (
    #                 doctor.id,
    #                 objeto_fecha_reserva.date(),
    #                 objeto_hora_inicio.strftime('%H:%M:%S')
    #             )

    #             if clave_reserva in horarios_ocupados:
    #                 # ya existe una reserva en ese horario para este doctor
    #                 continue
    #             else:
    #                 horarios_ocupados.add(clave_reserva)
    #                 listas_reservas.append(datos_reservas)

    #         # INSERCCIÓN RESERVAS MASIVA FINAL CON PANDAS
    #         if listas_reservas:
    #             #df_reservas = pd.DataFrame(listas_reservas)
    #             instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
    #             reservas_creadas = ReservaModel.objects.bulk_create(instancias_reserva, batch_size=1000)

    #             # Extraemos los UUIDs que acabamos de crear en este método
    #             uuids_creados = [r['reserva_uuid'] for r in listas_reservas]

    #             # Filtramos para traer SOLO las reservas de este lote
    #             reservas = list(ReservaModel.objects.filter(reserva_uuid__in=uuids_creados).values_list('id', 'tipo_pago', 'pago_realizado', 'especialidad'))

    #             dict_especialidades = {e.nombre_especialidad: e for e in Especialidad.objects.all()}
    #             #
    #             for id, tipo_pago, pago_realizado, especialidad in reservas:
    #                 valor_especialidad = dict_especialidades.get(especialidad)
    #                 if not valor_especialidad:
    #                     continue
    #                 # id = ReservaModel.objects.get(pk=id)
    #                 #
    #                 precio_int = int(valor_especialidad.valor_especialidad)
    #                 #
    #                 if pago_realizado == 1 and tipo_pago == "Crédito":
    #                     cant_cuotas = random.choice([3, 6, 9])
    #                     monto_cuotas = None
    #                     if cant_cuotas == 3:
    #                         monto_cuotas = math.ceil(int(precio_int) / 3)
    #                     if cant_cuotas == 6:
    #                         monto_cuotas = math.ceil(int(precio_int) / 6)
    #                     if cant_cuotas == 9:
    #                         monto_cuotas = math.ceil(int(precio_int) / 9)
    #                     credito = {
    #                         'credito': 1,
    #                         'fecha_pago': ahora.strftime('%Y-%m-%d %H:%M:%S.%f'),
    #                         'credito_uuid': str(uuid.uuid4()),
    #                         'monto': precio_int,
    #                         'cant_cuotas': cant_cuotas,
    #                         'monto_total': precio_int,
    #                         'monto_cuotas': monto_cuotas,
    #                         # OJO; paraque nos pidauna instancia y no utilizar .get() que es mala práctica
    #                         # para efecto de este caso, la columna de la BD; fk_reserva,se le debe agregar el id
    #                         # al final y queda así; fk_reserva_id.
    #                         # Con esto NO ralentizamos el proceso de carga y es una forma eficiente de
    #                         # trabajar cargas masivas.
    #                         'fk_reserva_id': id,
    #                     }
    #                     lista_credito.append(credito)
    #                 #
    #                 if pago_realizado == 1 and tipo_pago == "Débito":
    #                     debito = {
    #                         'debito': 0,
    #                         'fecha_pago': ahora.strftime('%Y-%m-%d %H:%M:%S.%f'),
    #                         'debito_uuid': str(uuid.uuid4()),
    #                         'monto': precio_int,
    #                         'monto_total': precio_int,
    #                         # OJO; paraque nos pidauna instancia y no utilizar .get() que es mala práctica
    #                         # para efecto de este caso, la columna de la BD; fk_reserva,se le debe agregar el id
    #                         # al final y queda así; fk_reserva_id.
    #                         # Con esto NO ralentizamos el proceso de carga y es una forma eficiente de
    #                         # trabajar cargas masivas.
    #                         'fk_reserva_id': id,
    #                     }
    #                     lista_debito.append(debito)
    #             # Fuera del ciclo for.
    #             #df_credito = pd.DataFrame(lista_credito)
    #             instancias_credito = [CreditoModel(**reg) for reg in lista_credito]
    #             credito_creadas = CreditoModel.objects.bulk_create(instancias_credito, batch_size=1000)
    #             #df_debito = pd.DataFrame(lista_debito)
    #             instancias_debito = [DebitoModel(**reg) for reg in lista_debito]
    #             debito_creadas = DebitoModel.objects.bulk_create(instancias_debito, batch_size=1000)
    #             #
    #             self.stdout.write(self.style.SUCCESS(f"  ✅ Reservas pagadas con DÉBITO o CRÉDITO inyectadas con éxito."))
    #         else:
    #             self.stdout.write(self.style.WARNING("  ⚠️ No se generaron reservas válidas para insertar."))
    #     except Exception as e:
    #         self.stdout.write(self.style.ERROR(f"❌ Ocurrió un error inesperado: {e}"))

    # Método para insertar las reservas.
    def insertar_reserva_paciente_registrado(self, horarios_ocupados=None):
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
            listado_pacientes_ids = list(
                CustomersUsers.objects.filter(pacientemodel__isnull=False)
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

            # Conjunto para controlar horarios únicos por doctor
            horarios_ocupados = set()
            objetivo = 34000

            # Realizamos los registros para los INSERT MASIVOS.
            while len(listas_reservas) < objetivo:

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

                reser_anulada = random.choice([1, 0])
                reser_confirmada = 0 if reser_anulada == 1 else 1

                # Elegimos el Doctor y sus datos
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

                ahora = datetime.now()
                dias_en_el_futuro = random.randint(0, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_en_el_futuro)
                fecha_formateada = objeto_fecha_reserva.date()

                # ================================================================
                # BUSCADOR DE HORARIOS DISPONIBLES PARA EL DOCTOR
                # ================================================================
                hora_encontrada = False
                intentos_hora = 0

                # Intentaremos un máximo de 15 veces buscar una hora libre para este doctor en este día.
                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")

                    # Estructuramos la clave única
                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    # Si NO está en nuestro set, significa que la agenda está libre a esa hora
                    if clave_reserva not in horarios_ocupados:
                        horarios_ocupados.add(clave_reserva)
                        objeto_hora_termino = objeto_hora_inicio + timedelta(hours=1)
                        hora_encontrada = True
                        # Rompe el ciclo while interno de inmediato porque encontramos hora libre
                        break

                    intentos_hora += 1

                # Si tras 15 intentos el doctor está colapsado en ese día, saltamos a elegir otro doctor
                if not hora_encontrada:
                    continue
                # ================================================================

                # Pasamos los datos seguros al diccionario (ya garantizados sin colisiones)
                datos_reservas = {
                    "fecha_creacion_reserva": datetime.now().strftime("%Y-%m-%d"),
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
                    "fk_usuario": random.choice(listado_pacientes_ids),
                }

                listas_reservas.append(datos_reservas)

            # INSERCCIÓN RESERVAS MASIVA FINAL CON PANDAS (El resto de tu código queda idéntico)
            if listas_reservas:
                instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
                reservas_creadas = ReservaModel.objects.bulk_create(
                    instancias_reserva, batch_size=1000
                )

                uuids_creados = [r["reserva_uuid"] for r in listas_reservas]
                reservas = list(
                    ReservaModel.objects.filter(
                        reserva_uuid__in=uuids_creados
                    ).values_list("id", "tipo_pago", "pago_realizado", "especialidad")
                )

                dict_especialidades = {
                    e.nombre_especialidad: e for e in Especialidad.objects.all()
                }

                for id, tipo_pago, pago_realizado, especialidad in reservas:
                    valor_especialidad = dict_especialidades.get(especialidad)
                    if not valor_especialidad:
                        continue

                    precio_int = int(valor_especialidad.valor_especialidad)

                    if pago_realizado == 1 and tipo_pago == "Crédito":
                        cant_cuotas = random.choice([3, 6, 9])
                        monto_cuotas = math.ceil(precio_int / cant_cuotas)
                        credito = {
                            "credito": 1,
                            "fecha_pago": ahora.strftime("%Y-%m-%d %H:%M:%S.%f"),
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
                            "fecha_pago": ahora.strftime("%Y-%m-%d %H:%M:%S.%f"),
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
                        f"  ✅ Reservas pagadas con DÉBITO o CRÉDITO inyectadas con éxito."
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
        # 1. Traemos las reservas. 'nombre_completo_medico' debe coincidir con el campo de texto en ReservaModel
        reservas = list(
            ReservaModel.objects.values_list(
                "id",
                "reserva_cerrada",
                "reserva_uuid",
                "fk_usuario_id",
                "nombre_doctor",
            )
        )

        # Extraemos primer_nombre, segundo_nombre, ap_paterno, ap_materno y el nombre de la especialidad asociada
        medicos_con_especialidades = DoctorModel.objects.values_list(
            "primer_nombre",
            "segundo_nombre",
            "ap_paterno",
            "ap_materno",
            # Sigue la relación ManyToMany de mi tabla DoctorModel.
            "especialidades__nombre_especialidad",
        )

        # Construimos el diccionario usando el formato "PrimerNombre SegundoNombre ApellidoPaterno ApellidoMaterno"
        mapa_medico_especialidad = {}
        for (
            primer_nombre,
            segundo_nombre,
            ap_paterno,
            ap_materno,
            nombre_esp,
        ) in medicos_con_especialidades:
            # Validamos que los campos no sean None antes de concatenar y aplicar strip para los espacios
            # en blanco.
            p_nombre = primer_nombre if primer_nombre else ""
            s_nombre = segundo_nombre if segundo_nombre else ""
            ape_paterno = ap_paterno if ap_paterno else ""
            ape_materno = ap_materno if ap_materno else ""
            # Acá sola concatenamos el nombre de Doctor y qutamos los espacios en blanco
            # para luego utilizarlo.
            nombre_completo = (
                f"{p_nombre} {s_nombre} {ape_paterno} {ape_materno}".strip()
            )
            # Agregamosun nuevo elemento a la lista, en este caso, nombre_completo.
            mapa_medico_especialidad[nombre_completo] = nombre_esp
        print("Medico Especialidad")
        # Ejemplo de lo que obtenemos en esta parte. Nombre del doctor y la especialidad aignada.
        # {'Yolanda Carlos Rubilar Hurtado': 'Traumatología', 'Sonia Sergio Soto Gallardo': 'Nutrición'}
        print(mapa_medico_especialidad)
        # Obtenemos el IDs del PACIENTE y además su FK del Usuario.
        mapa_pacientes_raw = PacienteModel.objects.values_list("id", "fk_user_id")
        # diccionario_pacientes Ej: [(18469, 45), (18470, 46), (18471, 47)]
        # Si tienes que recorrer miles de filas (por ejemplo, 5.000 reservas) y por cada reserva necesitas
        # averiguar a qué ID de paciente corresponde el usuario, nunca debes hacer una consulta a la base
        # de datos dentro del for.
        # Mal escenario (Consulta por ciclo): 5.000 vueltas = 5.000 consultas a la base de datos.
        # El script tardará minutos en terminar o se congelará.
        # Buen escenario (Tu código): Haces una sola consulta al principio,
        # armas el diccionario_pacientes en un milisegundo, y luego el for consulta la memoria RAM.
        # El script termina en 2 segundos.
        diccionario_pacientes = {
            fk_user: id_paciente for id_paciente, fk_user in mapa_pacientes_raw
        }
        # Creamos la lista para almacenar el objeto de historial_clinico.
        historial_pac_registrado = []

        # Procesamos el bucle de las reservas de forma limpia
        for id, reserva_cerrada, reserva_uuid, fk_usuario_id, nombre_doctor in reservas:

            # Solo historiales para citas completadas/cerradas
            if reserva_cerrada == 0:
                continue

            # Obtenemos el ID numérico del paciente.
            id_paciente_real = diccionario_pacientes.get(fk_usuario_id)
            print(id_paciente_real)
            if id_paciente_real is None:
                continue

            # Buscamos la especialidad usando el el nombre del doctor.
            # Reserva y es texto.
            medico_limpio = nombre_doctor.strip() if nombre_doctor else ""
            # Si por defecto no lo encentra, se asigna la especialidad; "Medicina General".
            nombre_especialidad = mapa_medico_especialidad.get(
                medico_limpio, "Medicina General"
            )
            print("nombre_especialidad-------------------------")
            print(nombre_especialidad)

            # Llamamos al método que creamos en nuestro archivo providres.py.
            # Pasamos el nombre_especialidad como parámetro.
            datos_medicos = fake.historial_por_especialidad(nombre_especialidad)

            # Armamos el registro estructurado usando el ID entero.
            dato_historial = {
                "fecha_creacion_historial": datetime.now().strftime("%Y-%m-%d"),
                # Pasamos el nombre de la especialidad del diccionario que se encuentra en el archivo providers.py
                "diagnostico": datos_medicos["diagnostico"],
                "sintoma": datos_medicos["sintoma"],
                "observacion": datos_medicos["observacion"],
                "reserva_uuid": reserva_uuid,
                "fk_paciente_id": id_paciente_real,  # ID numérico entero listo
            }
            # Guardamos en nuestra lista.
            historial_pac_registrado.append(dato_historial)
        # En caso de error.
        if not historial_pac_registrado:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No se encontraron historiales aptos para insertar."
                )
            )
            return
        # Creamos el DataFrame para la insercción masiva en la BD.
        # df_historial = pd.DataFrame(historial_pac_registrado)
        instancias_historial = [
            HistorialClinicoModel(**reg) for reg in historial_pac_registrado
        ]
        # Realizamos el insert a la BD.
        HistorialClinicoModel.objects.bulk_create(instancias_historial, batch_size=1000)
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES REGISTRADOS inyectados con coherencia total."
            )
        )

    # Método para insertar a PACIENTES NO REGISTRADOS.
    def insertar_paciente_no_registrado(self):
        #
        self.stdout.write(
            self.style.SUCCESS("  ✅ Método para insertar a Pacientes NO REGISTRADOS.")
        )
        # Generamos la instancia de Faker.
        generador_faker = Faker("es_CL")

        # Inicializamos las listas.
        lista_paciente_data = []

        # Creamos la cantidad de pac no registrado a poblar.
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

                # Generamos datos de acceso únicos como e username y gmail a partir de los nombres y apellidos.
                primer_nombre_corto = primer_nombre_paciente[:3].lower()
                ap_paterno_corto = ap_paterno_paciente[:3].lower()
                username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                email = f"{username_paciente}@gmail.com"

                # Creamos los datos del PACIENTE NO REGISTRADOS.
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
                # Volvemos a agregar los datos a la lista.
                lista_paciente_data.append(data_paciente_no_registrado)
            else:
                primer_nombre_paciente = generador_faker.first_name_male()
                segundo_nombre_paciente = generador_faker.first_name_male()
                ap_paterno_paciente = generador_faker.last_name()
                ap_materno_paciente = generador_faker.last_name()
                edad_paciente = edad
                sexo_paciente = "F"
                telefono_paciente = (
                    f"+56 9{generador_faker.random_int(min=10000000, max=99999999)}"
                )
                # Generamos datos de acceso únicos como e username y gmail a partir de los nombres y apellidos.
                primer_nombre_corto = primer_nombre_paciente[:3].lower()
                ap_paterno_corto = ap_paterno_paciente[:3].lower()
                username_paciente = f"{primer_nombre_corto}{ap_paterno_corto}_{i}_{generador_faker.random_int(100,999)}"
                email = f"{username_paciente}@gmail.com"

                # Creamos losdatos del PACIENTE NO REGISTRADOS.
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
                # Volvemos a agregar los datos a la lista.
                lista_paciente_data.append(data_paciente_no_registrado)
        # INSERCIÓN EN LA BASE DE DATOS.
        # Creamos DataFrame con los datos de las listas.
        # df_pac_no_registrado = pd.DataFrame(lista_paciente_data)
        # Convertimos la lista a diccionario e instanciamos su modelo.
        instancias_paciente = [
            PacienteNoRegisterModel(**reg) for reg in lista_paciente_data
        ]
        # Realizamos el insert.
        # Acá obtenemos los id incertados de los pacientes.
        PacienteNoRegisterModel.objects.bulk_create(
            instancias_paciente, batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS("  ✅ PACIENTE NO REGISTRADO INSERTADOS CORRECTAMENTE")
        )

    # Método para insertar las reservas.
    def insertar_reserva_paciente_no_registrado(self, horarios_ocupados=None):
        try:
            #
            self.stdout.write(
                self.style.SUCCESS("  ✅ Método Insertar las Reservas Iniciando.......")
            )
            if horarios_ocupados is None:
                horarios_ocupados = set()
            # Como este es una INSERCCIÓN MASIVA, no es buena práctica utilizar el metodo all y recorrer todo en
            # un for, esto sería interminable y a su vez lento, es un trabajo ineficiente para la insercción masiva.
            # Enotnces lo que debemos hacer, es obtener ese objeto de los modelos y convertirlo de inmediato a lista.
            # En esta lista solo guardamos los IDs necesarios.
            listado_doctores = list(
                DoctorModel.objects.prefetch_related(
                    "doctor_clinica", "especialidades"
                ).all()
            )
            # print(listado_pacientes_ids)
            listado_clinicas = list(
                ComunaClinicaModel.objects.values_list(
                    "id", "nombre_clinica", "comuna_clinica", "direccion_clinica"
                )
            )
            # print(listado_clinicas)
            # Para las especialidades, si necesitas el nombre y el valor, podemos traer el QuerySet completo
            especialidades = list(
                Especialidad.objects.values_list(
                    "id", "nombre_especialidad", "valor_especialidad"
                )
            )
            # print(especialidades)
            # IDs de los pacientes REGISTRADOS.
            paciente_registrado = list(
                PacienteNoRegisterModel.objects.values_list("id", flat=True)
            )
            # Elegimos un Doctor al azar de la memoria.
            listas_reservas = []
            lista_debito = []
            lista_credito = []
            # Conjunto para controlar horarios únicos por doctor
            horarios_ocupados = set()
            objetivo = 34000
            # Realizamos los registros para los INSERT MASIVOS.
            while len(listas_reservas) < objetivo:
                #
                tipo_pago = ""
                pago_realizado = 0
                #
                reserva_cerrada = random.choice([1, 0])
                #
                if reserva_cerrada == 1:
                    #
                    tipo_pago = random.choice(["Crédito", "Débito"])
                    pago_realizado = 1
                #
                if reserva_cerrada == 0:
                    tipo_pago = random.choice(["Crédito", "Débito", ""])
                    #
                    if tipo_pago == "":
                        pago_realizado = 0
                    if tipo_pago != "":
                        pago_realizado = 1
                #
                reser_anulada = random.choice([1, 0])
                reser_confirmada = 0
                if reser_anulada == 1:
                    reser_confirmada = 0
                if reser_anulada == 0:
                    reser_confirmada = 1
                # Elegimos un Doctor al azar de la lista que tenemos en memoria
                doctor = random.choice(listado_doctores)
                nombre_completo_doctor = f"{doctor.primer_nombre} {doctor.segundo_nombre} {doctor.ap_paterno} {doctor.ap_materno}"

                # Extraemos las clínicas asociadas a este doctor desde la memoria ram (gracias al prefetch_related)
                clinicas_del_doctor = list(doctor.doctor_clinica.all())
                if not clinicas_del_doctor:
                    continue  # Si este doctor no tiene clínicas asignadas, saltamos al siguiente

                # Elegimos una clínica válida para el doctor (Este es un objeto completo del modelo)
                clinica_elegida = random.choice(clinicas_del_doctor)

                # Extraemos las especialidades reales del doctor
                especialidades_del_doctor = list(doctor.especialidades.all())
                if not especialidades_del_doctor:
                    continue  # Si el doctor no tiene especialidades registradas, saltamos

                # Elegimos una especialidad válida para el doctor (Objeto completo del modelo)
                especialidad_elegida = random.choice(especialidades_del_doctor)

                # Obtenemos la Fecha y Hora actual.
                ahora = datetime.now()
                # Crea días en el futuro, esto para utilizar varias fechas de reservas a futuro.
                # Genera un número entero aleatorio entre 0 y 30.
                # Ese número representa cuántos días hacia adelante se moverá la fecha.
                # Ejemplo: dias_en_el_futuro = 12
                ahora = datetime.now()
                dias_en_el_futuro = random.randint(0, 90)
                objeto_fecha_reserva = ahora + timedelta(days=dias_en_el_futuro)
                fecha_formateada = objeto_fecha_reserva.date()
                # ================================================================
                hora_encontrada = False
                intentos_hora = 0

                # Intentaremos un máximo de 15 veces buscar una hora libre para este doctor en este día.
                while intentos_hora < 15:
                    hora_random = random.randint(8, 22)
                    objeto_hora_inicio = datetime.strptime(f"{hora_random}:00", "%H:%M")
                    hora_inicio_str = objeto_hora_inicio.strftime("%H:%M:%S")

                    # Estructuramos la clave única
                    clave_reserva = (doctor.id, fecha_formateada, hora_inicio_str)

                    # Si NO está en nuestro set, significa que la agenda está libre a esa hora
                    if clave_reserva not in horarios_ocupados:
                        horarios_ocupados.add(clave_reserva)
                        objeto_hora_termino = objeto_hora_inicio + timedelta(hours=1)
                        hora_encontrada = True
                        # Rompe el ciclo while interno de inmediato porque encontramos hora libre
                        break

                    intentos_hora += 1

                # Si tras 15 intentos el doctor está colapsado en ese día, saltamos a elegir otro doctor
                if not hora_encontrada:
                    continue
                # ================================================================
                # Pasamos los datos al diccionario.
                datos_reservas = {
                    "fecha_creacion_reserva": datetime.now().strftime("%Y-%m-%d"),
                    "usuario_creacion_reserva": "Admin",
                    "fecha_reserva": objeto_fecha_reserva.date(),
                    # Formateamos como String estricto para evitar transformaciones raras de Pandas.
                    # Dará "10:00:00"
                    "hora_inicio": objeto_hora_inicio.strftime("%H:%M:%S"),
                    # Dará "11:00:00"
                    "hora_termino": objeto_hora_termino.strftime("%H:%M:%S"),
                    # Accedemos de forma segura mediante objetos (.nombre_especialidad, .nombre_clinica)
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
                    # Asignamos el ID directo del paciente a la columna FK física
                    "fk_pac_no_register_id": random.choice(paciente_registrado),
                    "fk_usuario_id": None,
                }
                #
                listas_reservas.append(datos_reservas)

            # INSERCCIÓN RESERVAS MASIVA FINAL.
            if listas_reservas:
                print("Ingresamos a la RESERVA DEL PACIENTE NO REGISTRADO.")
                # df_reservas = pd.DataFrame(listas_reservas)
                instancias_reserva = [ReservaModel(**reg) for reg in listas_reservas]
                reservas_creadas = ReservaModel.objects.bulk_create(
                    instancias_reserva, batch_size=1000
                )

                # Extraemos los UUIDs que acabamos de crear en este método para pacientes no registrados.
                # Esta línea de código es una Comprensión de Listas (List Comprehension) en Python.
                # Su objetivo es extraer de forma masiva y ultra rápida todos los identificadores
                # únicos (reserva_uuid) de las reservas que se acaban de generar.
                # guardándolos en una lista limpia y plana.
                uuids_creados = [r["reserva_uuid"] for r in listas_reservas]

                # Filtramos para traer SOLO las reservas.
                reservas = list(
                    ReservaModel.objects.filter(
                        reserva_uuid__in=uuids_creados
                    ).values_list("id", "tipo_pago", "pago_realizado", "especialidad")
                )
                # La variable e representa a un objeto Especialidad completo (con su id, su nombre, su valor, etc.).
                # dict_especialidades = {
                #     "Odontología": <Objeto Especialidad Completo (id=1, valor=30000)>,
                #     "Cardiología": <Objeto Especialidad Completo (id=2, valor=45000)>,
                #     "Pediatría":   <Objeto Especialidad Completo (id=3, valor=35000)>
                # }
                dict_especialidades = {
                    e.nombre_especialidad: e for e in Especialidad.objects.all()
                }
                #
                for id, tipo_pago, pago_realizado, especialidad in reservas:
                    print("Ingresamos a la lista de la RESERVA")
                    valor_especialidad = dict_especialidades.get(especialidad)
                    if not valor_especialidad:
                        continue
                    #
                    valor_especialidad = Especialidad.objects.get(
                        nombre_especialidad=especialidad
                    )
                    # id = ReservaModel.objects.get(pk=id)
                    #
                    precio_int = int(valor_especialidad.valor_especialidad)
                    #
                    if pago_realizado == 1 and tipo_pago == "Crédito":
                        cant_cuotas = random.choice([3, 6, 9])
                        monto_cuotas = None
                        if cant_cuotas == 3:
                            monto_cuotas = math.ceil(int(precio_int) / 3)
                        if cant_cuotas == 6:
                            monto_cuotas = math.ceil(int(precio_int) / 6)
                        if cant_cuotas == 9:
                            monto_cuotas = math.ceil(int(precio_int) / 9)
                        credito = {
                            "credito": 1,
                            "fecha_pago": ahora.strftime("%Y-%m-%d %H:%M:%S.%f"),
                            "credito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "cant_cuotas": cant_cuotas,
                            "monto_total": precio_int,
                            "monto_cuotas": monto_cuotas,
                            # OJO; para que no nos pida una instancia y no utilizar .get() que es mala práctica
                            # para efecto de este caso, la columna de la BD; fk_reserva,se le debe agregar el id
                            # al final y queda así; fk_reserva_id.
                            # Con esto NO ralentizamos el proceso de carga y es una forma eficiente de
                            # trabajar cargas masivas.
                            "fk_reserva_id": id,
                        }
                        lista_credito.append(credito)
                    #
                    if pago_realizado == 1 and tipo_pago == "Débito":
                        debito = {
                            "debito": 0,
                            "fecha_pago": ahora.strftime("%Y-%m-%d %H:%M:%S.%f"),
                            "debito_uuid": str(uuid.uuid4()),
                            "monto": precio_int,
                            "monto_total": precio_int,
                            # OJO; paraque nos pidauna instancia y no utilizar .get() que es mala práctica
                            # para efecto de este caso, la columna de la BD; fk_reserva,se le debe agregar el id
                            # al final y queda así; fk_reserva_id.
                            # Con esto NO ralentizamos el proceso de carga y es una forma eficiente de
                            # trabajar cargas masivas.
                            "fk_reserva_id": id,
                        }
                        lista_debito.append(debito)
                # Fuera del ciclo for.
                # df_credito = pd.DataFrame(lista_credito)
                instancias_credito = [CreditoModel(**reg) for reg in lista_credito]
                credito_creadas = CreditoModel.objects.bulk_create(
                    instancias_credito, batch_size=1000
                )
                # df_debito = pd.DataFrame(lista_debito)
                instancias_debito = [DebitoModel(**reg) for reg in lista_debito]
                debito_creadas = DebitoModel.objects.bulk_create(
                    instancias_debito, batch_size=1000
                )
                #
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ Reservas pagadas con DÉBITO o CRÉDITO inyectadas con éxito PACIENTE NO REGISTRADO."
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
    def insertar_historial_paciente_no_registrado(self):
        # Traemos las reservas. 'nombre_completo_medico' debe coincidir con el campo de texto en ReservaModel
        reservas = list(
            ReservaModel.objects.values_list(
                "id",
                "reserva_cerrada",
                "reserva_uuid",
                "fk_pac_no_register_id",
                "nombre_doctor",
            )
        )

        # Extraemos primer_nombre, segundo_nombre, ap_paterno, ap_materno y el nombre de la especialidad asociada
        medicos_con_especialidades = DoctorModel.objects.values_list(
            "primer_nombre",
            "segundo_nombre",
            "ap_paterno",
            "ap_materno",
            # Sigue la relación ManyToMany de mi tabla DoctorModel.
            "especialidades__nombre_especialidad",
        )

        # Construimos el diccionario usando el formato "PrimerNombre SegundoNombre ApellidoPaterno ApellidoMaterno"
        mapa_medico_especialidad = {}
        for (
            primer_nombre,
            segundo_nombre,
            ap_paterno,
            ap_materno,
            nombre_esp,
        ) in medicos_con_especialidades:
            # Validamos que los campos no sean None antes de concatenar y aplicar strip para los espacios
            # en blanco.
            p_nombre = primer_nombre if primer_nombre else ""
            s_nombre = segundo_nombre if segundo_nombre else ""
            ape_paterno = ap_paterno if ap_paterno else ""
            ape_materno = ap_materno if ap_materno else ""
            # Acá sola concatenamos el nombre de Doctor y qutamos los espacios en blanco
            # para luego utilizarlo.
            nombre_completo = (
                f"{p_nombre} {s_nombre} {ape_paterno} {ape_materno}".strip()
            )
            # Agregamosun nuevo elemento a la lista, en este caso, nombre_completo.
            mapa_medico_especialidad[nombre_completo] = nombre_esp
        print("Medico Especialidad")
        # Ejemplo de lo que obtenemos en esta parte. Nombre del doctor y la especialidad aignada.
        # {'Yolanda Carlos Rubilar Hurtado': 'Traumatología', 'Sonia Sergio Soto Gallardo': 'Nutrición'}
        print(mapa_medico_especialidad)
        # Obtenemos el IDs del PACIENTE y además su FK del Usuario.
        mapa_pacientes_raw = PacienteNoRegisterModel.objects.values_list(
            "id", flat=True
        )
        # diccionario_pacientes Ej: [(18469, 45), (18470, 46), (18471, 47)]
        # Si tienes que recorrer miles de filas (por ejemplo, 5.000 reservas) y por cada reserva necesitas
        # averiguar a qué ID de paciente corresponde el usuario, nunca debes hacer una consulta a la base
        # de datos dentro del for.
        # Mal escenario (Consulta por ciclo): 5.000 vueltas = 5.000 consultas a la base de datos.
        # El script tardará minutos en terminar o se congelará.
        # Buen escenario (Tu código): Haces una sola consulta al principio,
        # armas el diccionario_pacientes en un milisegundo, y luego el for consulta la memoria RAM.
        # El script termina en 2 segundos.
        diccionario_pacientes = {
            id_paciente: id_paciente for id_paciente in mapa_pacientes_raw
        }
        # Creamos la lista para almacenar el objeto de historial_clinico.
        historial_pac_no_registrado = []

        # Procesamos el bucle de las reservas de forma limpia
        for (
            id,
            reserva_cerrada,
            reserva_uuid,
            fk_pac_no_register_id,
            nombre_doctor,
        ) in reservas:

            # Solo historiales para citas completadas/cerradas
            if reserva_cerrada == 0:
                continue

            # Obtenemos el ID numérico del paciente.
            id_paciente_real = diccionario_pacientes.get(fk_pac_no_register_id)
            print(id_paciente_real)
            if id_paciente_real is None:
                continue

            # Buscamos la especialidad usando el el nombre del doctor.
            # Reserva y es texto.
            medico_limpio = nombre_doctor.strip() if nombre_doctor else ""
            # Si por defecto no lo encentra, se asigna la especialidad; "Medicina General".
            nombre_especialidad = mapa_medico_especialidad.get(
                medico_limpio, "Medicina General"
            )
            print("nombre_especialidad-------------------------")
            print(nombre_especialidad)

            # Llamamos al método que creamos en nuestro archivo providres.py.
            # Pasamos el nombre_especialidad como parámetro.
            datos_medicos = fake.historial_por_especialidad(nombre_especialidad)

            # Armamos el registro estructurado usando el ID entero.
            dato_historial = {
                "fecha_historial": datetime.now().strftime("%Y-%m-%d"),
                # Pasamos el nombre de la especialidad del diccionario que se encuentra en el archivo providers.py
                "diagnostico": datos_medicos["diagnostico"],
                "sintoma": datos_medicos["sintoma"],
                "observacion": datos_medicos["observacion"],
                "reserva_uuid": reserva_uuid,
                "fk_pac_no_registrado_id": id_paciente_real,
            }
            # Guardamos en nuestra lista.
            historial_pac_no_registrado.append(dato_historial)
        # En caso de error.
        if not historial_pac_no_registrado:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No se encontraron historiales aptos para insertar."
                )
            )
            return

        # Creamos el DataFrame para la insercción masiva en la BD.
        df_historial = pd.DataFrame(historial_pac_no_registrado)
        print(df_historial)
        instancias_historial = [
            HistorialPacNoRegistradoModel(**reg)
            for reg in df_historial.to_dict("records")
        ]
        # Realizamos el insert a la BD.
        HistorialPacNoRegistradoModel.objects.bulk_create(
            instancias_historial, batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS(
                "  ✅ HISTORIAL CLÍNICO DE PACIENTES NO REGISTRADOS inyectados con coherencia total."
            )
        )
