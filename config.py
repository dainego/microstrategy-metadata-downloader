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
# Por defecto, las variables de entorno que ya existen tienen prioridad
# sobre los valores definidos en .env.
load_dotenv(ENV_FILE)

# Parámetros de conexión. os.getenv() devuelve None si la variable no existe.
# Actualmente, este módulo no valida que estos parámetros tengan un valor.
BASE_URL = os.getenv("MSTR_BASE_URL")
ACCOUNT_ID = os.getenv("MSTR_USERNAME")
ACCOUNT_PASSWORD = os.getenv("MSTR_PASSWORD")

# Identificación de la aplicación y rutas de salida
# Los objetos Path se pueden pasar directamente a las funciones que escriben
# los archivos de salida.
APP_NAME = "microstrategy-metadata-downloader"
LOG_FOLDER = BASE_FOLDER / "logs"
RESULTS_FOLDER = BASE_FOLDER / "results"

# Crea las carpetas faltantes al importar este módulo.
# parents=True también crea los directorios superiores que no existan.
# exist_ok=True evita un error si las carpetas ya existen.
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)


# Identificadores de objetos de metadata de MicroStrategy
# El tipo de objeto indica la categoría que se desea recuperar.
# El subtipo de atributo se utiliza para filtrar los resultados de atributos.
OBJECT_TYPE_ATTRIBUTE = 12
OBJECT_SUBTYPE_ATTRIBUTE = 3072
OBJECT_TYPE_METRIC = 4
OBJECT_TYPE_FILTER = 1
OBJECT_TYPE_FACT = 13


# Configuración de los proyectos disponibles
# Las claves del diccionario corresponden a las opciones del menú principal.
# name: Nombre del proyecto que se muestra en los mensajes y registros.
# project_id: Identificador del proyecto enviado en las llamadas a la API.
# attribute_root: Identificador de la carpeta raíz de búsqueda de atributos.
# Actualmente, ambos proyectos tienen configurado el mismo identificador
# de carpeta raíz para la búsqueda de atributos.
PROJECTS = {
    "1": {
        "name": "Big Data",
        "project_id": "86B8BBB711E8A19F0A290080EF251385",
        "attribute_root": "6F55FB47F9974EABA18CB0C5FF46785C"
    },
    "2": {
        "name": "MUC",
        "project_id": "B32C690C11EAEDFDC5090080EF35D25D",
        "attribute_root": "6F55FB47F9974EABA18CB0C5FF46785C"
    }
}

