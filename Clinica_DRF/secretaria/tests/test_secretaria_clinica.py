import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from secretaria.models import SecretariaModel


#
@pytest.mark.django_db
def test_agregar_clinica_a_secretaria(crear_secretaria, crear_clinica):
    # 1. Autenticamos al usuario (la vista pide IsAuthenticated)
    client = APIClient()
    client.force_authenticate(user=crear_secretaria.fk_user)

    # 2. Preparamos la URL y los datos
    url = reverse("agregar_clin_secretaria_panel_adm")
    data = {
        # ID del usuario de la secretaria que queremos actualizar.
        "id_user_secretaria": crear_secretaria.fk_user_id,
        # ID de la clínica que queremos agregar a la secretaria.
        "id_clinica": crear_clinica.id,
    }

    # Al principio, la secretaria del fixture ya viene con 1 clínica asignada
    # (la que agregamos en el conftest). Podemos validar que al menos tenga 1.
    assert crear_secretaria.secretaria_clinica.count() == 1

    # 3. Hacemos la petición
    response = client.post(url, data, format="json")

    # 4. Verificamos que responda 200
    assert response.status_code == 200

    # 5. Verificamos que la relación ManyToMany se haya guardado
    # (Si le pasamos la misma clínica, seguirá siendo 1. Si quisiéramos probar
    # agregar una segunda, tendríamos que crear otra clínica en el test).
    crear_secretaria.refresh_from_db()
    assert crear_secretaria.secretaria_clinica.count() == 1


#
@pytest.mark.django_db
def test_delete_clin_secretaria(crear_clinica, crear_secretaria):
    # 1. Autenticamos al usuario (la vista pide IsAuthenticated)
    client = APIClient()
    client.force_authenticate(user=crear_secretaria.fk_user)
    # Se debe verificar que al inicio la secretaria tenga la clínica asignada (por el fixture)
    assert crear_secretaria.secretaria_clinica.count() == 1
    # 2. Preparamos la URL para eliminar la clínica de la secretaria.
    # En este caso, como es relacion de una a muchas,
    # necesitamos pasar el id de la clínica y el id del usuario de la secretaria.
    url = reverse(
        "delete_clin_secretaria",
        kwargs={
            "id_clin": crear_clinica.id,
            "id_user_secret": crear_secretaria.fk_user_id,
        },
    )
    # Usamos DELETE
    response = client.delete(url)
    print("RESPUESTA DEL SERVIDOR:", response.json())
    # Verificamos que la respuesta sea exitosa (código 200).
    assert response.status_code == 200
    # Verificamos que la clínica haya sido eliminada de la secretaria.
    crear_secretaria.refresh_from_db()
    assert crear_secretaria.secretaria_clinica.count() == 0
    # Verificamos que la secretaria SIGUE existiendo en la base de datos
    assert SecretariaModel.objects.filter(id=crear_secretaria.id).exists()
