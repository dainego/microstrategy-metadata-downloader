"""Búsqueda común y aplanamiento específico por tipo de objeto."""
# Funciones para consultar metadata de MicroStrategy, reconstruir las rutas
# de carpetas y transformar los objetos en registros planos exportables.
# La autenticación y la escritura de archivos se gestionan en otros módulos.
from utils import clean_text

COMMON_FIELDS = ['objectId', 'name', 'subType', 'description', 'folder',
                 'model', 'submodel', 'submodel1', 'submodel2', 'submodel3']
TYPE_FIELDS = {
    12: ['formName', 'formCategory', 'displayFormat', 'expression',
         'tableObjectId', 'tableSubType', 'tableName'],
    4: ['expression', 'filterObjectId', 'filterSubType', 'filterName'],
    1: ['qualification', 'treeType', 'predicateObjectId', 'predicateSubType',
        'predicateName', 'function', 'elementDisplay', 'elementId'],
    13: ['expression', 'tableName'],
}


def read_response(client, **kwargs):
    """Lee y cierra la respuesta; la ausencia de respuesta aborta la búsqueda."""
    # Realiza la consulta utilizando la sesión autenticada del cliente.
    response = client.api_call(**kwargs)
    # Comprueba que exista una respuesta antes de intentar interpretar el JSON.
    if response is None:
        raise RuntimeError('No se obtuvo respuesta de MicroStrategy.')
    try:
        return response.json()
    # Cierra la respuesta HTTP incluso si falla la interpretación del JSON.
    finally:
        response.close()


def list_objects(client, object_type, root):
    """Busca por tipo y raíz; devuelve la lista y su árbol de carpetas."""
    # Inicia la búsqueda con el tipo, la visibilidad y la raíz indicados.
    search = read_response(client, method='POST', endpoint='/metadataSearches/results',
        params={'domain': 2, 'type': object_type, 'scope': 'all',
                'visibility': 'VISIBLE', 'root': root})
    # Reutiliza el identificador de búsqueda en las siguientes consultas.
    params = {'searchId': search['id'], 'limit': -1}
    # Recupera los resultados usando los parámetros de la implementación actual.
    # El timeout se expresa en segundos y se pasa al cliente HTTP.
    objects = read_response(client, method='GET', endpoint='/metadataSearches/results',
                            params=params, timeout=7200)
    # Recupera la representación jerárquica de la misma búsqueda.
    tree = read_response(client, method='GET', endpoint='/metadataSearches/results/tree',
                         params=params, timeout=7200)
    if not isinstance(objects, list) or not isinstance(tree, dict):
        raise ValueError('Estructura de resultados de búsqueda inesperada.')
    return objects, tree


def get_all_object_details(client, object_ids, settings):
    """Mantiene el orden de IDs y representa los detalles fallidos con None."""
    details = []
    for position, object_id in enumerate(object_ids, 1):
        # Consulta el endpoint correspondiente al tipo para cada ID seleccionado.
        response = client.api_call(method='GET',
            endpoint=settings['endpoint'].format(object_id=object_id),
            params=settings.get('params') or None, timeout=1800)
        # Permite omitir el objeto cuando la llamada HTTP no obtiene una respuesta
        # utilizable. None mantiene la correspondencia entre IDs y detalles.
        detail = None
        if response is not None:
            try:
                candidate = response.json()
                # Comprueba que la respuesta contenga información del objeto solicitado.
                if (isinstance(candidate, dict)
                        and isinstance(candidate.get('information'), dict)
                        and candidate['information'].get('objectId') == object_id):
                    detail = candidate
            except ValueError:
                pass
            finally:
                response.close()
        # Registra las consultas fallidas para que el servicio pueda contarlas.
        if detail is None:
            client.logger.warning('No se pudo obtener un detalle válido para %s.', object_id)
        details.append(detail)
        client.logger.info('Procesado %s de %s - %s', position, len(object_ids), object_id)
    return details


def parse_folder(folder, prefix='Schema Objects/Attributes'):
    """Retira el prefijo configurable del tipo y conserva cinco niveles."""
    fields = ['model', 'submodel', 'submodel1', 'submodel2', 'submodel3']
    # Divide la ruta y elimina componentes vacíos.
    parts = [p.strip() for p in (folder or '').replace('\\', '/').split('/') if p.strip()]
    roots = [p.strip() for p in prefix.split('/') if p.strip()]
    # Elimina el prefijo de carpeta del tipo seleccionado, si está presente.
    if roots and parts[:len(roots)] == roots:
        parts = parts[len(roots):]
    # Asigna los niveles en orden; los niveles ausentes conservan None.
    return {key: parts[i] if i < len(parts) else None for i, key in enumerate(fields)}


def expression_rows(detail, attribute=False):
    # Recorre los forms del atributo y las expresiones de cada form.
    # En facts las expresiones se encuentran directamente en el objeto.
    forms = (detail.get('forms') or [{}]) if attribute else [detail]
    for form in forms:
        # Conserva una fila con los datos disponibles aunque no haya expresiones.
        for expression in form.get('expressions') or [{}]:
            # Repite los datos para cada tabla asociada. Si no hay tablas, conserva
            # la expresión con campos de tabla vacíos.
            for table in expression.get('tables') or [{}]:
                row = {'expression': (expression.get('expression') or {}).get('text'),
                       'tableName': table.get('name')}
                if attribute:
                    row.update(formName=form.get('name'), formCategory=form.get('category'),
                               displayFormat=form.get('displayFormat'),
                               tableObjectId=table.get('objectId'), tableSubType=table.get('subType'))
                yield row


def metric_rows(detail):
    # La métrica combina su expresión y el filtro condicional en una misma fila.
    # Si no tiene filtro, los campos correspondientes quedan vacíos.
    condition = (detail.get('conditionality') or {}).get('filter') or {}
    yield {'expression': (detail.get('expression') or {}).get('text'),
           'filterObjectId': condition.get('objectId'),
           'filterSubType': condition.get('subType'), 'filterName': condition.get('name')}


def filter_rows(detail):
    """Una fila por elemento; recorre nodos anidados sin cruzar predicados."""
    qualification = detail.get('qualification') or {}

    # Recorre el árbol de calificación para encontrar predicados anidados.
    def walk(node):
        if isinstance(node, list):
            for child in node:
                yield from walk(child)
        elif isinstance(node, dict):
            predicate = node.get('predicateTree')
            if isinstance(predicate, dict):
                # El ID, subtipo y nombre pertenecen al objeto dentro de predicateTree.
                target = predicate.get('attribute') or predicate.get('metric') or {}
                # Genera una fila por elemento del predicado, sin cruzarlo con otros predicados.
                for element in predicate.get('elements') or [{}]:
                    yield {'qualification': qualification.get('text'), 'treeType': node.get('type'),
                           'predicateObjectId': target.get('objectId'),
                           'predicateSubType': target.get('subType'), 'predicateName': target.get('name'),
                           'function': predicate.get('function'),
                           'elementDisplay': element.get('display'), 'elementId': element.get('elementId')}
            for key, child in node.items():
                if key != 'elements' and isinstance(child, (dict, list)):
                    yield from walk(child)

    rows = list(walk(qualification.get('tree') or {}))
    yield from rows or [{'qualification': qualification.get('text'),
                         'treeType': (qualification.get('tree') or {}).get('type')}]


FLATTENERS = {12: lambda d: expression_rows(d, attribute=True),
              4: metric_rows, 1: filter_rows, 13: expression_rows}


def flatten_object_details(details, folder_map, object_type, folder_prefix):
    """Produce filas uniformes por tipo, con textos normalizados y campos comunes."""
    fields = COMMON_FIELDS + TYPE_FIELDS[object_type]
    rows = []
    for detail in details:
        # Omite las consultas fallidas representadas por None.
        if detail is None:
            continue
        info = detail['information']
        folder = folder_map.get(info.get('objectId'))
        common = {key: info.get(key) for key in COMMON_FIELDS[:4]}
        # Descompone la ruta en modelo y los cuatro niveles de submodelo
        # definidos en esta versión: submodel, submodel1, submodel2 y submodel3.
        common.update(folder=folder, **parse_folder(folder, folder_prefix))
        for specific in FLATTENERS[object_type](detail):
            values = {**common, **specific}
            # Normaliza saltos de línea, tabulaciones y espacios de la descripción
            # y del resto de los textos antes de exportarlos.
            rows.append({key: clean_text(values.get(key)) if isinstance(values.get(key), str)
                         else values.get(key) for key in fields})
    return rows


def build_folder_map(search_tree, object_ids):
    """
    Construye un diccionario de rutas para los objetos seleccionados.

    Parámetros:
        search_tree: Árbol de búsqueda con nodos que pueden contener id,
            name y children.
        object_ids: Identificadores de los objetos cuyas rutas se necesitan.

    Retorno:
        Diccionario {id_objeto: ruta_de_carpeta}, con niveles separados por
        "/". No incluye el nombre del objeto ni el nodo raíz del árbol.
        Los objetos que no se encuentran no se agregan al diccionario.
    """
    folder_map = {}

    # Usa un conjunto para comprobar la pertenencia de cada ID durante
    # el recorrido sin buscar secuencialmente en la lista original.
    object_ids = set(object_ids)

    def walk(node, current_path):
        """Recorre un nodo y sus descendientes acumulando la ruta de carpetas."""

        children = node.get("children", [])

        # Al encontrar un objeto seleccionado, current_path ya representa
        # la carpeta que lo contiene. No recorre descendientes de ese objeto.
        if node.get("id") in object_ids:
            folder_map[node["id"]] = "/".join(current_path)
            return

        if children:
            node_name = node.get("name")

            next_path = current_path.copy()

            if node_name:
                next_path.append(node_name)

            for child in children:
                walk(child, next_path)

    # Comienza en los hijos para excluir el nodo raíz del proyecto o del árbol.
    for child in search_tree.get("children", []):
        walk(child, [])

    return folder_map


