# Funciones de exportación de datos a archivos JSON, CSV y texto delimitado.
# Las rutas pueden recibirse como cadenas o como objetos Path.
# La carpeta de destino debe existir antes de llamar a estas funciones.
# El modo "w" reemplaza el contenido de un archivo existente.
# Los errores de escritura se propagan al código que llama a la función.


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