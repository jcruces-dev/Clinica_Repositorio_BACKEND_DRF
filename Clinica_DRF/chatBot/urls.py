from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/chatbot/obtener_respuesta/",
        views.obtener_respuesta,
        name="obtener_respuesta",
    ),
]
