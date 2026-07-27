import re
import json
import requests
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from reserva.models import ReservaModel
from paciente_no_registrado.models import PacienteNoRegisterModel
from paciente_no_registrado.validar_rut import validar_rut
from doctor.models import DoctorModel
from especialidad.models import Especialidad
from comuna_clinica.models import ComunaClinicaModel
from datetime import datetime, timedelta

# ========== DICCIONARIO PARA GUARDAR ESTADOS ==========
estados_conversacion = {}


def extraer_codigo(mensaje):
    """
    Extrae un UUID del mensaje del usuario.
    Busca un patrón de UUID: 8-4-4-4-12 caracteres hexadecimales
    """
    patron_uuid = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    match = re.search(patron_uuid, mensaje, re.IGNORECASE)
    if match:
        return match.group()
    return None


# Configuración de la URL y el modelo de DeepSeek.
def llamar_deepseek(prompt, model="deepseek-r1:7b"):
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0},
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=350)
        data = response.json()
        contenido = data["message"]["content"]

        json_match = re.search(r"\{.*\}", contenido, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return contenido.strip()
    except Exception as e:
        print(f"Error llamando a DeepSeek: {e}")
        return None


# ========== PROMPT 1: CLASIFICAR INTENCIÓN ==========
def clasificar_intencion(mensaje):
    prompt = f"""
        Eres un asistente de una clínica médica. Clasifica la intención del usuario en una de estas opciones:

        - "anular_reserva": el usuario quiere cancelar, anular o eliminar su cita
        - "informacion_reserva": el usuario quiere saber información de su cita, consultar o ver el estado de su reserva
        - "consultar_doctor": el usuario pregunta por doctores o especialidades
        - "consultar_clinica": el usuario pregunta por clínicas o ubicaciones
        - "solicitar_reserva": el usuario quiere agendar, reservar o pedir una nueva cita/hora médica
        - "otro": no encaja en ninguna de las anteriores

        Devuelve SOLO UN JSON con el formato:
        {{"intencion": "opcion_elegida"}}

        Mensaje del usuario: "{mensaje}"
    """
    resultado = llamar_deepseek(prompt)
    if resultado and isinstance(resultado, dict):
        return resultado.get("intencion", "otro")
    return "otro"


# ========== PROMPT 2: EXTRAER ENTIDADES ==========
def extraer_entidades(mensaje, intencion):
    prompt = f"""
        Eres un asistente de una clínica. Extrae los datos importantes del mensaje del usuario.

        Intención detectada: {intencion}

        Extrae SOLO los campos relevantes según la intención:
        - Si es "anular_reserva" o "informacion_reserva": extrae "codigo" (código de reserva / UUID)
        - Si es "consultar_doctor": extrae "especialidad" o "nombre_doctor"
        - Si es "consultar_clinica": extrae "nombre_clinica" o "comuna"
        - Si es "solicitar_reserva": extrae "especialidad" si la menciona

        Devuelve SOLO UN JSON con las entidades encontradas.
        Si no encuentra ninguna, devuelve {{}}.

        Mensaje del usuario: "{mensaje}"
    """
    resultado = llamar_deepseek(prompt)

    # Asegurar extracción de código por Expresión Regular si DeepSeek no lo detecta
    if intencion in ["anular_reserva", "informacion_reserva"]:
        codigo_regex = extraer_codigo(mensaje)
        if codigo_regex:
            if not isinstance(resultado, dict):
                resultado = {}
            resultado["codigo"] = codigo_regex

    if resultado and isinstance(resultado, dict):
        return resultado
    return {}


# ========== PROMPT 3: GENERAR RESPUESTA ==========
def generar_respuesta(intencion, entidades, estado=None):
    if intencion == "anular_reserva":
        if "codigo" in entidades:
            return f"✅ Procesando anulación de la reserva con código {entidades['codigo']}... Dame un momento."
        else:
            return "🔑 Para anular tu reserva, necesito el código de reserva. Por favor, escríbelo a continuación."

    elif intencion == "informacion_reserva":
        if "codigo" in entidades:
            return f"🔍 Buscando información de la reserva con código {entidades['codigo']}..."
        else:
            return "🔍 Para consultar tu reserva, necesito el código de reserva. Por favor, escríbelo a continuación."

    elif intencion == "consultar_doctor":
        especialidad = entidades.get("especialidad", "")
        nombre = entidades.get("nombre_doctor", "")
        if especialidad:
            return f"👨‍⚕️ Buscando doctores en la especialidad de {especialidad}..."
        elif nombre:
            return f"👨‍⚕️ Buscando información del Dr. {nombre}..."
        else:
            return "👨‍⚕️ ¿Qué especialidad o doctor estás buscando?"

    elif intencion == "consultar_clinica":
        nombre = entidades.get("nombre_clinica", "")
        comuna = entidades.get("comuna", "")
        if nombre:
            return f"🏥 Buscando información de {nombre}..."
        elif comuna:
            return f"🏥 Buscando clínicas en {comuna}..."
        else:
            return "🏥 ¿Qué clínica o comuna te interesa?"

    elif intencion == "solicitar_reserva":
        return "📝 ¡Con gusto te ayudo a agendar una hora! Para comenzar, indícame tu RUT (formato: 12345678-9):"

    else:
        return "👋 Hola, ¿cómo puedo ayudarte? Puedo consultar tu reserva, anular una cita o darte información de doctores y clínicas."


# ========== PROMPT 4: PROCESAR CÓDIGO ==========
def procesar_codigo_reserva(mensaje, session_id):
    codigo = extraer_codigo(mensaje)
    if not codigo:
        codigo = mensaje.strip()
        print(f"No se encontró UUID, usando mensaje completo: {codigo}")

    print(f"Código a buscar: {codigo}")
    try:
        reserva = ReservaModel.objects.get(reserva_uuid=codigo)
        return {"existe": True, "codigo": codigo, "reserva": reserva}
    except ReservaModel.DoesNotExist:
        return {"existe": False, "codigo": codigo, "reserva": None}


# ========== VALIDADORES DE CAMPOS ==========
def validar_solo_numeros(texto):
    return texto.strip().isdigit()


def validar_sexo(texto):
    return texto.strip().upper() in ["M", "F"]


def validar_email(email):
    patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron_email, email.strip()) is not None


def validar_fecha(fecha_str):
    try:
        datetime.strptime(fecha_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_hora(hora_str):
    try:
        datetime.strptime(hora_str.strip(), "%H:%M")
        return True
    except ValueError:
        return False


def validar_hora_completa(hora_str):
    try:
        hora_dt = datetime.strptime(hora_str.strip(), "%H:%M")
        return hora_dt.minute == 0
    except ValueError:
        return False


def validar_seleccion(texto, opciones):
    try:
        idx = int(texto.strip()) - 1
        return 0 <= idx < len(opciones)
    except ValueError:
        return False


VALIDADORES_CAMPOS = {
    "edad": validar_solo_numeros,
    "sexo": validar_sexo,
    "rut": validar_rut,
    "fono": validar_solo_numeros,
    "email": validar_email,
    "fecha_reserva": validar_fecha,
    "hora_inicio": validar_hora_completa,
}


# ========== DETECCIÓN DE INTENCIÓN: SOLICITAR NUEVA RESERVA ==========
def es_solicitud_nueva_reserva(mensaje):
    """
    Detecta de forma estricta si el usuario solicita agendar una NUEVA reserva/cita.
    Evita activarse si el mensaje busca consultar o saber información.
    """
    mensaje_lower = mensaje.lower()

    # Si busca información o consulta, NUNCA es una solicitud de agendamiento
    palabras_consulta = [
        "saber",
        "informacion",
        "información",
        "consultar",
        "ver",
        "estado",
        "anular",
        "cancelar",
        "codigo",
        "código",
    ]
    if any(p in mensaje_lower for p in palabras_consulta):
        return False

    frases_clave = [
        "quiero solicitar una reserva",
        "quiero pedir una hora",
        "quiero agendar",
        "quiero una reserva",
        "quiero una cita",
        "solicitar reserva",
        "solicitar una hora",
        "pedir hora",
        "pedir una cita",
        "agendar hora",
        "agendar cita",
        "agendar una reserva",
        "reservar hora",
        "reservar una hora",
        "necesito una reserva",
        "necesito una cita",
        "necesito pedir una hora",
        "necesito agendar",
        "reservar una cita",
        "hacer una reserva",
        "hacer una cita",
        "tomar una hora",
        "tomar una cita",
        "requiero una reserva",
        "requiero una cita",
        "quisiera hacer una reserva",
        "quisiera agendar",
        "quisiera una cita",
        "quisiera una hora",
        "necesito una hora médica",
        "quiero una hora médica",
        "reservar una hora médica",
        "solicitar una hora médica",
        "pedir una hora médica",
        "agendar una hora médica",
        "me gustaría reservar",
        "me gustaría agendar",
        "deseo reservar",
        "deseo agendar",
        "quiero reservar",
        "necesito reservar",
        "realizar una reserva",
        "tomar una reserva",
        "sacar una hora",
        "sacar una cita",
        "pedir una reserva",
        "solicitar una cita",
        "nueva reserva",
        "nueva cita",
        "nueva hora",
    ]

    tiene_reserva = any(p in mensaje_lower for p in ["reserva", "cita", "hora"])
    tiene_verbo_agendar = any(
        p in mensaje_lower
        for p in ["agendar", "solicitar", "pedir", "reservar", "tomar", "sacar"]
    )

    return any(frase in mensaje_lower for frase in frases_clave) or (
        tiene_reserva and tiene_verbo_agendar
    )


# ========== WIZARD: PASOS PARA RECOLECTAR DATOS ==========
PASOS_PACIENTE = [
    ("reg_primer_nombre", "primer_nombre", "😊 ¿Cuál es tu primer nombre?"),
    (
        "reg_segundo_nombre",
        "segundo_nombre",
        "¿Cuál es tu segundo nombre? (si no tienes, escribe 'ninguno')",
    ),
    ("reg_ap_paterno", "ap_paterno", "¿Cuál es tu apellido paterno?"),
    ("reg_ap_materno", "ap_materno", "¿Cuál es tu apellido materno?"),
    ("reg_edad", "edad", "¿Cuál es tu edad?"),
    ("reg_sexo", "sexo", "¿Cuál es tu sexo? (M/F)"),
    ("reg_fono", "fono", "📞 ¿Cuál es tu número de teléfono?"),
    ("reg_email", "email", "📧 ¿Cuál es tu correo electrónico?"),
]

PASOS_RESERVA = [
    ("res_especialidad", "especialidad", "🩺 ¿Qué especialidad médica necesitas?"),
    (
        "res_clinica",
        "clinica",
        "🏥 Estas son las clínicas disponibles para esa especialidad. Escribe el número de la que prefieras:",
    ),
    (
        "res_doctor",
        "nombre_doctor",
        "🧑‍⚕️ Estos son los doctores disponibles. Escribe el número del doctor que prefieras:",
    ),
    (
        "res_fecha",
        "fecha_reserva",
        "📅 ¿Qué fecha deseas para tu cita? (formato: AAAA-MM-DD)",
    ),
    (
        "res_hora_inicio",
        "hora_inicio",
        "⏰ ¿A qué hora inicia tu cita? (solo horas en punto, formato: HH:00, ej: 08:00, 09:00)",
    ),
]

PASOS_FLUJO_RESERVA_NO_REGISTRADO = (
    {"reg_rut", "res_confirmar"}
    | {paso for paso, _campo, _pregunta in PASOS_PACIENTE}
    | {paso for paso, _campo, _pregunta in PASOS_RESERVA}
)


# ========== CONSULTAS DE BASE DE DATOS Y FORMATEO ==========
def obtener_clinicas_por_especialidad(especialidad_nombre):
    try:
        especialidad = Especialidad.objects.get(nombre_especialidad=especialidad_nombre)
        doctores = DoctorModel.objects.filter(especialidades=especialidad)
        clinicas = ComunaClinicaModel.objects.filter(
            doctormodel__in=doctores
        ).distinct()
        return list(clinicas)
    except Especialidad.DoesNotExist:
        return []


def obtener_doctores_por_especialidad_y_clinica(especialidad_nombre, clinica_nombre):
    try:
        especialidad = Especialidad.objects.get(nombre_especialidad=especialidad_nombre)
        clinica = ComunaClinicaModel.objects.get(nombre_clinica=clinica_nombre)
        doctores = DoctorModel.objects.filter(
            especialidades=especialidad, doctor_clinica=clinica
        ).distinct()
        return list(doctores)
    except (Especialidad.DoesNotExist, ComunaClinicaModel.DoesNotExist):
        return []


def formatear_lista_opciones(elementos, *atributos):
    if not elementos:
        return "No hay opciones disponibles."
    lineas = []
    for i, elem in enumerate(elementos, 1):
        nombre = " ".join(str(getattr(elem, attr, "")) for attr in atributos).strip()
        if not nombre:
            nombre = str(elem)
        lineas.append(f"{i}. {nombre}")
    return "\n".join(lineas)


def crear_paciente_no_registrado_y_continuar(estado):
    datos = estado["datos_paciente"]
    try:
        nuevo_paciente = PacienteNoRegisterModel.objects.create(
            primer_nombre=datos.get("primer_nombre"),
            segundo_nombre=datos.get("segundo_nombre") or "",
            ap_paterno=datos.get("ap_paterno"),
            ap_materno=datos.get("ap_materno"),
            edad=int(datos.get("edad")),
            sexo=datos.get("sexo"),
            rut=datos.get("rut"),
            fono=datos.get("fono"),
            email=datos.get("email"),
            paciente_uuid=str(uuid.uuid4()),
        )
        estado["paciente_id"] = nuevo_paciente.id
        estado["paso"] = PASOS_RESERVA[0][0]
        return (
            f"✅ ¡Listo, {nuevo_paciente.primer_nombre}! Tu ficha ha sido creada correctamente.\n\n"
            f"Ahora sigamos con los datos de tu reserva.\n\n{PASOS_RESERVA[0][2]}"
        )
    except Exception as e:
        print(f"Error creando paciente no registrado: {e}")
        estado["paso"] = "inicio"
        estado["datos_paciente"] = {}
        estado["datos_reserva"] = {}
        estado["paciente_id"] = None
        return (
            "❌ Hubo un problema al guardar tus datos. Por favor, intenta nuevamente "
            "escribiendo 'quiero pedir una hora'."
        )


def verificar_disponibilidad_doctor(nombre_doctor, fecha_reserva, hora_inicio):
    try:
        existe_conflicto = ReservaModel.objects.filter(
            nombre_doctor=nombre_doctor,
            fecha_reserva=fecha_reserva,
            hora_inicio=hora_inicio,
            reser_anulada=0,
        ).exists()
        return not existe_conflicto
    except Exception as e:
        print(f"Error verificando disponibilidad del doctor: {e}")
        return False


def generar_resumen_confirmacion(estado):
    d = estado["datos_reserva"]
    return (
        "📋 Por favor confirma los datos de tu reserva:\n\n"
        f"- **Especialidad:** {d.get('especialidad')}\n"
        f"- **Clínica:** {d.get('nombre_clinica')}\n"
        f"- **Doctor/a:** {d.get('nombre_doctor')}\n"
        f"- **Fecha:** {d.get('fecha_reserva')}\n"
        f"- **Hora:** {d.get('hora_inicio')} - {d.get('hora_termino')}\n\n"
        "¿Confirmas estos datos? Responde 'Sí' para agendar o 'No' para cancelar."
    )


def finalizar_reserva_no_registrado(estado):
    d = estado["datos_reserva"]
    try:
        nueva_reserva = ReservaModel.objects.create(
            usuario_creacion_reserva="chatbot_paciente_no_registrado",
            fecha_reserva=d.get("fecha_reserva"),
            hora_inicio=d.get("hora_inicio"),
            hora_termino=d.get("hora_termino"),
            especialidad=d.get("especialidad"),
            nombre_doctor=d.get("nombre_doctor"),
            nombre_clinica=d.get("nombre_clinica"),
            comuna_clinica=d.get("comuna_clinica") or "",
            direccion_clinica=d.get("direccion_clinica") or "",
            tipo_pago="",
            reserva_uuid=str(uuid.uuid4()),
            fk_pac_no_register_id=estado["paciente_id"],
        )
        mensaje_final = (
            "🎉 ¡Tu reserva ha sido creada exitosamente!\n\n"
            f"🔖 **Código de reserva:** {nueva_reserva.reserva_uuid}\n"
            f"- **Especialidad:** {nueva_reserva.especialidad}\n"
            f"- **Clínica:** {nueva_reserva.nombre_clinica}\n"
            f"- **Doctor/a:** {nueva_reserva.nombre_doctor}\n"
            f"- **Fecha:** {nueva_reserva.fecha_reserva}\n"
            f"- **Hora:** {nueva_reserva.hora_inicio} - {nueva_reserva.hora_termino}\n\n"
            "Guarda tu código de reserva, lo necesitarás para consultarla o anularla más adelante."
        )
    except Exception as e:
        print(f"Error creando la reserva de paciente no registrado: {e}")
        mensaje_final = (
            "❌ Hubo un problema al crear tu reserva. Por favor, intenta nuevamente "
            "escribiendo 'quiero pedir una hora'."
        )
    finally:
        estado["paso"] = "inicio"
        estado["intencion"] = None
        estado["entidades"] = {}
        estado["datos_paciente"] = {}
        estado["datos_reserva"] = {}
        estado["paciente_id"] = None
    return mensaje_final


# ========== WIZARD: MANEJADOR PRINCIPAL DEL FLUJO ==========
def manejar_flujo_reserva_no_registrado(mensaje, estado):
    paso = estado["paso"]

    # --- Paso: RUT ---
    if paso == "reg_rut":
        rut_ingresado = mensaje.strip()
        if not validar_rut(rut_ingresado):
            return "⚠️ El RUT ingresado no es válido. Por favor, ingrésalo nuevamente (formato: 12345678-9):"

        rut_limpio = rut_ingresado.replace(".", "").replace("-", "").upper()
        estado["datos_paciente"]["rut"] = rut_limpio
        estado["paso"] = PASOS_PACIENTE[0][0]
        return f"🆕 Vamos a crear tu ficha.\n\n{PASOS_PACIENTE[0][2]}"

    # --- Pasos de datos personales ---
    for indice, (nombre_paso, campo, pregunta) in enumerate(PASOS_PACIENTE):
        if paso == nombre_paso:
            valor = mensaje.strip()
            validador = VALIDADORES_CAMPOS.get(campo)
            if validador and not validador(valor):
                return f"⚠️ El dato ingresado no parece válido. {pregunta}"

            if campo == "sexo":
                valor = valor.upper()[0]
            if campo == "segundo_nombre" and valor.lower() == "ninguno":
                valor = ""

            estado["datos_paciente"][campo] = valor

            if indice + 1 < len(PASOS_PACIENTE):
                siguiente_paso, _siguiente_campo, siguiente_pregunta = PASOS_PACIENTE[
                    indice + 1
                ]
                estado["paso"] = siguiente_paso
                return siguiente_pregunta
            else:
                return crear_paciente_no_registrado_y_continuar(estado)

    # --- Pasos de datos de la reserva ---
    for indice, (nombre_paso, campo, pregunta) in enumerate(PASOS_RESERVA):
        if paso == nombre_paso:
            valor = mensaje.strip()

            if campo == "especialidad":
                try:
                    especialidad_obj = Especialidad.objects.get(
                        nombre_especialidad__iexact=valor
                    )
                    estado["datos_reserva"][
                        "especialidad"
                    ] = especialidad_obj.nombre_especialidad
                    clinicas = obtener_clinicas_por_especialidad(
                        especialidad_obj.nombre_especialidad
                    )
                    if not clinicas:
                        return "❌ No hay clínicas disponibles para esa especialidad. Intenta con otra especialidad."

                    estado["clinicas_disponibles"] = clinicas
                    estado["paso"] = PASOS_RESERVA[1][0]
                    lista = formatear_lista_opciones(clinicas, "nombre_clinica")
                    return f"🏥 Estas son las clínicas disponibles para {especialidad_obj.nombre_especialidad}:\n\n{lista}\n\nEscribe el número de la clínica que prefieras:"
                except Especialidad.DoesNotExist:
                    return "❌ No encontré esa especialidad. Por favor, intenta con otra (ej: Cardiología, Traumatología, etc.)."

            if campo == "clinica":
                clinicas = estado.get("clinicas_disponibles", [])
                if not validar_seleccion(valor, clinicas):
                    lista = formatear_lista_opciones(clinicas, "nombre_clinica")
                    return f"⚠️ Selección no válida. Elige un número del 1 al {len(clinicas)}:\n\n{lista}"

                idx = int(valor) - 1
                clinica_elegida = clinicas[idx]
                estado["datos_reserva"][
                    "nombre_clinica"
                ] = clinica_elegida.nombre_clinica
                estado["datos_reserva"][
                    "comuna_clinica"
                ] = clinica_elegida.comuna_clinica
                estado["datos_reserva"][
                    "direccion_clinica"
                ] = clinica_elegida.direccion_clinica

                especialidad_nombre = estado["datos_reserva"].get("especialidad")
                doctores = obtener_doctores_por_especialidad_y_clinica(
                    especialidad_nombre, clinica_elegida.nombre_clinica
                )
                if not doctores:
                    return "❌ No hay doctores disponibles para esa clínica y especialidad. Intenta con otra clínica."

                estado["doctores_disponibles"] = doctores
                estado["paso"] = PASOS_RESERVA[2][0]
                lista = formatear_lista_opciones(
                    doctores, "primer_nombre", "ap_paterno"
                )
                return f"🧑‍⚕️ Estos son los doctores disponibles para {especialidad_nombre} en {clinica_elegida.nombre_clinica}:\n\n{lista}\n\nEscribe el número del doctor que prefieras:"

            if campo == "nombre_doctor":
                doctores = estado.get("doctores_disponibles", [])
                if not validar_seleccion(valor, doctores):
                    lista = formatear_lista_opciones(
                        doctores, "primer_nombre", "ap_paterno"
                    )
                    return f"⚠️ Selección no válida. Elige un número del 1 al {len(doctores)}:\n\n{lista}"

                idx = int(valor) - 1
                doctor_elegido = doctores[idx]
                nombre_completo = f"{doctor_elegido.primer_nombre} {doctor_elegido.segundo_nombre} {doctor_elegido.ap_paterno} {doctor_elegido.ap_materno}".strip()
                estado["datos_reserva"]["nombre_doctor"] = nombre_completo
                estado["paso"] = PASOS_RESERVA[3][0]
                return f"✅ Has seleccionado al Dr/a. {nombre_completo}\n\n{PASOS_RESERVA[3][2]}"

            validador = VALIDADORES_CAMPOS.get(campo)
            if validador and not validador(valor):
                return f"⚠️ El dato ingresado no parece válido. {pregunta}"

            estado["datos_reserva"][campo] = valor

            if campo == "hora_inicio":
                hora_inicio_dt = datetime.strptime(valor, "%H:%M")
                hora_termino_dt = hora_inicio_dt + timedelta(hours=1)
                estado["datos_reserva"]["hora_termino"] = hora_termino_dt.strftime(
                    "%H:%M"
                )

            if indice + 1 < len(PASOS_RESERVA):
                siguiente_paso, _siguiente_campo, siguiente_pregunta = PASOS_RESERVA[
                    indice + 1
                ]
                estado["paso"] = siguiente_paso
                return siguiente_pregunta
            else:
                estado["paso"] = "res_confirmar"
                return generar_resumen_confirmacion(estado)

    # --- Paso: confirmar y crear la reserva ---
    if paso == "res_confirmar":
        respuesta_usuario = mensaje.strip().lower()
        if respuesta_usuario in ["si", "sí", "confirmar", "confirmo", "s"]:
            d = estado["datos_reserva"]
            disponible = verificar_disponibilidad_doctor(
                d.get("nombre_doctor"), d.get("fecha_reserva"), d.get("hora_inicio")
            )
            if not disponible:
                estado["paso"] = "res_hora_inicio"
                return (
                    "⚠️ Lo sentimos, el/la doctor/a ya tiene una reserva en ese horario. "
                    "Por favor, indica otra hora de inicio (formato: HH:00, ej: 09:00):"
                )
            return finalizar_reserva_no_registrado(estado)
        elif respuesta_usuario in ["no", "cancelar", "n"]:
            estado["paso"] = "inicio"
            estado["intencion"] = None
            estado["entidades"] = {}
            estado["datos_paciente"] = {}
            estado["datos_reserva"] = {}
            estado["paciente_id"] = None
            return "❌ Reserva cancelada. Si deseas comenzar de nuevo, escribe 'quiero pedir una hora'."
        else:
            return "❓ No entendí tu respuesta. ¿Confirmas la reserva? Responde 'Sí' o 'No'."

    estado["paso"] = "inicio"
    estado["datos_paciente"] = {}
    estado["datos_reserva"] = {}
    estado["paciente_id"] = None
    return "❌ Ocurrió un problema con tu solicitud. Por favor, escribe 'quiero pedir una hora' para comenzar de nuevo."


# ========== VISTA PRINCIPAL ==========
@api_view(["POST"])
@permission_classes([AllowAny])
def obtener_respuesta(request):
    try:
        mensaje = request.data.get("pregunta", "")
        session_id = request.data.get("session_id", "")

        if not mensaje:
            return Response(
                {"error": "Mensaje vacío"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not session_id:
            session_id = str(uuid.uuid4())

        if session_id not in estados_conversacion:
            estados_conversacion[session_id] = {
                "paso": "inicio",
                "intencion": None,
                "entidades": {},
                "datos_paciente": {},
                "datos_reserva": {},
                "paciente_id": None,
                "clinicas_disponibles": [],
                "doctores_disponibles": [],
            }

        estado = estados_conversacion[session_id]

        # ========== PRIORIDAD 1: DETECTAR SOLICITUD DE NUEVA RESERVA ==========
        if estado["paso"] == "inicio" and es_solicitud_nueva_reserva(mensaje):
            estado["paso"] = "reg_rut"
            estado["intencion"] = "solicitar_reserva"
            estado["entidades"] = {}
            estado["datos_paciente"] = {}
            estado["datos_reserva"] = {}
            estado["paciente_id"] = None
            return Response(
                {
                    "session_id": session_id,
                    "respuesta": "📝 ¡Con gusto te ayudo a agendar una hora! Para comenzar, indícame tu RUT (formato: 12345678-9):",
                    "intencion": "solicitar_reserva",
                },
                status=status.HTTP_200_OK,
            )

        # ========== PRIORIDAD 2: MANEJO DE ESTADO - ESPERANDO CÓDIGO ==========
        if estado["paso"] in ["esperando_codigo_anular", "esperando_codigo_info"]:
            codigo = extraer_codigo(mensaje)
            if not codigo:
                return Response(
                    {
                        "session_id": session_id,
                        "respuesta": "❌ El código ingresado no es válido. Debe ser un código UUID (ej: 550e8400-e29b-41d4-a716-446655440000). Por favor, verifica el código e inténtalo nuevamente.",
                    },
                    status=status.HTTP_200_OK,
                )

            resultado_codigo = procesar_codigo_reserva(mensaje, session_id)

            if resultado_codigo["existe"]:
                reserva = resultado_codigo["reserva"]
                if estado["paso"] == "esperando_codigo_anular":
                    reserva.reser_anulada = 1
                    reserva.save()
                    estados_conversacion[session_id] = {
                        "paso": "inicio",
                        "intencion": None,
                        "entidades": {},
                    }
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"✅ Tu reserva con código {resultado_codigo['codigo']} ha sido anulada correctamente.",
                            "intencion": "anular_reserva",
                        },
                        status=status.HTTP_200_OK,
                    )

                elif estado["paso"] == "esperando_codigo_info":
                    estados_conversacion[session_id] = {
                        "paso": "inicio",
                        "intencion": None,
                        "entidades": {},
                    }
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"📋 **Información de tu reserva:**\n- **Doctor:** {reserva.nombre_doctor}\n- **Especialidad:** {reserva.especialidad}\n- **Fecha:** {reserva.fecha_reserva}\n- **Hora:** {reserva.hora_inicio} - {reserva.hora_termino}\n- **Clínica:** {reserva.nombre_clinica}\n- **Estado:** {'Anulada' if reserva.reser_anulada else 'Activa'}",
                            "intencion": "informacion_reserva",
                        },
                        status=status.HTTP_200_OK,
                    )
            else:
                return Response(
                    {
                        "session_id": session_id,
                        "respuesta": f"❌ No encontré ninguna reserva con el código '{resultado_codigo['codigo']}'. Por favor, verifica el código e inténtalo nuevamente.",
                    },
                    status=status.HTTP_200_OK,
                )

        # ========== PRIORIDAD 3: MANEJO DE ESTADO - FLUJO DE RESERVA ==========
        if estado["paso"] in PASOS_FLUJO_RESERVA_NO_REGISTRADO:
            respuesta = manejar_flujo_reserva_no_registrado(mensaje, estado)
            return Response(
                {
                    "session_id": session_id,
                    "respuesta": respuesta,
                    "intencion": "reserva_no_registrado",
                },
                status=status.HTTP_200_OK,
            )

        # ========== PRIORIDAD 4: CLASIFICAR INTENCIÓN CON DEEPSEEK ==========
        intencion = clasificar_intencion(mensaje)
        print(f"Intención detectada: {intencion}")

        entidades = extraer_entidades(mensaje, intencion)
        print(f"Entidades extraídas: {entidades}")

        # ========== MANEJO DE INTENCIONES ==========
        if intencion == "anular_reserva":
            if "codigo" in entidades:
                codigo = entidades["codigo"]
                try:
                    reserva = ReservaModel.objects.get(reserva_uuid=codigo)
                    reserva.reser_anulada = 1
                    reserva.save()
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"✅ Tu reserva con código {codigo} ha sido anulada correctamente.",
                            "intencion": intencion,
                            "entidades": entidades,
                        },
                        status=status.HTTP_200_OK,
                    )
                except ReservaModel.DoesNotExist:
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"❌ No encontré ninguna reserva con el código {codigo}. Por favor, verifica el código.",
                            "intencion": intencion,
                            "entidades": entidades,
                        },
                        status=status.HTTP_200_OK,
                    )
            else:
                estados_conversacion[session_id] = {
                    "paso": "esperando_codigo_anular",
                    "intencion": intencion,
                    "entidades": entidades,
                }
                return Response(
                    {
                        "session_id": session_id,
                        "respuesta": "🔑 Para anular tu reserva, necesito el código de reserva. Por favor, escríbelo a continuación.",
                        "intencion": intencion,
                        "entidades": entidades,
                    },
                    status=status.HTTP_200_OK,
                )

        elif intencion == "informacion_reserva":
            if "codigo" in entidades:
                codigo = entidades["codigo"]
                try:
                    reserva = ReservaModel.objects.get(reserva_uuid=codigo)
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"📋 **Información de tu reserva:**\n- **Doctor:** {reserva.nombre_doctor}\n- **Especialidad:** {reserva.especialidad}\n- **Fecha:** {reserva.fecha_reserva}\n- **Hora:** {reserva.hora_inicio} - {reserva.hora_termino}\n- **Clínica:** {reserva.nombre_clinica}\n- **Estado:** {'Anulada' if reserva.reser_anulada else 'Activa'}",
                            "intencion": intencion,
                            "entidades": entidades,
                        },
                        status=status.HTTP_200_OK,
                    )
                except ReservaModel.DoesNotExist:
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"❌ No encontré ninguna reserva con el código {codigo}.",
                            "intencion": intencion,
                            "entidades": entidades,
                        },
                        status=status.HTTP_200_OK,
                    )
            else:
                estados_conversacion[session_id] = {
                    "paso": "esperando_codigo_info",
                    "intencion": intencion,
                    "entidades": entidades,
                }
                return Response(
                    {
                        "session_id": session_id,
                        "respuesta": "🔍 Para consultar tu reserva, necesito el código de reserva. Por favor, escríbelo a continuación.",
                        "intencion": intencion,
                        "entidades": entidades,
                    },
                    status=status.HTTP_200_OK,
                )

        elif intencion == "solicitar_reserva":
            estado["paso"] = "reg_rut"
            estado["datos_paciente"] = {}
            estado["datos_reserva"] = {}
            estado["paciente_id"] = None
            return Response(
                {
                    "session_id": session_id,
                    "respuesta": "📝 Para comenzar con tu reserva, indícame tu RUT (formato: 12345678-9):",
                    "intencion": "solicitar_reserva",
                },
                status=status.HTTP_200_OK,
            )

        # ========== OTRAS INTENCIONES ==========
        respuesta = generar_respuesta(intencion, entidades)
        return Response(
            {
                "session_id": session_id,
                "respuesta": respuesta,
                "intencion": intencion,
                "entidades": entidades,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as err:
        print(f"Error: {err}")
        return Response(
            {"error": "Hubo un problema al procesar tu solicitud."},
            status=status.HTTP_400_BAD_REQUEST,
        )
