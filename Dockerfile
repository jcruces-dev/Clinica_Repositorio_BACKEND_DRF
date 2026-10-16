# Definimos la imagen base de Python en su versión ligera.
FROM python:3.13-slim

# Evita que Python genere archivos .pyc en el disco y fuerza que los logs salgan 
# directo a consola sin buffer.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema operativo requeridas por psycopg2 y WeasyPrint
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

# Establecemos el directorio de trabajo interno en /app
WORKDIR /app

# Copiamos el archivo requirements.txt ubicado dentro de la subcarpeta Clinica_DRF hacia el directorio /app del contenedor
COPY Clinica_DRF/requirements.txt .

# Actualizamos pip e instalamos las librerías necesarias sin guardar archivos en caché
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos todo el proyecto del backend dentro de /app
COPY . .

# Comando por defecto para iniciar el servidor de desarrollo apuntando a manage.py dentro de Clinica_DRF
CMD ["python", "Clinica_DRF/manage.py", "runserver", "0.0.0.0:8000"]