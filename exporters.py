"""Exportación UTF-8 a JSON y texto delimitado por pipe."""
# Funciones de exportación de datos a archivos JSON y texto delimitado.
# Las rutas pueden recibirse como cadenas o como objetos Path.
# La carpeta de destino debe existir antes de llamar a estas funciones.
# El modo "w" reemplaza el contenido de un archivo existente.
# Los errores de escritura se propagan al código que llama a la función.
import csv
import json
from utils import clean_text


def write_to_json(data, file_path, indent=4):
    # El bloque with cierra el archivo automáticamente, incluso ante un error.
    # Una lista vacía se escribe como [], sin omitir la creación del archivo.
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)


def write_to_text(data, file_path, separator='|', fieldnames=None):
    """Las comillas protegen pipes dentro de valores; sin datos escribe la cabecera."""
    # Usa las columnas indicadas o las del primer registro cuando hay datos.
    # Evita acceder al primer registro cuando la lista está vacía.
    fields = list(fieldnames or (data[0].keys() if data else []))
    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        # Conserva el orden de las columnas para todos los registros.
        # El escritor coloca comillas cuando un campo contiene el separador pipe.
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=separator, lineterminator='\n')
        # Escribe la cabecera con los nombres de las columnas, incluso sin filas.
        if fields:
            writer.writeheader()
        for row in data:
            # Los valores None y las claves ausentes se representan como campos vacíos.
            # Los demás valores se convierten a texto; clean_text normaliza los textos.
            writer.writerow({key: clean_text(value) if isinstance(value, str) else value
                             for key, value in row.items()})
