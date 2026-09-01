#Internal libraries
from microstrategy_client import api_call
from utils import clean_text

# Function to list objects
def list_objects(base_url, auth_token, cookies, logger,project_id, object_type, root):
    
    headers = {
        "X-MSTR-AuthToken": auth_token,
        "X-MSTR-ProjectID": project_id,
        "Accept": "application/json"
    }

    # Create metadata search
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

    search_id = response.json()["id"]

    # Retrieve metadata search results
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

     # Retrieve the same results as a tree
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

# Function to get attribute details
def get_attribute_details(base_url, auth_token, cookies, logger, project_id, attribute_id):

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

    if response is None:
        logger.warning(
            f"Skipping attribute {attribute_id}"
    )

        return None

    return response.json()

#Function to get all attribute details
def get_all_attribute_details(base_url, auth_token, cookies, logger, project_id, attribute_ids):

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

#Function to flatten attribute details
def flatten_attribute_details(attribute_list, folder_map):
    flat_attributes = []

    for attribute in attribute_list:

        # Skip attributes whose API call failed
        if attribute is None:
            continue

        information = attribute.get("information", {})

        object_id = information.get("objectId")
        subtype = information.get("subType")
        attribute_name = information.get("name")
        description = information.get("description")

        #If description is not None, replace newlines with spaces
        if description:
             description = clean_text(description)

        folder = folder_map.get(object_id)

        folder_fields = parse_folder(folder)
        model = folder_fields.get("model")
        submodel = folder_fields.get("submodel")
        submodel1 = folder_fields.get("submodel1")
        submodel2 = folder_fields.get("submodel2")
        submodel3 = folder_fields.get("submodel3")

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
    folder_map = {}

    object_ids = set(object_ids)

    def walk(node, current_path):

        children = node.get("children", [])

        # If the node is one of our objects, current_path
        # represents the folder containing it
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

    # Do not include the project/tree root itself in the folder path
    for child in search_tree.get("children", []):
        walk(child, [])

    return folder_map


def parse_folder(folder):
    """
    Parses a folder path and extracts model and submodel information.
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

    for field_name, value in zip(field_names, parts):
        result[field_name] = value

    return result