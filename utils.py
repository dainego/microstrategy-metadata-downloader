# Utilidades generales del descargador de metadata:
# configuración de registros de ejecución y normalización de textos.

import logging
from pathlib import Path


def setup_logger(
    name: str,
    log_file: Path | str,
    level: int = logging.INFO
) -> logging.Logger:

    """
    Configura un logger con salida a consola y, si se indica, a un archivo.

    Parámetros:
        name: Nombre que identifica al logger dentro del proceso.
        log_file: Ruta del archivo como objeto Path o cadena. Una cadena
            vacía omite la salida a archivo. La carpeta debe existir.
        level: Nivel mínimo de los mensajes; por defecto, logging.INFO.

    Retorno:
        Objeto logging.Logger para registrar mensajes con info(), warning(),
        error(), debug() y otros métodos del módulo logging.

    Consideraciones:
        Si el logger ya tiene manejadores propios, se reutilizan sin cambiar
        sus destinos, formatos ni niveles; solo se actualiza el nivel del
        logger. La función no modifica la propagación a loggers superiores.
    """

     # Obtiene el logger existente con este nombre o crea uno nuevo.
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita agregar manejadores duplicados en llamadas posteriores.
    if logger.handlers:
        return logger

    # Formato de cada registro: fecha y hora | nivel | mensaje.
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Envía los mensajes a la consola; StreamHandler usa stderr por defecto.
    # El logger y cada manejador aplican sus respectivos filtros de nivel.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

     # Agrega salida a archivo únicamente cuando la ruta tiene un valor.
    if log_file:
        # FileHandler agrega registros al final del archivo por defecto.
        # UTF-8 permite conservar tildes, eñes y otros caracteres Unicode.
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def clean_text(value: str | None) -> str | None:
    """
    Normaliza los espacios en blanco de un texto para dejarlo en una línea.

    Parámetros:
        value: Texto que se desea limpiar, o None si no hay un valor.

    Retorno:
        Texto sin espacios iniciales o finales, con saltos de línea,
        tabulaciones y espacios consecutivos reemplazados por un solo espacio.
        Conserva None; devuelve una cadena vacía si no hay contenido textual.

    Consideraciones:
        No elimina separadores como "|" ni convierte otros tipos a texto.
    """

     # Conserva la diferencia entre un valor ausente y una cadena vacía.
    if value is None:
        return None

    # split() sin argumentos separa por espacios en blanco y descarta los
    # segmentos vacíos; join() une las palabras con un único espacio.
    return " ".join(value.split())


