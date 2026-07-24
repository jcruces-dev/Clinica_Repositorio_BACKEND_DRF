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
from datetime import datetime

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
    # Función auxiliar para llamar a DeepSeek recordar que es de manera Local.
    url = "http://127.0.0.1:11434/api/chat"
    # Este código es específico para la API de Ollama (Servidor Local), que es la que usa DeepSeek.
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0},
        "stream": False,
    }
    try:
        # Hacemos la petición POST a DeepSeek con un timeout de 350 segundos (5 minutos) .
        response = requests.post(url, json=payload, timeout=350)
        data = response.json()
        contenido = data["message"]["content"]

        # Intentar extraer JSON si existe
        json_match = re.search(r"\{.*\}", contenido, re.DOTALL)
        if json_match:
            # Si encontramos un JSON, lo parseamos y lo retornamos como diccionario.
            # Para esto, usamos json.loads() para convertir la cadena JSON en un diccionario de Python.
            return json.loads(json_match.group())
        return contenido.strip()
    except Exception as e:
        print(f"Error llamando a DeepSeek: {e}")
        return None


# ========== PROMPT 1: CLASIFICAR INTENCIÓN ==========
# Esta función toma el mensaje del usuario y lo envía a DeepSeek para determinar la intención.
def clasificar_intencion(mensaje):
    prompt = f"""
        Eres un asistente de una clínica médica. Clasifica la intención del usuario en una de estas opciones:

        - "anular_reserva": el usuario quiere cancelar, anular o eliminar su cita
        - "informacion_reserva": el usuario quiere saber información de su cita
        - "consultar_doctor": el usuario pregunta por doctores o especialidades
        - "consultar_clinica": el usuario pregunta por clínicas o ubicaciones
        - "otro": no encaja en ninguna de las anteriores

        Devuelve SOLO UN JSON con el formato:
        {{"intencion": "opcion_elegida"}}

        Mensaje del usuario: "{mensaje}"
    """
    # Realizamosla petición a DeepSeek para obtener la intención del mensaje.
    resultado = llamar_deepseek(prompt)
    # Verificamos si el resultado es un diccionario y extraemos la intención.
    if resultado and isinstance(resultado, dict):
        # Retornamos la intención detectada, u "otro" si no se encuentra.
        return resultado.get("intencion", "otro")
    # Si no se pudo obtener un resultado válido, retornamos "otro".
    return "otro"


# ========== PROMPT 2: EXTRAER ENTIDADES ==========
# Esta función toma el mensaje del usuario y la intención detectada, y envía un prompt a DeepSeek para extraer las entidades relevantes.
def extraer_entidades(mensaje, intencion):
    # Este es el prompt que se envía a DeepSeek para extraer las entidades según la intención detectada.
    prompt = f"""
        Eres un asistente de una clínica. Extrae los datos importantes del mensaje del usuario.

        Intención detectada: {intencion}

        Extrae SOLO los campos relevantes según la intención:
        - Si es "anular_reserva" o "informacion_reserva": extrae "codigo" (código de reserva)
        - Si es "consultar_doctor": extrae "especialidad" o "nombre_doctor"
        - Si es "consultar_clinica": extrae "nombre_clinica" o "comuna"

        Devuelve SOLO UN JSON con las entidades encontradas.
        Si no encuentra ninguna, devuelve {{}}.

        Mensaje del usuario: "{mensaje}"
    """
    # Realizamos la petición a DeepSeek para obtener las entidades del mensaje (Interpretación).
    resultado = llamar_deepseek(prompt)
    # Verificamos si el resultado es un diccionario y lo retornamos.
    # Si resultado no es None, ni False, ni vacío
    # y además es un diccionario, lo retornamos. De lo contrario, retornamos un diccionario vacío.
    if resultado and isinstance(resultado, dict):
        return resultado
    return {}


# ========== PROMPT 3: GENERAR RESPUESTA ==========
# Esta función genera la respuesta del chatbot basada en la intención y las entidades extraídas.
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
    # Acá manejamos la intención de consultar doctores, verificando si se proporcionó una especialidad
    # o un nombre de doctor.
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

    else:
        return "👋 Hola, ¿cómo puedo ayudarte? Puedo consultar tu reserva, anular una cita o darte información de doctores y clínicas."


# ========== PROMPT 4: PROCESAR CÓDIGO ==========
# Procesa el código que el usuario escribe cuando se lo piden.
def procesar_codigo_reserva(mensaje, session_id):
    # Este es el método creado anteriormente para extraer los UUID.
    codigo = extraer_codigo(mensaje)
    # Si no se encuentra un UUID en el mensaje, usamos el mensaje completo como código.
    if not codigo:
        codigo = mensaje.strip()
        print(f"No se encontró UUID, usando mensaje completo: {codigo}")

    print(f"Código a buscar: {codigo}")
    # Intentamos buscar la reserva en la base de datos usando el código proporcionado.
    try:
        # Hacemos el lamado al modelo para verificar el cod UUID de la reserva.
        reserva = ReservaModel.objects.get(reserva_uuid=codigo)
        # Retornamos un diccionario indicando que la reserva existe,
        # junto con el código y la instancia de la reserva.
        return {"existe": True, "codigo": codigo, "reserva": reserva}
    except ReservaModel.DoesNotExist:
        return {"existe": False, "codigo": codigo, "reserva": None}


# ========== VALIDADORES DE CAMPOS (RESERVA PACIENTE NO REGISTRADO) ==========
def validar_solo_numeros(texto):
    """Valida que el texto ingresado contenga solo dígitos (ej: edad, teléfono)."""
    return texto.strip().isdigit()


def validar_sexo(texto):
    """Valida que el sexo ingresado sea 'M' o 'F'."""
    return texto.strip().upper() in ["M", "F"]


def validar_email(email):
    """Valida un formato básico de correo electrónico."""
    patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(patron_email, email.strip()) is not None


def validar_fecha(fecha_str):
    """Valida que la fecha venga en formato AAAA-MM-DD."""
    try:
        datetime.strptime(fecha_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_hora(hora_str):
    """Valida que la hora venga en formato HH:MM."""
    try:
        datetime.strptime(hora_str.strip(), "%H:%M")
        return True
    except ValueError:
        return False


# Diccionario que asocia cada campo del wizard con su función de validación.
# Los campos que no aparecen aquí (ej: primer_nombre, especialidad) se aceptan
# como texto libre, sin validación adicional.
VALIDADORES_CAMPOS = {
    "edad": validar_solo_numeros,
    "sexo": validar_sexo,
    "rut": validar_rut,
    "fono": validar_solo_numeros,
    "email": validar_email,
    "fecha_reserva": validar_fecha,
    "hora_inicio": validar_hora,
    "hora_termino": validar_hora,
}


# ========== DETECCIÓN DE INTENCIÓN: SOLICITAR NUEVA RESERVA ==========
def es_solicitud_nueva_reserva(mensaje):
    """
    Detecta por palabras clave si el usuario quiere iniciar el flujo de
    solicitud de una nueva reserva/hora. Se revisa antes de llamar a DeepSeek
    porque este flujo se maneja completamente con un wizard de estados propio.
    """
    mensaje_lower = mensaje.lower()
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
    ]
    return any(frase in mensaje_lower for frase in frases_clave)


# ========== WIZARD: PASOS PARA RECOLECTAR DATOS DEL PACIENTE NO REGISTRADO ==========
# Cada tupla es (nombre_del_paso, nombre_del_campo, pregunta_a_mostrar).
# El RUT se pide primero para poder detectar tempranamente si el paciente ya
# existe en la base de datos y así evitar volver a pedir el resto de sus datos.
PASOS_PACIENTE = [
    ("reg_primer_nombre", "primer_nombre", "😊 ¿Cuál es tu primer nombre?"),
    ("reg_segundo_nombre", "segundo_nombre", "¿Cuál es tu segundo nombre? (si no tienes, escribe 'ninguno')"),
    ("reg_ap_paterno", "ap_paterno", "¿Cuál es tu apellido paterno?"),
    ("reg_ap_materno", "ap_materno", "¿Cuál es tu apellido materno?"),
    ("reg_edad", "edad", "¿Cuál es tu edad?"),
    ("reg_sexo", "sexo", "¿Cuál es tu sexo? (M/F)"),
    ("reg_fono", "fono", "📞 ¿Cuál es tu número de teléfono?"),
    ("reg_email", "email", "📧 ¿Cuál es tu correo electrónico?"),
]

# Pasos para recolectar los datos de la reserva propiamente tal.
PASOS_RESERVA = [
    ("res_especialidad", "especialidad", "🩺 ¿Qué especialidad médica necesitas?"),
    ("res_doctor", "nombre_doctor", "🧑‍⚕️ ¿Con qué doctor/a deseas la cita? (si no tienes preferencia, escribe 'cualquiera')"),
    ("res_clinica", "nombre_clinica", "🏥 ¿En qué clínica deseas atenderte?"),
    ("res_comuna", "comuna_clinica", "📍 ¿En qué comuna se encuentra la clínica?"),
    ("res_direccion", "direccion_clinica", "🏠 ¿Cuál es la dirección de la clínica?"),
    ("res_fecha", "fecha_reserva", "📅 ¿Qué fecha deseas para tu cita? (formato: AAAA-MM-DD)"),
    ("res_hora_inicio", "hora_inicio", "⏰ ¿A qué hora inicia tu cita? (formato: HH:MM)"),
    ("res_hora_termino", "hora_termino", "⏰ ¿A qué hora termina tu cita? (formato: HH:MM)"),
    ("res_tipo_pago", "tipo_pago", "💳 ¿Cuál será el tipo de pago? (Efectivo/Débito/Crédito)"),
]

# Conjunto con TODOS los nombres de "paso" que pertenecen a este flujo. Se usa en
# la vista principal para saber si el mensaje entrante debe ser manejado por el wizard.
PASOS_FLUJO_RESERVA_NO_REGISTRADO = (
    {"esperando_confirmacion_registro", "reg_rut", "res_confirmar"}
    | {paso for paso, _campo, _pregunta in PASOS_PACIENTE}
    | {paso for paso, _campo, _pregunta in PASOS_RESERVA}
)


# ========== WIZARD: CREAR FICHA DEL PACIENTE NO REGISTRADO ==========
def crear_paciente_no_registrado_y_continuar(estado):
    """
    Se ejecuta cuando ya se recolectaron todos los datos personales del paciente
    (no encontrado previamente por RUT). Crea el registro en PacienteNoRegisterModel
    y avanza el estado hacia el primer paso de recolección de datos de la reserva.
    """
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


def generar_resumen_confirmacion(estado):
    """Genera el resumen de la reserva antes de crearla, para que el usuario confirme."""
    d = estado["datos_reserva"]
    return (
        "📋 Por favor confirma los datos de tu reserva:\n\n"
        f"- **Especialidad:** {d.get('especialidad')}\n"
        f"- **Doctor/a:** {d.get('nombre_doctor')}\n"
        f"- **Clínica:** {d.get('nombre_clinica')}\n"
        f"- **Comuna:** {d.get('comuna_clinica')}\n"
        f"- **Dirección:** {d.get('direccion_clinica')}\n"
        f"- **Fecha:** {d.get('fecha_reserva')}\n"
        f"- **Hora:** {d.get('hora_inicio')} - {d.get('hora_termino')}\n"
        f"- **Tipo de pago:** {d.get('tipo_pago')}\n\n"
        "¿Confirmas estos datos? Responde 'Sí' para agendar o 'No' para cancelar."
    )


def finalizar_reserva_no_registrado(estado):
    """Crea la ReservaModel definitiva, asociada al paciente no registrado."""
    d = estado["datos_reserva"]
    try:
        nueva_reserva = ReservaModel.objects.create(
            usuario_creacion_reserva="chatbot_paciente_no_registrado",
            fecha_reserva=d.get("fecha_reserva"),
            hora_inicio=d.get("hora_inicio"),
            hora_termino=d.get("hora_termino"),
            especialidad=d.get("especialidad"),
            nombre_doctor=d.get("nombre_doctor"),
            tipo_pago=d.get("tipo_pago"),
            reserva_uuid=str(uuid.uuid4()),
            nombre_clinica=d.get("nombre_clinica"),
            comuna_clinica=d.get("comuna_clinica"),
            direccion_clinica=d.get("direccion_clinica"),
            fk_pac_no_register_id=estado["paciente_id"],
        )
        mensaje_final = (
            "🎉 ¡Tu reserva ha sido creada exitosamente!\n\n"
            f"🔖 **Código de reserva:** {nueva_reserva.reserva_uuid}\n"
            f"- **Especialidad:** {nueva_reserva.especialidad}\n"
            f"- **Doctor/a:** {nueva_reserva.nombre_doctor}\n"
            f"- **Clínica:** {nueva_reserva.nombre_clinica}\n"
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
    """
    Maneja TODOS los pasos del flujo de reserva para pacientes no registrados,
    usando el `paso` guardado en el estado de la conversación (estados_conversacion).
    Retorna siempre un string con la respuesta a enviar al usuario.
    """
    paso = estado["paso"]

    # --- Paso 0: ¿Estás registrado? ---
    if paso == "esperando_confirmacion_registro":
        respuesta_usuario = mensaje.strip().lower()
        if respuesta_usuario in ["no", "no estoy registrado", "no, no estoy registrado", "n"]:
            estado["paso"] = "reg_rut"
            estado["datos_paciente"] = {}
            estado["datos_reserva"] = {}
            estado["paciente_id"] = None
            return "🪧 Perfecto, para comenzar indícame tu RUT (formato: 12345678-9):"
        elif respuesta_usuario in ["si", "sí", "si estoy registrado", "sí, estoy registrado", "s"]:
            estado["paso"] = "inicio"
            estado["intencion"] = None
            estado["entidades"] = {}
            return (
                "🙂 Por ahora este asistente solo gestiona reservas para pacientes NO registrados. "
                "Por favor, ingresa a tu cuenta de paciente para solicitar tu hora."
            )
        else:
            return "❓ No entendí tu respuesta. ¿Estás registrado en el sistema? Responde 'Sí' o 'No'."

    # --- Paso: RUT (se pide primero para detectar duplicados) ---
    if paso == "reg_rut":
        rut_ingresado = mensaje.strip()
        if not validar_rut(rut_ingresado):
            return "⚠️ El RUT ingresado no es válido. Por favor, ingrésalo nuevamente (formato: 12345678-9):"

        rut_limpio = rut_ingresado.replace(".", "").replace("-", "").upper()

        # Validamos que el RUT no exista ya en PacienteNoRegisterModel, para evitar duplicados.
        try:
            paciente_existente = PacienteNoRegisterModel.objects.filter(rut=rut_limpio).first()
        except Exception as e:
            print(f"Error consultando PacienteNoRegisterModel: {e}")
            return "❌ Hubo un problema al validar tu RUT. Intenta nuevamente en unos momentos."

        estado["datos_paciente"]["rut"] = rut_limpio

        if paciente_existente:
            # El paciente ya existe: lo reutilizamos y saltamos directo a los datos de la reserva.
            estado["paciente_id"] = paciente_existente.id
            estado["paso"] = PASOS_RESERVA[0][0]
            return (
                f"✅ Encontré una ficha registrada con ese RUT a nombre de {paciente_existente.primer_nombre}. "
                f"Usaremos esos datos.\n\nAhora sigamos con los datos de tu reserva.\n\n{PASOS_RESERVA[0][2]}"
            )
        else:
            # No existe: comenzamos a recolectar el resto de los datos personales.
            estado["paso"] = PASOS_PACIENTE[0][0]
            return f"🆕 No encontré registros con ese RUT, vamos a crear tu ficha.\n\n{PASOS_PACIENTE[0][2]}"

    # --- Pasos de datos personales (todos excepto el RUT, ya manejado arriba) ---
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
                siguiente_paso, _siguiente_campo, siguiente_pregunta = PASOS_PACIENTE[indice + 1]
                estado["paso"] = siguiente_paso
                return siguiente_pregunta
            else:
                # Ya se recolectaron todos los datos personales: creamos la ficha del paciente.
                return crear_paciente_no_registrado_y_continuar(estado)

    # --- Pasos de datos de la reserva ---
    for indice, (nombre_paso, campo, pregunta) in enumerate(PASOS_RESERVA):
        if paso == nombre_paso:
            valor = mensaje.strip()
            validador = VALIDADORES_CAMPOS.get(campo)
            if validador and not validador(valor):
                return f"⚠️ El dato ingresado no parece válido. {pregunta}"

            if campo == "nombre_doctor" and valor.lower() == "cualquiera":
                valor = "Sin preferencia"

            estado["datos_reserva"][campo] = valor

            if indice + 1 < len(PASOS_RESERVA):
                siguiente_paso, _siguiente_campo, siguiente_pregunta = PASOS_RESERVA[indice + 1]
                estado["paso"] = siguiente_paso
                return siguiente_pregunta
            else:
                # Ya se recolectaron todos los datos de la reserva: pedimos confirmación.
                estado["paso"] = "res_confirmar"
                return generar_resumen_confirmacion(estado)

    # --- Paso: confirmar y crear la reserva ---
    if paso == "res_confirmar":
        respuesta_usuario = mensaje.strip().lower()
        if respuesta_usuario in ["si", "sí", "confirmar", "confirmo", "s"]:
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

    # Si por alguna razón el paso no coincide con ninguno conocido, reiniciamos el flujo.
    estado["paso"] = "inicio"
    estado["datos_paciente"] = {}
    estado["datos_reserva"] = {}
    estado["paciente_id"] = None
    return "❌ Ocurrió un problema con tu solicitud. Por favor, escribe 'quiero pedir una hora' para comenzar de nuevo."


# ========== VISTA PRINCIPAL ==========
# Acá en esta vista se le envía el mensaje del usuario y devuelve la respuesta del chatbot.
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

        # Si no hay session_id, crear uno nuevo
        if not session_id:
            session_id = str(uuid.uuid4())

        # Inicializar estado si es nuevo
        if session_id not in estados_conversacion:
            # Guardamos el estado inicial de la conversación para este session_id.
            # Incluimos "datos_paciente", "datos_reserva" y "paciente_id" para soportar
            # el flujo de reserva de pacientes NO registrados.
            estados_conversacion[session_id] = {
                "paso": "inicio",
                "intencion": None,
                "entidades": {},
                "datos_paciente": {},
                "datos_reserva": {},
                "paciente_id": None,
            }
        # Una vez que tenemos el session_id, obtenemos el estado actual de la conversación para este usuario.
        # forma de acceder al estado de una conversación específica usando el session_id como
        # "llave" para encontrar la información guardada.
        estado = estados_conversacion[session_id]

        # ========== MANEJO DE ESTADO: ESPERANDO CÓDIGO ==========
        # Acá verificamos si estamos en un estado donde el chatbot está esperando que
        # el usuario ingrese un código de reserva.
        if estado["paso"] in ["esperando_codigo_anular", "esperando_codigo_info"]:
            resultado_codigo = procesar_codigo_reserva(mensaje, session_id)

            if resultado_codigo["existe"]:
                reserva = resultado_codigo["reserva"]
                # Dependiendo del paso en el que estamos, realizamos la acción correspondiente.
                if estado["paso"] == "esperando_codigo_anular":
                    # Realizamos la acción si la reserva existe:
                    # anulamos la reserva y actualizamos el estado de la conversación.
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
                            "respuesta": f"""📋 **Información de tu reserva:**
                            - **Doctor:** {reserva.nombre_doctor}
                            - **Especialidad:** {reserva.especialidad}
                            - **Fecha:** {reserva.fecha_reserva}
                            - **Hora:** {reserva.hora_inicio} - {reserva.hora_termino}
                            - **Clínica:** {reserva.nombre_clinica}
                            - **Estado:** {'Anulada' if reserva.reser_anulada else 'Activa'}""",
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

        # ========== MANEJO DE ESTADO: FLUJO DE RESERVA PARA PACIENTE NO REGISTRADO ==========
        # Si estamos en medio del wizard de creación de reserva para un paciente no
        # registrado (recolectando datos personales o datos de la reserva), delegamos
        # el manejo completo del mensaje a `manejar_flujo_reserva_no_registrado`.
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

        # ========== DETECTAR INICIO DE SOLICITUD DE NUEVA RESERVA ==========
        # Antes de clasificar la intención con el modelo, revisamos si el usuario está
        # pidiendo explícitamente una nueva reserva/hora, ya que este flujo se maneja
        # con un wizard de estados propio (no requiere DeepSeek).
        if estado["paso"] == "inicio" and es_solicitud_nueva_reserva(mensaje):
            estado["paso"] = "esperando_confirmacion_registro"
            estado["intencion"] = "solicitar_reserva"
            estado["entidades"] = {}
            return Response(
                {
                    "session_id": session_id,
                    "respuesta": "📝 ¡Con gusto te ayudo a agendar una hora! ¿Estás registrado en el sistema como paciente? Responde 'Sí' o 'No'.",
                    "intencion": "solicitar_reserva",
                },
                status=status.HTTP_200_OK,
            )

        # ========== PASO 1: CLASIFICAR INTENCIÓN ==========
        # Primero, clasificamos la intención del mensaje del usuario usando la función clasificar_intencion.
        intencion = clasificar_intencion(mensaje)
        print(f"Intención detectada: {intencion}")

        # ========== PASO 2: EXTRAER ENTIDADES ==========
        # Extraemos las entidades relevantes del mensaje según la intención detectada anteriormente.
        entidades = extraer_entidades(mensaje, intencion)
        print(f"Entidades extraídas: {entidades}")

        # ========== PASO 3: VERIFICAR SI FALTA INFORMACIÓN ==========
        # Dependiendo de la intención, verificamos si necesitamos más información del usuario.
        if intencion == "anular_reserva":
            # Si la intención es anular una reserva, verificamos si el
            # código de reserva está presente en las entidades extraídas.
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
        # Acá manejamos la intención de información de reserva, verificando si el código está presente y
        # actuando en consecuencia.
        elif intencion == "informacion_reserva":
            if "codigo" in entidades:
                codigo = entidades["codigo"]
                try:
                    reserva = ReservaModel.objects.get(reserva_uuid=codigo)
                    return Response(
                        {
                            "session_id": session_id,
                            "respuesta": f"""📋 **Información de tu reserva:**
                            - **Doctor:** {reserva.nombre_doctor}
                            - **Especialidad:** {reserva.especialidad}
                            - **Fecha:** {reserva.fecha_reserva}
                            - **Hora:** {reserva.hora_inicio} - {reserva.hora_termino}
                            - **Clínica:** {reserva.nombre_clinica}
                            - **Estado:** {'Anulada' if reserva.reser_anulada else 'Activa'}""",
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

        # ========== OTRAS INTENCIONES ==========
        # Para las demás intenciones, generamos una respuesta basada en la intención y las entidades extraídas.
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
