# Configuración central del descargador de metadata de MicroStrategy.
# Al importar este módulo, se cargan las variables de entorno y se crean
# las carpetas de salida. Las credenciales deben guardarse en .env
# (excluido de Git), no en este archivo.

import os
from pathlib import Path
from dotenv import load_dotenv

# Configuración del entorno
# Calcula las rutas a partir de la ubicación de este archivo, sin depender
# del directorio desde el cual se ejecute la aplicación.
BASE_FOLDER = Path(__file__).resolve().parent
ENV_FILE = BASE_FOLDER / ".env"

# Carga los valores de .env en las variables de entorno del proceso.
load_dotenv(ENV_FILE)

# Parámetros de conexión. os.getenv() devuelve None si la variable no existe.
# Actualmente, este módulo no valida que estos parámetros tengan un valor.
BASE_URL = os.getenv("MSTR_BASE_URL")
ACCOUNT_ID = os.getenv("MSTR_USERNAME")
ACCOUNT_PASSWORD = os.getenv("MSTR_PASSWORD")

# Identificación de la aplicación y rutas de salida
# Los objetos Path se pueden pasar directamente a las funciones que escriben
# los archivos de salida.
APP_NAME = os.getenv("APP_NAME")
LOG_FOLDER = BASE_FOLDER / "logs"
RESULTS_FOLDER = BASE_FOLDER / "results"

# Identificadores de objetos de metadata de MicroStrategy
# El tipo de objeto indica la categoría que se desea recuperar.
OBJECT_TYPE_ATTRIBUTE = int(os.getenv("OBJECT_TYPE_ATTRIBUTE", "12"))
OBJECT_TYPE_METRIC = int(os.getenv("OBJECT_TYPE_METRIC", "4"))
OBJECT_TYPE_FILTER = int(os.getenv("OBJECT_TYPE_FILTER", "1"))
OBJECT_TYPE_FACT = int(os.getenv("OBJECT_TYPE_FACT", "13"))


# Configuración de los proyectos disponibles
# Las claves del diccionario corresponden a las opciones del menú principal.
# name: Nombre del proyecto que se muestra en los mensajes y registros.
# project_id: Identificador del proyecto enviado en las llamadas a la API.
# attribute_root: Identificador de la carpeta raíz de búsqueda de atributos.

PROJECTS = {
    "1": {
        "name": os.getenv("MSTR_PROJECT_1_NAME"),
        "project_id": os.getenv("MSTR_PROJECT_1_ID"),
        "attribute_root": os.getenv("MSTR_PROJECT_1_ATTRIBUTE_ROOT"),
        "metric_root": os.getenv("MSTR_PROJECT_1_METRIC_ROOT"),
        "filter_root": os.getenv("MSTR_PROJECT_1_FILTER_ROOT"),
        "fact_root": os.getenv("MSTR_PROJECT_1_FACT_ROOT"),
    },
    "2": {
        "name": os.getenv("MSTR_PROJECT_2_NAME"),
        "project_id": os.getenv("MSTR_PROJECT_2_ID"),
        "attribute_root": os.getenv("MSTR_PROJECT_2_ATTRIBUTE_ROOT"),
        "metric_root": os.getenv("MSTR_PROJECT_2_METRIC_ROOT"),
        "filter_root": os.getenv("MSTR_PROJECT_2_FILTER_ROOT"),
        "fact_root": os.getenv("MSTR_PROJECT_2_FACT_ROOT"),
    },
}

# Endpoints relativos a MSTR_BASE_URL, que debe terminar en /api.
OBJECT_TYPES = {
    12: {"name": "attributes", "endpoint": "/model/attributes/{object_id}",
         "root_key": "attribute_root", "folder_prefix": "Schema Objects/Attributes", "params": {}},
    4: {"name": "metrics", "endpoint": "/model/metrics/{object_id}",
        "root_key": "metric_root", "folder_prefix": "Public Objects/Metrics", "params": {}},
    1: {"name": "filters", "endpoint": "/model/filters/{object_id}",
        "root_key": "filter_root", "folder_prefix": "Public Objects/Filters", "params": {}},
    13: {"name": "facts", "endpoint": "/model/facts/{object_id}",
         "root_key": "fact_root", "folder_prefix": "Schema Objects/Facts", "params": {}},
}

# Función de utilidad para validar el tipo de objeto y obtener la configuración asociada.
def get_object_settings(object_type):
    """Valida el tipo antes de iniciar cualquier llamada HTTP."""
    if type(object_type) is not int or object_type not in OBJECT_TYPES:
        raise ValueError("object_type debe ser 12, 4, 1 o 13.")
    return OBJECT_TYPES[object_type]
