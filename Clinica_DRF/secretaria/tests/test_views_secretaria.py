import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model


# Este es el test para probar la insercción a la BD desde el panel Admin.
@pytest.mark.django_db
def test_crear_secretaria_desde_admin(crear_clinica, crear_grupo_secretaria):

    #
    User = get_user_model()
    admin_user = User.objects.create_user(
        username="admin_test",
        password="Password123!",
        email="admin@test.com",
        is_staff=True,
        is_superuser=True,
    )

    client = APIClient()
    client.force_authenticate(user=admin_user)

    url = reverse("crear_secretaria")
    data = {
        "username": "nueva_secre_unica",
        "password": "123",
        "email": "nueva@test.com",
        "primer_nombre": "Maria",
        "segundo_nombre": "Josefa",
        "ap_paterno": "Gonzalez",
        "ap_materno": "Rojas",
        "edad": 30,
        "sexo": "F",
        "rut": "98.757.278-7",
        "fono": "974699961",
        "id_clinica": crear_clinica.id,
    }

    response = client.post(url, data, format="json")
    print("RESPUESTA DEL SERVIDOR:", response.json())
    assert response.status_code in (200, 201)


#
@pytest.mark.django_db
def test_crear_secretaria(crear_user_secretaria, crear_clinica):
    client = APIClient()
    client.force_authenticate(user=crear_user_secretaria)
    # Esta es la url de la vista que queremos probar. Debe coincidir con el nombre que le dimos en urls.py.
    url = reverse("crear_secretaria")
    # Enviamos más datos.
    data = {
        "username": "nueva_secre_unica",
        "password": "123",
        "email": "nueva@test.com",
        "primer_nombre": "Maria",
        "segundo_nombre": "Josefa",
        "ap_paterno": "Gonzalez",
        "ap_materno": "Rojas",
        "edad": 30,
        "sexo": "F",
        "rut": "98.757.278-7",
        # 9 dígitos, sin el +56
        "fono": "974699961",
        # La vista lo necesita para el ManyToMany.
        "id_clinica": crear_clinica.id,
    }

    response = client.post(url, data, format="json")
    print("RESPUESTA CREAR:", response.json())
    print("RESPUESTA DEL SERVIDOR:", response.json())
    # Verificamos que la respuesta sea exitosa (código 201).
    assert response.status_code == 200


# Este es el FIXTURE que se encarga de crear 3 secretarias con Faker,
# para luego ser utilizadas en el test_listar_secretarias_masivo.
@pytest.mark.django_db
def test_listar_secretarias_masivo(crear_3_secretarias):
    client = APIClient()
    url = reverse("listar_secretaria")
    response = client.get(url)
    # Verificamos que la respuesta sea exitosa (código 200).
    assert response.status_code == 200
    # Verificas que la API devolvió los 3 registros creados por Faker
    assert len(response.json()["secretarias"]) == 3


# Este es el FIXTURE que se encarga de crear una secretaria con Faker para actualizarla.
@pytest.mark.django_db
def test_actualizar_secretaria(crear_secretaria):
    client = APIClient()
    client.force_authenticate(user=crear_secretaria.fk_user)
    # Esta es la url de la vista que queremos probar. Debe coincidir con el nombre que le dimos en urls.py.
    url = reverse("update_secretaria", kwargs={"id": crear_secretaria.fk_user_id})

    # Enviamos más datos.
    data = {
        "username": crear_secretaria.fk_user.username,
        "password": "123",  # Enviamos una contraseña cualquiera
        "email": crear_secretaria.fk_user.email,
        "primer_nombre": "NombreActualizado",
        "segundo_nombre": crear_secretaria.segundo_nombre,
        "ap_paterno": crear_secretaria.ap_paterno,
        "ap_materno": crear_secretaria.ap_materno,
        "edad": crear_secretaria.edad,
        "sexo": crear_secretaria.sexo,
        "rut": crear_secretaria.rut,
        "fono": crear_secretaria.fono,
        "fk_user": crear_secretaria.fk_user_id,
        "secretaria_clinica": [
            c.id for c in crear_secretaria.secretaria_clinica.all()
        ],  # Si es ManyToMany
    }

    # Usamos PUT
    response = client.put(url, data, format="json")
    print("RESPUESTA DEL SERVIDOR:", response.json())
    # Verificamos que la respuesta sea exitosa (código 200).
    assert response.status_code == 200
    # Verificamos que el nombre de la secretaria se haya actualizado correctamente.
    crear_secretaria.refresh_from_db()
    assert crear_secretaria.primer_nombre == "NombreActualizado"


# Este es el FIXTURE que se encarga de crear una secretaria para eliminar.
@pytest.mark.django_db
def test_eliminar_secretaria(crear_secretaria):
    client = APIClient()
    client.force_authenticate(user=crear_secretaria.fk_user_id)

    url = reverse("delete_secretaria", kwargs={"id": crear_secretaria.fk_user_id})

    # Usamos DELETE
    response = client.delete(url)
    print("RESPUESTA DEL SERVIDOR:", response.json())
    # Verificamos que la respuesta sea exitosa (código 200).
    assert response.status_code == 200
    # Verificamos que la secretaria haya sido eliminada de la base de datos.
    with pytest.raises(crear_secretaria.DoesNotExist):
        crear_secretaria.refresh_from_db()
