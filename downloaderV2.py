import requests
import json
import csv
import logging
from utils import setup_logger, write_json_to_file, write_to_csv
from datetime import datetime
import sys

#
project_id_big_data = "86B8BBB711E8A19F0A290080EF251385"
project_id_muc = "B32C690C11EAEDFDC5090080EF35D25D"
root_attributes_big_data = "6F55FB47F9974EABA18CB0C5FF46785C"
root_attributes_muc = "6F55FB47F9974EABA18CB0C5FF46785C"


base_url = "https://bi.movistar.com.ar/MicroStrategyLibrary/api"

account_id = "diotero"
account_psw = "Giwos.007"
object_type_attribute = 12
object_subtype_attribute = 3072
object_type_metric = 4
object_type_filter = 1
object_type_fact = 13


app_name="microstrategy-metadata-downloader"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"microstrategy_metadata_downloader_{timestamp}.txt"



# Function for API call
def api_call(method, url, cookies, headers=None, params=None, json_body=None, logger=None,timeout=3600, retries=5):
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            cookies=cookies,
            timeout=timeout
        )

        if not response.ok:

            logger.error(f"HTTP {response.status_code} "f"{response.reason}")
            logger.error(f"URL: {response.url}")
            logger.error(f"Response: {response.text}")

            return None

        return response

    except requests.exceptions.RequestException as e:

        logger.exception(
            f"API request failed: {e}"
        )

        return None

# Function to get the authentication token
def get_auth_token(base_url, logger, account_id, account_psw, project_id):

    url = f"{base_url}/auth/login"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
        }

    data = {
        "loginMode": 1,
        "username": account_id,
        "password": account_psw,
        "applicationId": project_id
    }

    response = api_call("POST", 
                        url, 
                        cookies=None, 
                        headers=headers, 
                        json_body=data, 
                        logger=logger)

    if response is None:
            logger.error(f"Could not login to MicroStrategy. Please check your credentials and try again.")
            raise RuntimeError("Could not login to MicroStrategy.")
            
    auth_token = response.headers['X-MSTR-AuthToken']
    cookies = dict(response.cookies)

    return auth_token, cookies

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

        folder = folder_map.get(object_id)

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
                            "formName": form_name,
                            "formCategory": form_category,
                            "displayFormat": display_format,
                            "expression": expression_text,
                            "tableName": table.get("name"),
                            "tableSubType": table.get("subType")
                        })

    return flat_attributes

#Function to disconnect
def logout(base_url, auth_token, cookies, logger):
    headers = {
        "X-MSTR-AuthToken": auth_token,
        "Accept": "application/json"
    }

    try:
        api_call(
            method="POST",
            url=f"{base_url}/auth/logout",
            headers=headers,
            cookies=cookies,
            logger=logger
        )

        logger.info("MicroStrategy session closed successfully.")

    except Exception as e:
        logger.error(
            f"Error closing MicroStrategy session: {e}"
        )


def main():

    #Start of the script
    logger = setup_logger(name=app_name, log_file=log_file, level=logging.DEBUG)
    logger.info("Start of the script")

    print("Select what to process:")
    print("1) Big Data")
    print("2) MUC")
    print("3) Exit")

    option = input("Enter option (1, 2, or 3): ")

    if option == "1":
        project_id = project_id_big_data
        root_attributes = root_attributes_big_data
        logger.info("Processing Big Data project")
    elif option == "2":
        project_id = project_id_muc
        root_attributes = root_attributes_muc
        logger.info("Processing MUC project")
    elif option == "3":
        logger.info("User chose to exit the script.")
        sys.exit()
    else:
        logger.error("Invalid option. Please select 1, 2, or 3.")
        raise ValueError("Invalid option selected.")

    #Authenticate
    logger.info("Authenticating")
    auth_token, cookies = get_auth_token(base_url, logger, account_id, account_psw, project_id)
    logger.info("Authentication successful")

    #Get Attirbute List
    logger.info("Retrieving attribute list")
    attribute_list, attribute_tree  = list_objects(base_url, auth_token, cookies, logger, project_id, object_type_attribute, root_attributes)
    write_json_to_file(attribute_list, "attribute_list.txt")

    # Exclude derived attributes
    attribute_ids = [
        obj["id"]
        for obj in attribute_list
        if obj.get("subtype") == object_subtype_attribute
        ]
    logger.info(f"Retrieved {len(attribute_list)} attributes")

    #Get Attribute Details
    logger.info("Retrieving attribute details")
    folder_map = build_folder_map(attribute_tree, attribute_ids)
    attributes_details = get_all_attribute_details(base_url, auth_token, cookies, logger,project_id, attribute_ids)
    write_json_to_file(attributes_details, "attributes_details.json")
    flat_attributes = flatten_attribute_details(attributes_details, folder_map)
    write_to_csv(flat_attributes, "flat_attributes.csv")
    logger.info(f"Retrieved details for {len(attribute_list)} attributes")

    logout(base_url, auth_token, cookies, logger)
    
    logger.info("End of the script")


main()