"""Punto de entrada por consola del descargador de metadata."""

from config import PROJECTS
from service import download_metadata


def main():
    """Solicita un proyecto y ejecuta la descarga de metadata."""

    print("\nMicroStrategy Metadata Downloader")
    print("---------------------------------")

    for project_key, project in PROJECTS.items():
        print(f"{project_key}) {project['name']}")

    print("0) Salir")

    project_key = input("\nSeleccione un proyecto: ").strip()

    if project_key == "0":
        print("Programa finalizado.")
        return

    if project_key not in PROJECTS:
        print("La opción seleccionada no es válida.")
        return

    project_name = PROJECTS[project_key]["name"]

    print(f"\nIniciando descarga del proyecto {project_name}...")

    try:
        result = download_metadata(project_key)

    except Exception:
        print("\nLa descarga falló. Revise el archivo de log.")
        return

    print("\nDescarga finalizada.")
    print(f"Estado: {result['status']}")
    print(f"Atributos descargados: {result['attributes_downloaded']}")
    print(f"Atributos fallidos: {result['attributes_failed']}")
    print(f"Filas exportadas: {result['rows_exported']}")
    print(f"Duración: {result['duration_seconds']} segundos")
    print(f"Archivo JSON: {result['files']['json']}")

    if result["files"]["txt"]:
        print(f"Archivo TXT: {result['files']['txt']}")

    if result["warnings"]:
        print("\nAdvertencias:")

        for warning in result["warnings"]:
            print(f"- {warning}")


if __name__ == "__main__":
    main()