# Funciones para consultar metadata de MicroStrategy, reconstruir las rutas
# de carpetas y transformar los atributos en registros planos exportables.
# La autenticación y la escritura de archivos se gestionan en otros módulos.

# Utilidades internas para las llamadas HTTP y la limpieza de descripciones.
from microstrategy_client import api_call
from utils import clean_text


def list_objects(base_url, auth_token, cookies, logger,project_id, object_type, root):
    """
    Crea una búsqueda de objetos por tipo y recupera sus resultados como lista y como árbol.

    Parámetros:
        base_url: URL base de la API de MicroStrategy.
        auth_token: Token de una sesión autenticada.
        cookies: Cookies de la sesión.
        logger: Logger utilizado para registrar las llamadas y sus errores.
        project_id: Identificador del proyecto que se consultará.
        object_type: Tipo de objeto que se desea buscar.
        root: Identificador de la carpeta raíz de la búsqueda.

    Retorno:
        Tupla (objects, tree) con las respuestas JSON deserializadas:
        la lista de objetos y el árbol utilizado para reconstruir sus rutas.

    Consideraciones:
        Actualmente no comprueba si api_call() devuelve None antes de acceder
        a response.json(). Los errores de respuesta o estructura se propagan.
    """
    
    headers = {
        "X-MSTR-AuthToken": auth_token,
        "X-MSTR-ProjectID": project_id,
        "Accept": "application/json"
    }

    # Inicia la búsqueda con el tipo, la visibilidad y la raíz indicados.
    response = api_call(
        method="POST",
        url=f"{base_url}/metadataSearches/results",
        headers=headers,
        cookies=cookies,
        logger=logger,
        params={
            "domain": 2,
            "type": object_type,
            "scope": "all",
            "visibility": "VISIBLE",
            "root": root
        }
    )

    # Reutiliza el identificador de búsqueda en las siguientes consultas.
    search_id = response.json()["id"]

    # Recupera los resultados usando los parámetros de la implementación actual.
    # El timeout se expresa en segundos y se pasa a api_call().
    response = api_call(
        method="GET",
        url=f"{base_url}/metadataSearches/results",
        headers=headers,
        cookies=cookies,
        logger=logger,
        timeout=7200,
        params={
            "searchId": search_id,
            "limit": -1
        }
    )

    objects = response.json()

    # Recupera la representación jerárquica de la misma búsqueda.
    response = api_call(
        method="GET",
        url=f"{base_url}/metadataSearches/results/tree",
        headers=headers,
        cookies=cookies,
        logger=logger,
        timeout=7200,
        params={
            "searchId": search_id,
            "limit": -1
        }
    )

    tree = response.json()

    return objects, tree


def get_attribute_details(base_url, auth_token, cookies, logger, project_id, attribute_id):
    """
    Consulta el detalle de un atributo mediante su identificador.

    Parámetros:
        base_url: URL base de la API.
        auth_token: Token de autenticación.
        cookies: Cookies de la sesión.
        logger: Logger para registrar errores y advertencias.
        project_id: Identificador del proyecto.
        attribute_id: Identificador del atributo que se consultará.

    Retorno:
        Detalle deserializado de la respuesta JSON, o None si api_call()
        devuelve None. Los errores al interpretar el JSON no se capturan aquí.
    """

    headers = {
        "X-MSTR-AuthToken": auth_token,
        "X-MSTR-ProjectID": project_id,
        "Accept": "application/json"
    }

    url = f"{base_url}/model/attributes/{attribute_id}"

    response = api_call(
        method="GET",
        url=url,
        headers=headers,
        cookies=cookies,
        logger=logger,
        timeout=1800
    )

    # Permite omitir el atributo cuando la llamada HTTP no obtiene respuesta
    # utilizable. Se conserva el mensaje original del registro de ejecución.
    if response is None:
        logger.warning(
            f"Skipping attribute {attribute_id}"
    )

        return None

    return response.json()


def get_all_attribute_details(base_url, auth_token, cookies, logger, project_id, attribute_ids):
    """
    Recupera secuencialmente los detalles de los atributos seleccionados.

    Parámetros:
        base_url: URL base de la API.
        auth_token: Token de autenticación.
        cookies: Cookies de la sesión.
        logger: Logger para registrar el progreso y los errores.
        project_id: Identificador del proyecto.
        attribute_ids: Secuencia de identificadores de atributos.

    Retorno:
        Lista en el mismo orden que attribute_ids. Incluye None cuando una
        consulta devuelve ese valor; el aplanamiento lo omite posteriormente.

    Consideraciones:
        El progreso cuenta consultas procesadas, no necesariamente exitosas.
        Una excepción no capturada interrumpe el recorrido.
    """

    attributes = []

    for i, attribute_id in enumerate(attribute_ids, start=1):

        attribute = get_attribute_details(
            base_url,
            auth_token,
            cookies,
            logger,
            project_id,
            attribute_id
        )

        logger.info(f"Processed {i} of {len(attribute_ids)} - {attribute_id}")
        attributes.append(attribute)

    return attributes


def flatten_attribute_details(attribute_list, folder_map):
    """
    Transforma los detalles anidados de atributos en una lista de diccionarios.

    Parámetros:
        attribute_list: Lista de detalles de atributos; puede incluir None.
        folder_map: Diccionario que relaciona el ID de cada objeto con su ruta.

    Retorno:
        Registros planos con datos del atributo, carpeta, modelo, submodelos,
        forma, expresión y tabla. Genera una fila por combinación recorrida
        de atributo, forma, expresión y tabla. Si la expresión no tiene tablas,
        genera una fila con los campos de tabla en None.

    Consideraciones:
        Omite los detalles None, los atributos sin formas y las formas sin
        expresiones. Solo normaliza el texto de la descripción.
    """
    flat_attributes = []

    for attribute in attribute_list:

        # Omite las consultas fallidas representadas por None.
        if attribute is None:
            continue

        information = attribute.get("information", {})

        object_id = information.get("objectId")
        subtype = information.get("subType")
        attribute_name = information.get("name")
        description = information.get("description")

        # Normaliza saltos de línea, tabulaciones y espacios de la descripción.
        if description:
             description = clean_text(description)

        # Descompone la ruta en modelo y los cuatro niveles de submodelo
        # definidos en esta versión: submodel, submodel1, submodel2 y submodel3.
        folder = folder_map.get(object_id)
        folder_fields = parse_folder(folder)
        model = folder_fields.get("model")
        submodel = folder_fields.get("submodel")
        submodel1 = folder_fields.get("submodel1")
        submodel2 = folder_fields.get("submodel2")
        submodel3 = folder_fields.get("submodel3")

        # Recorre los forms del atributo y las expresiones de cada form.
        for form in attribute.get("forms", []):

            form_name = form.get("name")
            form_category = form.get("category")
            display_format = form.get("displayFormat")

            for expression_item in form.get("expressions", []):

                expression_text = (
                    expression_item
                    .get("expression", {})
                    .get("text")
                )

                tables = expression_item.get("tables", [])

                # Conserva la expresión como línea vacía aunque no tenga tablas asociadas.
                if not tables:
                    flat_attributes.append({
                        "objectId": object_id,
                        "subType": subtype,
                        "name": attribute_name,
                        "description": description,
                        "folder": folder,
                        "model": model,
                        "submodel": submodel,
                        "submodel1": submodel1,
                        "submodel2": submodel2,
                        "submodel3": submodel3,
                        "formName": form_name,
                        "formCategory": form_category,
                        "displayFormat": display_format,
                        "expression": expression_text,
                        "tableName": None,
                        "tableSubType": None
                    })

                else:
                    # Repite los datos del atributo para cada tabla asociada.   
                    for table in tables:
                        flat_attributes.append({
                            "objectId": object_id,
                            "subType": subtype,
                            "name": attribute_name,
                            "description": description,
                            "folder": folder,
                            "model": model,
                            "submodel": submodel,
                            "submodel1": submodel1,
                            "submodel2": submodel2,
                            "submodel3": submodel3,                           
                            "formName": form_name,
                            "formCategory": form_category,
                            "displayFormat": display_format,
                            "expression": expression_text,
                            "tableName": table.get("name"),
                            "tableSubType": table.get("subType")
                        })

    return flat_attributes


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


def parse_folder(folder):
    """
    Descompone una ruta de carpeta en modelo y niveles de submodelo.

    Parámetros:
        folder: Ruta como cadena, o None si no se conoce la carpeta.

    Retorno:
        Diccionario con model, submodel, submodel1, submodel2 y submodel3.
        Los niveles que no están presentes conservan el valor None.

    Consideraciones:
        Normaliza los separadores de ruta y elimina componentes vacíos.
        Quita el prefijo Schema Objects/Attributes solo si coincide exactamente
        con los dos primeros componentes, respetando mayúsculas y minúsculas.
        Si no coincide, interpreta la ruta completa como niveles del modelo.
        Los niveles que exceden los cinco campos disponibles se ignoran.
    """

    root_parts = ["Schema Objects", "Attributes"]

    result = {
        "model": None,
        "submodel": None,
        "submodel1": None,
        "submodel2": None,
        "submodel3": None
    }

    if not folder:
        return result

    # Divide la ruta y elimina componentes vacíos
    parts = [
        part.strip()
        for part in folder.replace("\\", "/").split("/")
        if part.strip()
    ]

    # Elimina la raíz Schema Objects/Attributes, si está presente
    if parts[:2] == root_parts:
        parts = parts[2:]

    field_names = [
        "model",
        "submodel",
        "submodel1",
        "submodel2",
        "submodel3"
    ]

    # Asigna los niveles en orden; zip() termina al agotar la lista más corta.
    for field_name, value in zip(field_names, parts):
        result[field_name] = value

    return result