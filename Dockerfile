# ==============================================================================
# ETAPA 1: BASE (Configuraciones y dependencias del sistema compartidas)
# ==============================================================================
# Definimos la imagen base de Python. Usamos la misma imagen para todas las etapas.
FROM python:3.13 AS base

# Evita que Python genere archivos .pyc en el disco, manteniendo el contenedor limpio.
ENV PYTHONDONTWRITEBYTECODE=1
# Fuerza que los logs de Python salgan directo a la consola (sin buffer) para verlos en tiempo real.
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema operativo requeridas por psycopg2, WeasyPrint, etc.
# Usamos --no-install-recommends para no instalar paquetes innecesarios y ahorrar espacio.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    pango1.0-tools \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo interno en /app para todas las etapas.
WORKDIR /app


# ==============================================================================
# ETAPA 2: DESARROLLO Y PRUEBAS (Incluye Pytest)
# ==============================================================================
# Nombramos esta etapa "development" para que docker-compose la use por defecto.
FROM base AS development

# Copiamos el requirements.txt (dependencias de producción)
COPY Clinica_DRF/requirements.txt .
# Copiamos el requirements-dev.txt (dependencias de desarrollo y testing)
COPY Clinica_DRF/requirements-dev.txt .

# Actualizamos pip e instalamos TODAS las librerías (incluyendo pytest, faker, etc.)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copiamos todo el proyecto del backend dentro de /app del contenedor
COPY . .

# Comando por defecto para desarrollo (levantar el servidor Django)
CMD ["python", "Clinica_DRF/manage.py", "runserver", "0.0.0.0:8000"]


# ==============================================================================
# ETAPA 3: PRODUCCIÓN (Ligera, segura y sin herramientas de testing)
# ==============================================================================
# Nombramos esta etapa "production" para que el pipeline de CI/CD la use.
FROM base AS production

# Copiamos ÚNICAMENTE el requirements.txt (sin las herramientas de desarrollo)
COPY Clinica_DRF/requirements.txt .

# Actualizamos pip e instalamos SOLO lo necesario para que la app funcione en producción.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto del backend dentro de /app del contenedor
COPY . .

# Comando para iniciar la aplicación en producción.
# (Nota: En un futuro, aquí cambiarías "runserver" por un servidor real como Gunicorn).
CMD ["python", "Clinica_DRF/manage.py", "runserver", "0.0.0.0:8000"]