# Notas

## Ejecución del código

### Main
python main.py --project-key 1 --object-type 12

### Uvicorn
python -m uvicorn api:app --reload
http://127.0.0.1:8000/docs


## Responsabilidades de los Módulos
main.py ──┐
          ├──> service.download_metadata()
api.py ───┘

| Módulo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada desde consola. Interpreta parámetros como proyecto y tipo de objeto, e inicia la descarga. |
| `api.py` | Expone la API REST. Crea trabajos, consulta su estado y permite descargar resultados. |
| `service.py` | Orquesta una descarga completa: valida configuración, inicia sesión, obtiene metadata, la transforma, exporta archivos y cierra la sesión. |
| `microstrategy_client.py` | Define `MicroStrategyClient`, que encapsula la comunicación HTTP con la API de MicroStrategy: login, llamadas autenticadas, logout y manejo de sesión. |
| `metadata.py` | Consulta y procesa la metadata de atributos, métricas, filtros y facts. También reconstruye carpetas, normaliza textos y genera registros planos. |
| `exporters.py` | Escribe los resultados en JSON, TXT delimitado por `|` y, si se habilita, Excel. |
| `config.py` | Carga `.env` y centraliza rutas, tipos de objetos, proyectos, IDs y carpetas raíz. |
| `utils.py` | Funciones reutilizables, como crear loggers, limpiar texto y eliminar saltos de línea problemáticos. |
| `tests/` | Archivos pequeños para probar funciones o módulos de forma aislada. |
| `.env` | Valores específicos del entorno: URL, credenciales, IDs de proyectos y carpetas. No se versiona. |
| `.env.example` | Plantilla pública del `.env`, con nombres de variables y valores de ejemplo. |
| `.gitignore` | Indica a Git qué no debe subir, por ejemplo `.env`, `.venv`, logs y resultados. |
| `requirements.txt` | Lista las bibliotecas necesarias para ejecutar el proyecto. |

## Módulos revisados
config.py -> python -m py_compile config.py
api.py -> python -m py_compile api.py
main.py -> python -m py_compile main.py
service.py -> python -m py_compile service.py
matadta.py -> python -m py_compile metadata.py 
exporters.py -> python -m py_compile exporters.py 
utils.py -> python -m py_compile utils.py 


## Mejoras Futuras

### Función para crear carpetas
Función:
from pathlib import Path


def ensure_folder(folder: Path | str) -> Path:
    """
    Crea una carpeta y sus directorios padre cuando no existen.

    Retorna la ruta como objeto Path.
    """

    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)

    return path

Invocación:
from utils import ensure_folder
log_folder = ensure_folder(config.LOG_FOLDER)


### Módulo de validación
Armar un módulo que valide toda la información de config para
simplificar los módulos