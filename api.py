"""API REST local para ejecutar descargas de metadata.
Define la interfaz REST de la aplicación mediante FastAPI.
Expone los endpoints HTTP que permiten:
-Solicitar la descarga de metadata
-Consultar el estado de los trabajos
-Descargar los archivos generados
También administra la ejecución de los procesos en segundo plano y mantiene sus estados:
queued, running, completed y failed de forma segura ante accesos concurrentes.

api.py recibe solicitudes HTTP y administra los trabajos y service.py realiza el trabajo concreto.

Tiene logger aparte de service.py

Limitaciones:
- Los estados se pierden al reiniciar el servidor.
- No incluye autenticación: usar únicamente en localhost.
- Ejecutar con un solo worker.
"""

import logging

# Modulo incorporado de Python que proporciona primitivas de sincronización para
# permitir que múltiples subprocesos trabajen dentro del mismo proceso.
# Los subprocesos comparten memoria, incluidas variables y diccionarios.
from threading import Lock 

# Modulo incorporado de Python para generar identificadores únicos universales (UUIDs),
# que se utilizan para identificar de manera única los trabajos de descarga en la API.
from uuid import uuid4 

# Framework para construir APIs web. Permite que otros programas llamen a tu funcionalidad de Python
# a través de solicitudes HTTP.
from fastapi import BackgroundTasks, FastAPI, HTTPException 
from fastapi.responses import FileResponse

# Librería para la validación de datos y la creación de modelos de datos en Python.
from pydantic import BaseModel, StrictInt
from typing import Literal

# Funciones de los módulos internos del proyecto.
import config
from service import download_metadata
from utils import setup_logger


# Configura el logger para registrar errores y advertencias en un archivo.
logger = setup_logger(
    name=f"{config.APP_NAME}.api",
    log_file=config.LOG_FOLDER / f"{config.APP_NAME}_api.log",
    level=logging.INFO,
)

# Evitar que los mensajes de registro se propaguen a los loggers padres,
# lo que podría causar duplicación de mensajes en la salida del registro.
logger.propagate = False

# Diccionario que almacena el estado de los trabajos de descarga,
# incluyendo su identificador, clave de proyecto, estado y resultados.
jobs = {}

# Objeto de bloqueo que asegura que solo un hilo pueda acceder y modificar el diccionario
# de trabajos a la vez, evitando condiciones de carrera y garantizando la coherencia de los datos.
# jobs_lock es una instancia de Lock.
jobs_lock = Lock() 



class DownloadRequest(BaseModel):
    """
    Clase que define la estructura de los datos necesarios para solicitar una descarga de metadata.
    """
    # Clave del proyecto de MicroStrategy del cual se descargará la metadata.
    project_key: str
    # Tipo de objeto solicitado. StrictInt evita aceptar booleanos o texto como enteros.
    # El valor predeterminado 12 conserva la descarga de atributos.
    object_type: StrictInt = 12


def execute_download(job_id: str, project_key: str, object_type: int):
    """
    Función que ejecuta el servicio de descarga de metadata y registra su # resultado en el diccionario de trabajos.
    """
    # Actualiza el estado del trabajo a "running" antes de iniciar la descarga.
    # El bloque with jobs_lock bloquea el acceso al diccionario de trabajos mientras se actualiza el estado,
    # evitando que otros hilos lean o escriban en el diccionario al mismo tiempo.
    # Solo un hilo a la vez puede actualizar el diccionario de trabajos (jobs).
    # Si un hilo esta actualizando los demás deben esperar.
    with jobs_lock:
        jobs[job_id]["status"] = "running"

    # Se ejecuta una vez actualizado el estado del trabajo, para que otros hilos puedan leerlo y saber que la descarga está en progreso.
    # Intenta ejecutar la función download_metadata de service.py y captura cualquier excepción que ocurra.
    try:
        result = download_metadata(project_key, object_type)

    except Exception as exc:
        # No publica el texto de la excepción ni posibles datos sensibles.
        logger.error("Falló el trabajo %s (%s).", job_id, type(exc).__name__)


        with jobs_lock:
            jobs[job_id].update({
                "status": "failed",
                "error": "La descarga falló. Revisá los logs del servidor.",
            })

    else:
        with jobs_lock:
            jobs[job_id].update({
                "status": result["status"],
                "result": result,
            })

# Define la instancia de la aplicación FastAPI, con un título y
# una versión para la documentación automática de la API.
app = FastAPI(
    title="MicroStrategy Metadata Downloader",
    version="0.1.0",
) 

# @ indica que se está definiendo un decorador, que es una función que modifica el comportamiento de otra función.
# app es la instancia de la clase FastAPI definida mas arriba
# post es un método de app que registra una ruta para manejar solicitudes HTTP POST.
# /jobs es la dirección del endpoint
# status_code = 202 indica que la solicitud fue aceptada para ejecutarse en segundo plano
# con este decorador le indicamos a FastAPI que cuando reciba un solicitud POST en la ruta "/jobs"
# ejecute la función create_job y devuelva un código de estado 202 (Accepted) si la solicitud es válida.
# Endpoint para crear un nuevo trabajo de descarga de metadata.
@app.post("/jobs", status_code=202)
def create_job(
    request: DownloadRequest, #El parametro request es un objeto de la clase DownloadRequest que contiene la clave del proyecto y el tipo de objeto.
    background_tasks: BackgroundTasks, #El parametro background_tasks es un objeto que permite ejecutar tareas en segundo plano, como la descarga de metadata, sin bloquear la respuesta al cliente.
):
    """Solicita una descarga y devuelve su identificador."""

    # Verifica que la clave del proyecto proporcionada exista en la configuración de proyectos válidos.
    if request.project_key not in config.PROJECTS:
        raise HTTPException(
            status_code=400,
            detail="El proyecto solicitado no existe.",
        )

    # Valida el tipo permitido y la raíz configurada antes de crear el trabajo.
    try:
        settings = config.get_object_settings(request.object_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    if not config.PROJECTS[request.project_key].get(settings["root_key"]):
        raise HTTPException(status_code=400, detail=f"Falta configurar {settings['root_key']} para el proyecto.")

    job_id = uuid4().hex #Genera un identificador único para el trabajo de descarga.

    with jobs_lock:
        # Verifica si ya hay un trabajo en ejecución (con estado "queued" o "running").
        if any(
            job["status"] in {"queued", "running"}
            for job in jobs.values()
        ):
            raise HTTPException(
                status_code=409,
                detail="Ya hay una descarga en ejecución.",
            )

        # Agrega el nuevo trabajo al diccionario de trabajos con estado "queued".
        jobs[job_id] = {
            "job_id": job_id,
            "project_key": request.project_key,
            "object_type": request.object_type,
            "status": "queued",
        }

    # Agrega la tarea de descarga a la cola de tareas en segundo plano,
    # pasando el identificador del trabajo, la clave del proyecto y el tipo de objeto.
    background_tasks.add_task(
        execute_download, #funcion que invoca a download_metadata de service.py
        job_id,
        request.project_key,
        request.object_type,
    )

    # Devuelve una respuesta JSON con el identificador del trabajo y su estado inicial "queued".
    return {
        "job_id": job_id,
        "status": "queued",
    }

# Endpoint para obtener el estado y un resumen de un trabajo de descarga específico.
@app.get("/jobs/{job_id}")

def get_job(job_id: str):

    """Devuelve el estado y un resumen sin rutas internas del servidor."""

    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Trabajo no encontrado.",
            )

        result = job.get("result")
        response = {
            "job_id": job_id,
            "project_key": job["project_key"],
            "object_type": job["object_type"],
            "status": job["status"],
        }

        if "error" in job:
            response["error"] = job["error"]

        if result is not None:
            response["summary"] = {
                "project_name": result["project_name"],
                "objects_downloaded": result["objects_downloaded"],
                "objects_failed": result["objects_failed"],
                "rows_exported": result["rows_exported"],
                "duration_seconds": result["duration_seconds"],
                "warnings": result["warnings"],
            }
            response["result_url"] = f"/jobs/{job_id}/result"

    return response

# Endpoint para descargar el resultado de un trabajo de descarga finalizado.
@app.get("/jobs/{job_id}/result")
def get_result(job_id: str, format: Literal["json", "txt"] = "json"):
    """Descarga el JSON de un trabajo finalizado."""

    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Trabajo no encontrado.",
            )

        if job["status"] not in {
            "completed",
            "completed_with_warnings",
        }:
            raise HTTPException(
                status_code=409,
                detail="El resultado todavía no está disponible.",
            )

        # La ruta proviene del servicio, nunca de un parámetro del usuario.
        file_path = job["result"]["files"][format]

    # Devuelve el archivo JSON o TXT solicitado como respuesta, con el tipo de medio adecuado y un nombre de archivo que
    # incluye el identificador del trabajo.
    return FileResponse(
        path=file_path,
        media_type="application/json" if format == "json" else "text/plain",
        filename=f"metadata_{job_id}.{format}",
    )
