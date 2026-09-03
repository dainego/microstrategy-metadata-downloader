"""Servicio síncrono de descarga, reutilizable desde consola o un futuro worker.
No solicita datos por consola ni inicia trabajos en segundo plano. Devuelve un
diccionario serializable a JSON al terminar; los errores del proceso se propagan.
No es todavía una API HTTP ni un administrador persistente de trabajos.
"""
#Modulos incorporado de Python
import logging
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter #Función que devuelve el tiempo de CPU en segundos desde un punto de referencia.
from uuid import uuid4

#Funciones de los módulos internos del proyecto.
from exporters import write_to_json, write_to_text
from metadata import (
    build_folder_map,
    flatten_attribute_details,
    get_all_attribute_details,
    list_objects,
)
from microstrategy_client import MicroStrategyClient
from utils import setup_logger


def download_metadata(project_key, logger=None):
    """Descarga los atributos del proyecto y devuelve un resumen de ejecución.

    project_key: Clave de PROJECTS, por ejemplo "1" para Big Data o "2" para MUC.
    logger: Logger opcional del consumidor. Si no se recibe, crea uno propio
        con archivo por ejecución y cierra únicamente sus propios manejadores.

    Genera results/<run_id>/flat_attributes.json y, si hay filas, un TXT.
    El resumen incluye cantidades, advertencias y rutas locales como cadenas.
    No contiene credenciales. Las rutas son internas: una futura API deberá
    ofrecer descargas autorizadas, no exponer directamente el sistema de archivos.

    Si algunos detalles fallan, exporta los restantes con estado
    completed_with_warnings. Si todos fallan, lanza RuntimeError.
    Intenta logout y close incluso ante errores, sin ocultar el error original.
    Si hay un fallo de escritura pueden quedar archivos incompletos en la carpeta
    de esa ejecución; no deben publicarse como resultados exitosos.
    """
    # Carga config al invocar el servicio, no al importar este módulo.
    import config

    # Genera un identificador único para la ejecución, usado en nombres de archivos y logs.
    run_id = uuid4().hex

    # Si no se recibe un logger, crea uno propio con archivo por ejecución y cierra únicamente sus propios manejadores.
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
        project = config.PROJECTS[project_key]
        missing = [
            name for name in ("BASE_URL", "ACCOUNT_ID", "ACCOUNT_PASSWORD")
            if not getattr(config, name, None)
        ]
        if missing:
            raise ValueError("Falta configuración requerida: " + ", ".join(missing))
        if not project.get("project_id") or not project.get("attribute_root"):
            raise ValueError("El proyecto necesita project_id y attribute_root.")

        logger.info("Ejecución %s: inicio del proyecto %s.", run_id, project_key)
        output_folder = Path(config.RESULTS_FOLDER) / run_id
        output_folder.mkdir(parents=True, exist_ok=False)

        # Una instancia por ejecución: no se comparten tokens o cookies entre jobs.
        client = MicroStrategyClient(config.BASE_URL, project["project_id"], logger)
        client.login(config.ACCOUNT_ID, config.ACCOUNT_PASSWORD)
        objects, tree = list_objects(
            client, config.OBJECT_TYPE_ATTRIBUTE, project["attribute_root"]
        )
        attribute_ids = [
            obj["id"] for obj in objects
            if obj.get("subtype") == config.OBJECT_SUBTYPE_ATTRIBUTE
        ]
        folder_map = build_folder_map(tree, attribute_ids)
        details = get_all_attribute_details(client, attribute_ids)
        failed_ids = [
            object_id for object_id, detail in zip(attribute_ids, details)
            if detail is None
        ]
        downloaded = len(details) - len(failed_ids)
        if attribute_ids and downloaded == 0:
            raise RuntimeError("No se pudo descargar el detalle de ningún atributo seleccionado.")
        if failed_ids:
            warnings.append(f"Falló la descarga de {len(failed_ids)} atributos.")

        rows = flatten_attribute_details(details, folder_map)
        if downloaded and not rows:
            warnings.append("Los detalles descargados no generaron filas exportables.")
        json_path = output_folder / "flat_attributes.json"
        write_to_json(rows, json_path)
        # El exportador TXT actual no crea archivos con una lista vacía.
        text_path = None
        if rows:
            text_path = output_folder / "flat_attributes.txt"
            write_to_text(rows, text_path, "|")

        summary = {
            "run_id": run_id,
            "project_key": project_key,
            "project_name": project["name"],
            "started_at": started_at,
            "objects_found": len(objects),
            "attributes_selected": len(attribute_ids),
            "attributes_downloaded": downloaded,
            "attributes_failed": len(failed_ids),
            "failed_attribute_ids": failed_ids,
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