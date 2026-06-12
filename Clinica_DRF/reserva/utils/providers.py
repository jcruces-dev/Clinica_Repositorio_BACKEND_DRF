import random
from faker import Faker
from faker.providers import BaseProvider
# Configurado para Chile si necesitas localismos luego
fake = Faker('es_CL')

# Diccionario de Listas de Diccionarios
# Esta información se puede recorrer de la siguiente forma: 
# for especialidad, lista_de_casos in DATOS_CLINICOS_POR_ESPECIALIDAD.items():
    # Como 'lista_de_casos' es una lista, la recorremos con otro for
    # for caso in lista_de_casos:
    #     print(f"Diagnóstico: {caso['diagnostico']}")
    #     print(f"Síntoma: {caso['sintoma']}")
    #     print(f"Observación: {caso['observacion']}")
    #     print("-" * 20)
# Si queremos solo obtener uno en especial: # Entramos directo a la lista de esa especialidad
# casos_cardiologia = DATOS_CLINICOS_POR_ESPECIALIDAD[mi_especialidad]
DATOS_CLINICOS_POR_ESPECIALIDAD = {
    # [] Lista.
    "Cardiología": [
        # Diccionario nuevamente {}
        {
            "diagnostico": "Hipertensión arterial primaria",
            "sintoma": "Cefalea intensa, fatiga, tinnitus y palpitaciones.",
            "observacion": "Paciente refiere inicio de cuadro hace 3 días. Se indica tomar la presión diariamente."
        },
        {
            "diagnostico": "Insuficiencia cardíaca congestiva estable",
            "sintoma": "Disnea de esfuerzos moderados, edema de extremidades inferiores vespertino y ortopnea.",
            "observacion": "Se ajusta dosis de diuréticos. Se solicita ecocardiograma Doppler color de control urgente."
        }
    ],
    "Diabetología": [
        {
            "diagnostico": "Diabetes Mellitus Tipo 2",
            "sintoma": "Polidipsia, poliuria, pérdida de peso y visión borrosa.",
            "observacion": "Se solicita perfil bioquímico de control y hemoglobina glicosilada urgente."
        },
        {
            "diagnostico": "Hipotiroidismo primario subclínico",
            "sintoma": "Somnolencia constante, intolerancia al frío, piel xerótica y caída de cabello severa.",
            "observacion": "Se constata TSH elevada en exámenes previos. Se inicia sustitución hormonal con levotiroxina."
        }
    ],
    "Broncopulmonar": [
        {
            "diagnostico": "Asma bronquial en crisis moderada",
            "sintoma": "Disnea de esfuerzo, sibilancias espiratorias y opresión torácica.",
            "observacion": "Mantener inhalador de rescate a mano. Control en su consultorio correspondiente."
        },
        {
            "diagnostico": "Enfermedad Pulmonar Obstructiva Crónica (EPOC) reagudizada",
            "sintoma": "Aumento de la disnea basal, tos crónica con expectoración mucopurulenta y fatiga al caminar.",
            "observacion": "Se indica terapia con broncodilatadores de larga acción y pauta de corticoides orales por 5 días."
        }
    ],
    "Gastroenterología": [
        {
            "diagnostico": "Gastritis crónica erosiva",
            "sintoma": "Dolor epigástrico punzante, náuseas y acidez postprandial.",
            "observacion": "Se sugiere evitar alimentos irritantes, grasas y café. Evaluar en 2 semanas."
        },
        {
            "diagnostico": "Síndrome de Intestino Irritable (SII) variante dolor/meteorismo",
            "sintoma": "Distensión abdominal vespertina, dolor cólico aliviado tras la defecación y alteración del hábito intestinal.",
            "observacion": "Se indica pauta alimentaria baja en FODMAPs y tratamiento sintomático. Evaluar evolución."
        }
    ],
    "Traumatología": [
        {
            "diagnostico": "Esguince de tobillo grado 1",
            "sintoma": "Dolor localizado, inflamación moderada y dificultad para la marcha.",
            "observacion": "Se indica uso de tobillera compresiva y aplicar hielo local por 15 minutos."
        },
        {
            "diagnostico": "Lumbago mecánico agudo",
            "sintoma": "Dolor lumbar que se irradia a zona glútea, rigidez matutina.",
            "observacion": "Se deriva a kinesiología para evaluación y manejo. Evitar cargas pesadas."
        }
    ],
    "Medicina General": [
        {
            "diagnostico": "Gripe por influenza",
            "sintoma": "Mialgias generalizadas, escalofríos, odinofagia y decaimiento.",
            "observacion": "Cuadro viral estacional. Manejo sintomático con paracetamol cada 8 horas."
        },
        {
            "diagnostico": "Faringoamigdalitis bacteriana",
            "sintoma": "Odinofagia severa, adenopatías cervicales inflamadas y fiebre.",
            "observacion": "Inicia tratamiento antibiótico. Si presenta rash cutáneo, suspender de inmediato."
        }
    ],
    "Psiquiatría": [
        {
            "diagnostico": "Ansiedad generalizada",
            "sintoma": "Palpitaciones, insomnio de conciliación, irritabilidad y sudoración.",
            "observacion": "Se sugiere apoyo psicoterapéutico complementario y técnicas de respiración."
        },
        {
            "diagnostico": "Episodio depresivo moderado",
            "sintoma": "Anhedonia, humor deprimido la mayor parte del día, astenia marcada y fallas de concentración.",
            "observacion": "Se inicia tratamiento farmacológico con inhibidores de la recaptación de serotonina (ISRS). Control en 3 semanas."
        }
    ],
    # -------------
    "Pediatría": [
        {
            "diagnostico": "Faringoamigdalitis aguda sintomática",
            "sintoma": "Fiebre alta de 39°C, odinofagia severa, rechazo alimentario y decaimiento.",
            "observacion": "Se constatan placas pultáceas en amígdalas. Inicia amoxicilina, control en 48 horas."
        },
        {
            "diagnostico": "Bronquitis aguda no especificada",
            "sintoma": "Tos obstructiva intermitente, fiebre moderada, rinorrea saniosa y sibilancias.",
            "observacion": "Se indica esquema de salbutamol cada 4 horas y aseo nasal frecuente. Indicar signos de alerta."
        }
    ],
    "Ginecología": [
        {
            "diagnostico": "Síndrome de Ovario Poliquístico (SOP)",
            "sintoma": "Amenorrea secundaria, episodios de menorragia dolorosa, acné y aumento de vello.",
            "observacion": "Se solicita ecografía transvaginal de control y perfil androgénico completo."
        },
        {
            "diagnostico": "Candidiasis vulvovaginal aguda",
            "sintoma": "Prurito vaginal intenso, disuria, eritema local y leucorrea grumosa blanquecina.",
            "observacion": "Tratamiento con óvulos de clotrimazol por 3 días. Se sugieren medidas higiénicas generales."
        }
    ],
    "Dermatología": [
        {
            "diagnostico": "Dermatitis atópica severa",
            "sintoma": "Prurito intenso, lesiones eccematosas, descamación y xerosis cutánea generalizada.",
            "observacion": "Se recetan corticoides tópicos y cremas emolientes abundantes. Evitar baños prolongados."
        },
        {
            "diagnostico": "Acné vulgar moderado papulopastuloso",
            "sintoma": "Presencia de numerosos comedones, pápulas inflamatorias y quistes en zona T facial y espalda.",
            "observacion": "Inicia terapia combinada con gel tópico nocturno y antibiótico oral por 6 semanas."
        }
    ],
    "Oftalmología": [
        {
            "diagnostico": "Conjuntivitis bacteriana aguda",
            "sintoma": "Ojo rojo, secreción mucopurulenta abundante, sensación de cuerpo extraño y fotofobia.",
            "observacion": "Se prescribe colirio antibiótico cada 4 horas por 7 días. Lavado de manos estricto."
        },
        {
            "diagnostico": "Vicio de refracción (Astigmatismo miópico)",
            "sintoma": "Cefalea holocraneal vespertina, visión borrosa de lejos y fatiga ocular al leer.",
            "observacion": "Se realiza refracción clínica. Se extiende receta médica para uso permanente de lentes."
        }
    ],
    "Odontología": [
        {
            "diagnostico": "Caries dentinaria profunda con pulpitis reversible",
            "sintoma": "Dolor agudo localizado provocado por estímulos térmicos (dulce o frío) en pieza 4.6.",
            "observacion": "Se realiza remoción de tejido cariado y restauración definitiva con resina compuesta."
        },
        {
            "diagnostico": "Gingivitis crónica asociada a placa bacteriana",
            "sintoma": "Sangrado gingival espontáneo durante el cepillado, halitosis y tumefacción de encías.",
            "observacion": "Se realiza destartraje supra y subgingival mas profilaxis. Instrucción de técnica de higiene."
        }
    ],
    "Neurología": [
        {
            "diagnostico": "Migraña con aura visual",
            "sintoma": "Cefalea pulsátil unilateral intensa, náuseas, fotofobia y escotomas centelleantes previos.",
            "observacion": "Paciente refiere crisis recurrentes. Se indica tratamiento de rescate con triptanes."
        },
        {
            "diagnostico": "Síndrome de túnel carpiano bilateral",
            "sintoma": "Parestesias e hipoestesia nocturna en territorio del nervio mediano de ambas manos.",
            "observacion": "Se solicita electromiografía de extremidades superiores para confirmar grado de compresión."
        }
    ],
    "Oncología": [
        {
            "diagnostico": "Seguimiento de Adenocarcinoma de colon Dukes B",
            "sintoma": "Paciente asintomático en control postquirúrgico, refiere estabilidad ponderal.",
            "observacion": "Se solicitan marcadores tumorales (CEA) y tomografía computada de tórax, abdomen y pelvis."
        },
        {
            "diagnostico": "Evaluación por Síndrome Consuntivo en estudio",
            "sintoma": "Baja de peso involuntaria del 15% en 3 meses, astenia, adinamia y anorexia marcada.",
            "observacion": "Se hospitaliza para agilizar estudios imagenológicos avanzados y toma de biopsias corporales."
        }
    ],
    "Nutrición": [
        {
            "diagnostico": "Obesidad grado I y Resistencia a la Insulina",
            "sintoma": "Fatiga crónica, acantosis nigricans en cuello y dificultad para la pérdida de peso.",
            "observacion": "Se prescribe pauta alimentaria hipocalórica estructurada y pauta de ejercicio aeróbico progresivo."
        },
        {
            "diagnostico": "Dislipidemia mixta severa",
            "sintoma": "Paciente asintomático, detectado en exámenes de medicina preventiva de rutina.",
            "observacion": "Se entrega plan nutricional con restricción estricta de grasas saturadas y azúcares refinados."
        }
    ],
}

# Creamos la clase para el proveedor personalizado para Faker.
class ClinicaProvider(BaseProvider):
    # Método que recibe la especialidad y extrae una fila coherente.
    # Este es el método que utilizaremos para utlizar en el fake del metodo 
    # insertar_historial_paciente_registrado.
    def historial_por_especialidad(self, nombre_especialidad):
        # Si la especialidad no está en el diccionario, usamos 'Medicina General' como respaldo por seguridad
        casos_disponibles = DATOS_CLINICOS_POR_ESPECIALIDAD.get(nombre_especialidad, DATOS_CLINICOS_POR_ESPECIALIDAD["Medicina General"])
        
        # Elige al azar una de las opciones configuradas para esa especialidad y la retornamos.
        return random.choice(casos_disponibles)
# La agregamos a nuestro provider.
# Sirve para registrar mi clase personalizada, esta Clase creada.
fake.add_provider(ClinicaProvider)