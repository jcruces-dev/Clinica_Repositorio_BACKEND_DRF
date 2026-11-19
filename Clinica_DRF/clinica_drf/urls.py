"""
URL configuration for clinica_drf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

#
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
    path("", include("consulta.urls")),
    path("", include("grupo.urls")),
    path("", include("especialidad.urls")),
    path("", include("direccion.urls")),
    path("", include("reserva.urls")),
    path("", include("debito.urls")),
    path("", include("credito.urls")),
    path("", include("comuna_clinica.urls")),
    path("", include("doctor.urls")),
    path("", include("secretaria.urls")),
    path("", include("paciente.urls")),
    path("", include("descuento.urls")),
    path("", include("chatBot.urls")),
    path("", include("historial_clinico.urls")),
    path("", include("paciente_no_registrado.urls")),
    path("", include("historial_pac_no_registrado.urls")),
]
