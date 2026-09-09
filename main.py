"""Interfaz de consola para una descarga por proyecto y tipo de objeto."""
import argparse
import config
from service import download_metadata


def main():
    # Define los parámetros de consola para seleccionar proyecto y tipo de objeto.
    parser = argparse.ArgumentParser(description='MicroStrategy Metadata Downloader')
    parser.add_argument('--project-key', choices=config.PROJECTS)
    parser.add_argument('--object-type', type=int, choices=config.OBJECT_TYPES, default=12)
    args = parser.parse_args()
    project_key = args.project_key
    # Si no se indicó proyecto como parámetro, muestra el menú de proyectos.
    if project_key is None:
        for key, project in config.PROJECTS.items():
            print(f"{key}) {project['name']}")
        project_key = input('Proyecto (0 para salir): ').strip()
        if project_key == '0':
            return
    # Valida el tipo de objeto y la configuración necesaria para iniciar la descarga.
    settings = config.get_object_settings(args.object_type)
    if project_key not in config.PROJECTS:
        parser.error('Proyecto inválido.')
    if not config.PROJECTS[project_key].get(settings['root_key']):
        parser.error(f"Falta configurar {settings['root_key']} para el proyecto {project_key}.")
    # Invoca el mismo servicio que utiliza la API, sin duplicar la lógica de descarga.
    try:
        result = download_metadata(project_key, args.object_type)
    except Exception:
        print('La descarga falló. Revisá el archivo de log.')
        raise SystemExit(1)
    # Muestra el resumen de ejecución, los archivos generados y las advertencias.
    print(f"Estado: {result['status']}")
    print(f"Objetos descargados: {result['objects_downloaded']}")
    print(f"Objetos fallidos: {result['objects_failed']}")
    print(f"Filas exportadas: {result['rows_exported']}")
    print(f"Duración: {result['duration_seconds']} segundos")
    for format, path in result['files'].items():
        print(f'{format.upper()}: {path}')
    for warning in result['warnings']:
        print(f'Advertencia: {warning}')


if __name__ == '__main__':
    main()
