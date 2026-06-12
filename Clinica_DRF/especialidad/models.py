from django.db import models

# Create your models here.
class Especialidad(models.Model):
    nombre_especialidad = models.TextField(max_length=250, null=True)
    valor_especialidad = models.PositiveIntegerField(null=True)
    
    def __str__(self):
        return self.nombre_especialidad
