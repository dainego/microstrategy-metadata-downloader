# Punto de entrada del descargador de metadata de MicroStrategy.
# Coordina la selección del proyecto, la autenticación, la consulta de
# atributos, el aplanamiento de sus detalles y la exportación a TXT y JSON.

# Bibliotecas estándar de Python: fechas, salida del programa y registros.
from datetime import datetime
import sys
import logging

# Funciones de los módulos internos del proyecto.
from utils import setup_logger
from exporters import write_to_json, write_to_text
from metadata import (
    get_all_attribute_details, 
    flatten_attribute_details, 
    build_folder_map, 
    list_objects)
from microstrategy_client import get_auth_token, logout


# Configuración central: conexión, credenciales, rutas y objetos disponibles.
# Importar config también carga .env y crea las carpetas que define ese módulo.
from config import (
    BASE_URL,
    ACCOUNT_ID,
    ACCOUNT_PASSWORD,
    APP_NAME,
    LOG_FOLDER,
    RESULTS_FOLDER,
    OBJECT_TYPE_ATTRIBUTE,
    OBJECT_SUBTYPE_ATTRIBUTE,
    PROJECTS
)

# Identificadores asociados a las opciones del menú.
# Cada proyecto tiene un ID y una carpeta raíz para buscar atributos.
project_id_big_data = PROJECTS["1"]["project_id"]
project_id_muc = PROJECTS["2"]["project_id"]
root_attributes_big_data = PROJECTS["1"]["attribute_root"]
root_attributes_muc = PROJECTS["2"]["attribute_root"]

# Tipo y subtipo utilizados para seleccionar los atributos que se descargarán.
object_type_attribute = OBJECT_TYPE_ATTRIBUTE
object_subtype_attribute = OBJECT_SUBTYPE_ATTRIBUTE
# Estos tres tipos están declarados, pero no se utilizan en el flujo actual.
object_type_metric = 4
object_type_filter = 1
object_type_fact = 13

# Alias de los parámetros de conexión cargados desde config.py.
# No se deben registrar la contraseña ni el token de sesión en los logs.
base_url = BASE_URL
account_id = ACCOUNT_ID
account_psw = ACCOUNT_PASSWORD

# Nombre del archivo de registro, con fecha y hora local del proceso.
# El timestamp se calcula al cargar este módulo y también se usa en las
# exportaciones; no se recalcula si main() se llama varias veces en el proceso.
app_name=APP_NAME
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"{APP_NAME}_{timestamp}.txt"

# Rutas de los archivos de registro y de los resultados exportados.
log_folder = LOG_FOLDER
results_folder = RESULTS_FOLDER

# Asegura que las carpetas existan antes de escribir archivos.
# Estas instrucciones también se ejecutan si otro módulo importa main.
# exist_ok=True permite reutilizar carpetas creadas previamente por config.py.
log_folder.mkdir(parents=True, exist_ok=True)
results_folder.mkdir(parents=True, exist_ok=True)

# Nivel mínimo del logger y de los manejadores que se creen: DEBUG incluye
# mensajes de depuración y los niveles de mayor prioridad.
log_level = logging.DEBUG


def main():

    """
    Ejecuta el flujo interactivo de descarga y exportación de atributos.

    Parámetros:
        No recibe argumentos; usa la configuración de este módulo y la opción
        de proyecto ingresada por el usuario en la consola.

    Retorno:
        None al completar el flujo. La opción 3 finaliza mediante sys.exit().

    Flujo:
        1. Configura el logger y solicita el proyecto.
        2. Inicia una sesión en MicroStrategy.
        3. Consulta los objetos y filtra por el subtipo configurado.
        4. Reconstruye las rutas de carpetas y descarga los detalles.
        5. Genera los registros planos y los exporta a TXT/JSON.
        6. Solicita el cierre de la sesión y registra el fin del proceso.

    Consideraciones:
        Una opción inválida produce ValueError. Los errores no capturados
        interrumpen la ejecución. Como logout() no está en un bloque finally,
        un error anterior puede impedir que se solicite el cierre de sesión.
    """

    # Inicializa el registro de mensajes en consola y archivo.
    logger = setup_logger(name=app_name, log_file=log_folder / log_file, level=log_level)
    logger.info("Start of the script")

    # Presenta las opciones disponibles. Se conservan los textos originales
    # del menú y de los logs; esta versión solo modifica la documentación.
    print("Select what to process:")
    print("1) Big Data")
    print("2) MUC")
    print("3) Exit")

    option = input("Enter option (1, 2, or 3): ")

    # Asigna los identificadores correspondientes al proyecto elegido.
    # La entrada se compara literalmente; no se eliminan espacios adicionales.
    if option == "1":
        project_id = project_id_big_data
        root_attributes = root_attributes_big_data
        logger.info("Processing Big Data project")
    elif option == "2":
        project_id = project_id_muc
        root_attributes = root_attributes_muc
        logger.info("Processing MUC project")
    elif option == "3":
        logger.info("User chose to exit the script.")
        sys.exit()
    else:
        logger.error("Invalid option. Please select 1, 2, or 3.")
        raise ValueError("Invalid option selected.")

    # Obtiene el token y las cookies que se usarán en las llamadas posteriores.
    logger.info("Authenticating")
    auth_token, cookies = get_auth_token(base_url, logger, account_id, account_psw, project_id)
    logger.info("Authentication successful")

    # Recupera la lista de atributos y el árbol para reconstruir sus carpetas.
    logger.info("Retrieving attribute list")
    attribute_list, attribute_tree  = list_objects(base_url, auth_token, cookies, logger, project_id, object_type_attribute, root_attributes)
    

    # Conserva únicamente los objetos cuyo subtipo coincide con el configurado.
    # Los demás subtipos quedan fuera de la consulta de detalles.
    attribute_ids = [
        obj["id"]
        for obj in attribute_list
        if obj.get("subtype") == object_subtype_attribute
        ]
    # Este mensaje informa el total original, antes del filtro de subtipo.
    logger.info(f"Retrieved {len(attribute_list)} attributes")

    # Construye el mapa ID -> carpeta y consulta los atributos seleccionados.
    logger.info("Retrieving attribute details")
    folder_map = build_folder_map(attribute_tree, attribute_ids)
    attributes_details = get_all_attribute_details(base_url, auth_token, cookies, logger,project_id, attribute_ids)

    # Convierte las estructuras anidadas en registros planos exportables.
    flat_attributes = flatten_attribute_details(attributes_details, folder_map)
    # Usa el mismo timestamp para relacionar ambos archivos con el log.
    write_to_text(flat_attributes, results_folder / f"flat_attributes_{timestamp}.txt", "|")
    write_to_json(flat_attributes, results_folder / f"flat_attributes_{timestamp}.json")

    # El contador sigue usando la lista original: no representa necesariamente
    # la cantidad de detalles descargados con éxito ni la cantidad de filas.
    logger.info(f"Retrieved details for {len(attribute_list)} attributes")

    # Solicita el cierre de sesión al terminar normalmente la exportación.
    logout(base_url, auth_token, cookies, logger)
    
    logger.info("End of the script")

# Ejecuta el flujo interactivo solo al iniciar este archivo directamente.
# Al importarlo no se llama a main(), aunque sí se ejecuta el código global.
if __name__ == "__main__":
    main()
