"""Interfaz de consola para una descarga por proyecto y tipo de objeto."""
import argparse
import config
from service import download_metadata


def main():

    # Define los parámetros de consola para seleccionar proyecto y tipo de objeto.
    parser = argparse.ArgumentParser(description=config.APP_NAME) #Crea objeto parser para manejar argumentos de línea de comandos, con descripción del nombre de la aplicación
    parser.add_argument('--project-key', choices=config.PROJECTS) #Define que el parámetro --project-key solo acepta valores del diccionario config.PROJECTS
    parser.add_argument('--object-type', type=int, choices=config.OBJECT_TYPES, default=12) #Define que el parámetro --object-type solo acepta valores del diccionario config.OBJECT_TYPES, con tipo de dato int y valor por defecto 12 (atributos)
    args = parser.parse_args() #Parsea los argumentos de línea de comandos y los guarda en el objeto args
    project_key = args.project_key #Guarda el valor de --project-key

    # Si no se indicó proyecto como parámetro, muestra el menú de proyectos.
    if project_key is None:
        for key, project in config.PROJECTS.items():
            print(f"{key}) {project['name']}")
        project_key = input('Proyecto (0 para salir): ').strip()
        if project_key == '0':
            return
        
    # Valida el tipo de objeto y la configuración necesaria para iniciar la descarga.
    settings = config.get_object_settings(args.object_type) #Trae la configuración de object_type usando la función get_object_settings de config.py
    if project_key not in config.PROJECTS: #Valida si el valor de project_key está en el diccionario config.PROJECTS
        parser.error('Proyecto inválido.')
    if not config.PROJECTS[project_key].get(settings['root_key']): #Valida si el valor de settings['root_key'] está en el diccionario config.PROJECTS[project_key]
        parser.error(f"Falta configurar {settings['root_key']} para el proyecto {project_key}.")

    # Invoca el mismo servicio que utiliza la API, sin duplicar la lógica de descarga.
    try:
        result = download_metadata(project_key, args.object_type) #Invoca la funcion download_metadata de service.py

    # Si ocurrió un error, muestra el mensaje y sale con código de error.
    except Exception:
        print('La descarga falló. Revisá el archivo de log.')
        raise SystemExit(1)

    # Si no hay exepción, muestra el resumen de ejecución, los archivos generados y las advertencias.
    print(f"Estado: {result['status']}")
    print(f"Objetos descargados: {result['objects_downloaded']}")
    print(f"Objetos fallidos: {result['objects_failed']}")
    print(f"Filas exportadas: {result['rows_exported']}")
    print(f"Duración: {result['duration_seconds']} segundos")
    print("Archivos generados:")
    for format, path in result['files'].items():
        print(f'{format.upper()}: {path}')
    for warning in result['warnings']:
        print(f'Advertencia: {warning}')


if __name__ == '__main__':
    main()
