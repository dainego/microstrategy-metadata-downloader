"""Servicio síncrono de descarga, reutilizable desde consola o un futuro worker.
No solicita datos por consola ni inicia trabajos en segundo plano. Devuelve un
diccionario serializable a JSON al terminar; los errores del proceso se propagan.
No es todavía una API HTTP ni un administrador persistente de trabajos.
"""

# Modulos incorporado de Python
import logging
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter # Contador de alta resolución para medir el tiempo transcurrido en segundos.
from uuid import uuid4

# Funciones de los módulos internos del proyecto.
from exporters import write_to_json, write_to_text
from metadata import (
    build_folder_map,
    flatten_object_details,
    COMMON_FIELDS, TYPE_FIELDS,
    get_all_object_details,
    list_objects,
)
from microstrategy_client import MicroStrategyClient
from utils import setup_logger


def download_metadata(project_key, object_type=12, logger=None):
    """Descarga un tipo de objeto y devuelve archivos, contadores y advertencias."""
    # Carga config al invocar el servicio, no al importar este módulo.
    import config

    # Obtiene endpoint, parámetros, carpeta raíz y prefijo para el tipo solicitado.
    settings = config.get_object_settings(object_type)

    # Genera un identificador único para la ejecución, usado en nombres de archivos y logs.
    run_id = uuid4().hex

    # Si no se recibe un logger, crea uno propio con archivo por ejecución y cierra únicamente sus propios manejadores.
    # own_logger será True si no se recibió un logger, y será False si se recibió uno
    own_logger = logger is None
    # Si se crea un logger propio, se asegura de que exista la carpeta de logs y se configura con el nombre del proyecto y el identificador de ejecución.
    run_log = None
    if own_logger:
        log_folder = Path(config.LOG_FOLDER)
        log_folder.mkdir(parents=True, exist_ok=True)
        run_log = log_folder / f"{config.APP_NAME}_{run_id}.log"
        logger = setup_logger(
            name=f"{config.APP_NAME}.{run_id}",
            log_file=run_log,
            level=logging.INFO,
        )
        logger.propagate = False

    client = None
    warnings = []
    logout_confirmed = False
    started_at = datetime.now(timezone.utc).isoformat()
    start = perf_counter()

    # Valida la clave del proyecto y la configuración requerida antes de iniciar la descarga.
    try:
        if not isinstance(project_key, str) or project_key not in config.PROJECTS:
            raise ValueError("El proyecto solicitado no existe en PROJECTS.")
        # Luego de validado el project_key, obtiene la información del proyecto del diccionario PROJECTS de config.py
        project = config.PROJECTS[project_key]

        # Valida que las variables de entorno requeridas estén presentes en config.py antes de iniciar la descarga.
        missing = [
            name for name in ("BASE_URL", "ACCOUNT_ID", "ACCOUNT_PASSWORD") #recorre los nombres de variables de entorno requeridas
            if not getattr(config, name, None) #por cada nombre de variable obtiene el valor de la variable de entorno en config.py, si no existe devuelve None
        ]
        if missing:
            raise ValueError("Falta configuración requerida: " + ", ".join(missing))
        root = project.get(settings["root_key"])
        if not project.get("project_id") or not root:
            raise ValueError(f"El proyecto necesita project_id y {settings['root_key']}.")

        # Loguea el inicio de la ejecución del proyecto con el identificador de ejecución y la clave del proyecto.
        logger.info("Ejecución %s: inicio del proyecto %s.", run_id, project_key)
        output_folder = Path(config.RESULTS_FOLDER) / run_id
        output_folder.mkdir(parents=True, exist_ok=False)

        # Define una instancia de la clase MicrostrategyClient
        client = MicroStrategyClient(config.BASE_URL, project["project_id"], logger) 

        # Inicia sesión en la API de MicroStrategy con las credenciales proporcionadas en config.py
        client.login(config.ACCOUNT_ID, config.ACCOUNT_PASSWORD)

        # Obtiene la lista de objetos y el árbol de carpetas del proyecto, filtrando
        # por object_type y por la carpeta raíz configurada para ese tipo.
        objects, tree = list_objects(
            client, object_type, root
        )

        # Obtiene los IDs únicos de la búsqueda filtrada por tipo y construye
        # un mapa de carpetas a partir del árbol y los identificadores seleccionados.
        object_ids = list(dict.fromkeys(obj["id"] for obj in objects))
        folder_map = build_folder_map(tree, object_ids)

        # Obtiene los detalles de todos los objetos filtrados, y registra los identificadores de aquellos que fallaron en la descarga.
        details = get_all_object_details(client, object_ids, settings)

        failed_ids = [
            object_id for object_id, detail in zip(object_ids, details)
            if detail is None
        ]

        # Cuenta la cantidad de objetos descargados correctamente y lanza un error si no se pudo descargar ningún detalle de los objetos seleccionados.
        downloaded = len(details) - len(failed_ids)
        if object_ids and downloaded == 0:
            raise RuntimeError("No se pudo descargar el detalle de ningún objeto seleccionado.")
        if failed_ids:
            warnings.append(f"Falló la descarga de {len(failed_ids)} objetos.")

        # Convierte los detalles de los objetos descargados en filas exportables, y si no se generaron filas, agrega una advertencia.
        rows = flatten_object_details(details, folder_map, object_type, settings["folder_prefix"])
        if downloaded and not rows:
            warnings.append("Los detalles descargados no generaron filas exportables.")

        # Luego, escribe los resultados en archivos JSON y TXT delimitado por pipe.
        json_path = output_folder / f"flat_{settings['name']}.json"
        write_to_json(rows, json_path)
        # El TXT se genera también sin filas: conserva la cabecera del tipo seleccionado.
        text_path = output_folder / f"flat_{settings['name']}.txt"
        write_to_text(rows, text_path, "|", COMMON_FIELDS + TYPE_FIELDS[object_type])

        # Finalmente, construye un resumen de la ejecución con información relevante, incluyendo el identificador de ejecución,
        # la clave y el nombre del proyecto, la fecha y hora de inicio, la cantidad de objetos encontrados,
        # objetos seleccionados y descargados, objetos fallidos, filas exportadas, rutas de los archivos generados y el archivo de log.
        summary = {
            "run_id": run_id,
            "project_key": project_key,
            "object_type": object_type,
            "object_type_name": settings["name"],
            "project_name": project["name"],
            "started_at": started_at,
            "objects_found": len(objects),
            "objects_selected": len(object_ids),
            "objects_downloaded": downloaded,
            "objects_failed": len(failed_ids),
            "failed_object_ids": failed_ids,
            "rows_exported": len(rows),
            "files": {
                "json": str(json_path.resolve()),
                "txt": str(text_path.resolve()) if text_path is not None else None,
            },
            "log_file": str(run_log.resolve()) if run_log is not None else None,
        }
    except Exception as exc:
        # No registra el texto arbitrario de excepciones que podrían traer secretos.
        logger.error("Ejecución %s: proceso fallido (%s).", run_id, type(exc).__name__)
        raise
    finally:
        # La limpieza nunca reemplaza un error previo de descarga o exportación.
        if client is not None:
            try:
                logout_confirmed = client.logout() is True
                if not logout_confirmed:
                    warnings.append("No se pudo confirmar el cierre de la sesión remota.")
            except Exception as exc:
                logger.error("Ejecución %s: error en logout (%s).", run_id, type(exc).__name__)
                warnings.append("Ocurrió un error al cerrar la sesión remota.")
            finally:
                try:
                    client.close()
                except Exception as exc:
                    logger.error("Ejecución %s: error en close (%s).", run_id, type(exc).__name__)
                    warnings.append("No se pudo confirmar la liberación de recursos locales.")
        for warning in warnings:
            logger.warning("Ejecución %s: %s", run_id, warning)
        logger.info("Ejecución %s: fin del intento de ejecución.", run_id)
        if own_logger:
            for handler in list(logger.handlers):
                logger.removeHandler(handler)
                handler.close()

    # Solo se llega aquí si la descarga y las exportaciones finalizaron.
    summary.update({
        "status": "completed_with_warnings" if warnings else "completed",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(perf_counter() - start, 3),
        "logout_confirmed": logout_confirmed,
        "warnings": warnings,
    })
    return summary
