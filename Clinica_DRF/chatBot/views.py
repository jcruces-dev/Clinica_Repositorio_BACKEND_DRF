from django.shortcuts import render
# Importamos la librería de OpenIa.
from openai import OpenAI
# Llamamos la API_KEY de OpenIA de una manera más segura.
from decouple import config
# Permisos para peticion de la API.
from rest_framework.decorators import authentication_classes, permission_classes, api_view
# Cuando se establece IsAuthenticated como permiso para una vista, solo los usuarios autenticados podrán acceder a esa vista. Los usuarios no autenticados no tendrán permiso para realizar la solicitud
from rest_framework.permissions import IsAuthenticated, AllowAny
# Importamos el status.
from rest_framework import status
#
from rest_framework.response import Response
# HHTP RESPONSE.
from django.http import JsonResponse, HttpResponse
#
from reserva.models import ReservaModel
from reserva.serializers import ReservaSerializer



@api_view(['POST'])
@permission_classes([AllowAny])
def obtener_respuesta(request):
    try:
        # Recibimos la pregunta del usuario.
        pregunta = request.data.get('pregunta', '').strip()
        opcion = request.data.get('opcion')
        print(f"Pregunta recibida: {pregunta}")
        print(f"Opción seleccionada: {opcion}")

        # Si no existe pregunta, enviamos el error.
        if not pregunta:
            return Response({'error': 'Pregunta vacía'}, status=status.HTTP_400_BAD_REQUEST)

        # Revisamos si trae opcion seleccionda por el paciente.
        match opcion:
            case 2:
                try:
                    # Dependiendo de la opción cambiamos el color.
                    reserva_info = ReservaModel.objects.get(reserva_uuid=pregunta)
                    estado_reserva = "Anulada" if reserva_info.reser_anulada == 1 else "Activa"
                    color_estado = "#dc3545" if reserva_info.reser_anulada == 1 else "#28a745"

                    #
                    reserva_cerrada = "Si" if reserva_info.pago_realizado == 1 else "No"
                    # El color debe ser verde (#28a745) si está pagada (1) y rojo (#dc3545) si no (0).
                    color_estado_cerrada = "#28a745" if reserva_info.pago_realizado == 1 else "#dc3545"

                    # Creamos una estructura HTML elegante
                    respuesta_demo = f"""
                    <div class="reserva-card">
                        <div class="reserva-header">🗓️ Detalles de tu Cita</div>
                        <div class="reserva-body">
                            <p><i class="fas fa-user-md"></i> <strong>Doctor:</strong> {reserva_info.nombre_doctor}</p>
                            <p><i class="fas fa-stethoscope"></i> <strong>Especialidad:</strong> {reserva_info.especialidad}</p>
                            <p><i class="fas fa-hospital"></i> <strong>Clínica:</strong> {reserva_info.nombre_clinica}</p>
                            <p><i class="fas fa-map-marker-alt"></i> <strong>Ubicación:</strong> {reserva_info.comuna_clinica}</p>
                            <p><i class="fas fa-calendar-alt"></i> <strong>Fecha:</strong> {reserva_info.fecha_reserva}</p>
                            <p><i class="fas fa-clock"></i> <strong>Horario:</strong> {reserva_info.hora_inicio} - {reserva_info.hora_termino}</p>
                            <div class="reserva-status" style="background-color: {color_estado_cerrada}">
                                Reserva Pagada: {reserva_cerrada}
                            </div>
                            <div class="reserva-status" style="background-color: {color_estado}">
                                Estado Reserva: {estado_reserva}
                            </div>
                            <button type="button" id="boton_volver_info_reserva_chatbot" onclick="boton_volver_chatbot()" class="btn btn-sm btn-outline-info mt-3">Volver</button>
                        </div>
                    </div>
                    """
                    return Response({'respuesta': respuesta_demo}, status=status.HTTP_200_OK)
                except ReservaModel.DoesNotExist:
                    return Response({'respuesta': "❌ No encontré una reserva con ese código."}, status=status.HTTP_404_NOT_FOUND)
            case 3:
                try:
                    # Recibimos el código de la reserva que se desea cancelar.
                    reserva = ReservaModel.objects.get(reserva_uuid=pregunta)
                    reserva.fecha_reserva = None
                    reserva.hora_inicio = None
                    reserva.hora_termino = None
                    reserva.reser_anulada = 1
                    reserva.save()

                    # Dependiendo de la opción cambiamos el color.
                    reserva_info = ReservaModel.objects.get(reserva_uuid=pregunta)
                    estado_reserva = "Anulada" if reserva_info.reser_anulada == 1 else "Activa"
                    color_estado = "#dc3545" if reserva_info.reser_anulada == 1 else "#28a745"

                    #
                    reserva_cerrada = "No" if reserva_info.pago_realizado == 1 else "Si"
                    color_estado_cerrada = "#dc3545" if reserva_info.pago_realizado == 1 else "#28a745"

                    # Código si coincide con valor2
                    respuesta_demo = f"""
                    <div class="reserva-card">
                        <div class="reserva-header">
                            ✅ Cita Cancelada Correctamente
                        </div>
                        <div class="reserva-body">
                            <p><i class="fas fa-user-md"></i> <strong>Doctor:</strong> {reserva_info.nombre_doctor}</p>
                            <p><i class="fas fa-stethoscope"></i> <strong>Especialidad:</strong> {reserva_info.especialidad}</p>
                            <p><i class="fas fa-hospital"></i> <strong>Clínica:</strong> {reserva_info.nombre_clinica}</p>
                            <p><i class="fas fa-map-marker-alt"></i> <strong>Ubicación:</strong> {reserva_info.comuna_clinica}</p>
                            <button type="button" id="boton_volver_cancel_reserva_chatbot" onclick="boton_cancelar_reser_volver_chatbot()" class="btn btn-sm btn-outline-info mt-3">Volver</button>
                        </div>
                    </div>
                    """
                    return Response({'respuesta': respuesta_demo}, status=status.HTTP_200_OK)
                except ReservaModel.DoesNotExist:
                    return Response({'respuesta': "❌ No encontré una reserva con ese código."}, status=status.HTTP_404_NOT_FOUND)
            case 0:
                try:
                    # Código si coincide con valor2
                    respuesta_data = {
                    "tipo": "animar",
                    "texto": f"⚠️ Modo demo activado. Recibí tu pregunta: “{pregunta}”, pero en este momento no me encuentro operativo.",
                    "html_boton": f"""
                        <div style="text-align: center; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px;">
                            <button type="button" onclick="boton_volver_chat_chatbot()" class="btn-volver-inicio">
                                <i class="fas fa-arrow-left me-2"></i>Volver al Inicio
                            </button>
                        </div>
                    """
                    }
                    return Response({'respuesta': respuesta_data}, status=status.HTTP_200_OK)
                except ReservaModel.DoesNotExist:
                    return Response({'respuesta': "❌ No encontré una reserva con ese código."}, status=status.HTTP_404_NOT_FOUND)
            case _:
                # En caso de Activar OpenIA, solo se debe reestablecer al código de abajo.
                # if True:  # ← Cambia esto a una variable de configuración si deseas
                #     return Response({'respuesta': respuesta_demo}, status=status.HTTP_200_OK)
                # El guion bajo es el "default" (si nada coincide)
                # Simulamos una respuesta porque no tenemos créditos en OpenIA.
                # Simulamos una respuesta porque no tenemos créditos en OpenIA.
                respuesta_demo = f"""
                    <div class="demo-message">
                        <p style="margin-bottom: 15px;">⚠️ Modo demo activado. Recibí tu pregunta: “{pregunta}”, pero en este momento no me encuentro operativo.</p>
                        <div style="text-align: center; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px;">
                            <button type="button" onclick="boton_volver_chatbot()" class="btn-volver-inicio">
                                <i class="fas fa-arrow-left me-2"></i>Volver al Inicio
                            </button>
                        </div>
                    </div>
                    """
                return Response({'respuesta': respuesta_demo}, status=status.HTTP_200_OK)

        # Funcionando.
        # Código real (cuando vuelvas a tener acceso)
        # client = OpenAI(api_key=config('OPENAI_API_KEY'))
        # response = client.chat.completions.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "Eres un asistente útil."},
        #         {"role": "user", "content": pregunta}
        #     ]
        # )
        # respuesta_real = response.choices[0].message.content
        # return Response({'respuesta': respuesta_real}, status=status.HTTP_200_OK)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return Response({'error': 'Hubo un problema al procesar tu solicitud.'}, status=status.HTTP_400_BAD_REQUEST)