# Funciones de exportación de datos a archivos JSON, CSV y texto delimitado.
# Las rutas pueden recibirse como cadenas o como objetos Path.
# La carpeta de destino debe existir antes de llamar a estas funciones.
# El modo "w" reemplaza el contenido de un archivo existente.
# Los errores de escritura se propagan al código que llama a la función.

import csv
import json


def write_to_json(data, 
                  file_path, 
                  indent=4):
    """
    Exporta una estructura de datos de Python a un archivo JSON.

    Parámetros:
        data: Datos compatibles con JSON, como listas y diccionarios.
        file_path: Ruta del archivo de destino.
        indent: Cantidad de espacios de sangría; por defecto, 4.

    Retorno:
        None. El resultado se escribe en el archivo indicado.
    """
    # Evita acceder al primer registro cuando no hay datos.
    if not data:
        return
    
    # El bloque with cierra el archivo automáticamente, incluso ante un error.
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=indent,
            ensure_ascii=False
        )


def write_to_csv(data, file_path):
    """
    Exporta una lista de diccionarios a un archivo CSV separado por comas.

    Parámetros:
        data: Lista no vacía de diccionarios. Las claves del primero
            definen las columnas y su orden.
        file_path: Ruta del archivo de destino.

    Retorno:
        None. El resultado se escribe en el archivo indicado.

    Consideraciones:
        Una lista vacía produce IndexError después de abrir el archivo.
        Las claves adicionales en filas posteriores producen ValueError.
        Los campos ausentes y los valores None se escriben como celdas vacías.
    """
    # Evita acceder al primer registro cuando no hay datos.
    if not data:
        return
    
    # newline="" permite que csv gestione los saltos de línea.
    # utf-8-sig incluye una marca BOM que facilita la detección de UTF-8
    # al abrir el archivo en aplicaciones como Excel.
    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:

        # DictWriter asigna cada valor a la columna indicada por su clave
        # y aplica las comillas necesarias para el formato CSV.
        writer = csv.DictWriter(
            csv_file,
            fieldnames=data[0].keys()
        )

        writer.writeheader()
        writer.writerows(data)


def write_to_text(data, file_path, separator="|"):
    """
    Exporta una lista de diccionarios a un archivo de texto delimitado.

    Parámetros:
        data: Lista de diccionarios con los registros que se exportarán.
        file_path: Ruta del archivo de destino.
        separator: Separador de columnas; por defecto, el carácter "|".

    Retorno:
        None. Si no hay datos, no crea ni modifica el archivo.

    Consideraciones:
        Las claves del primer registro definen las columnas y su orden.
        Las claves adicionales en registros posteriores no se exportan.
        No elimina ni escapa separadores o saltos de línea en los valores;
        estos deben tratarse previamente si pueden alterar el formato.
    """

    # Evita acceder al primer registro cuando no hay datos.
    if not data:
        return

    fieldnames = data[0].keys()

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        # Escribe la cabecera con los nombres de las columnas.
        file.write(
            separator.join(fieldnames) + "\n"
        )

        # Conserva el orden de las columnas para todos los registros.
        for row in data:
            # Los valores None y las claves ausentes se representan como
            # campos vacíos. Los demás valores se convierten a texto.
            values = [
                "" if row.get(field) is None else str(row.get(field))
                for field in fieldnames
            ]

            file.write(
                separator.join(values) + "\n"
            )