#Python libraries
from datetime import datetime
import sys
import logging

#Internal Libraries
from utils import setup_logger
from exporters import write_to_json, write_to_text
from metadata import (
    get_all_attribute_details, 
    flatten_attribute_details, 
    build_folder_map, 
    list_objects)
from microstrategy_client import get_auth_token, logout


#Env Variables
from config import (
    BASE_URL,
    ACCOUNT_ID,
    ACCOUNT_PASSWORD,
    APP_NAME,
    LOG_FOLDER,
    RESULTS_FOLDER,
    OBJECT_TYPE_ATTRIBUTE,
    OBJECT_SUBTYPE_ATTRIBUTE,
    PROJECTS
)

#Variables de Proyectos    
project_id_big_data = PROJECTS["1"]["project_id"]
project_id_muc = PROJECTS["2"]["project_id"]
root_attributes_big_data = PROJECTS["1"]["attribute_root"]
root_attributes_muc = PROJECTS["2"]["attribute_root"]

#Variables de objetos
object_type_attribute = OBJECT_TYPE_ATTRIBUTE
object_subtype_attribute = OBJECT_SUBTYPE_ATTRIBUTE
object_type_metric = 4
object_type_filter = 1
object_type_fact = 13

#Variables de API
base_url = BASE_URL
account_id = ACCOUNT_ID
account_psw = ACCOUNT_PASSWORD

# Define log filename
app_name=APP_NAME
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"{APP_NAME}_{timestamp}.txt"

# Define project and output folders
log_folder = LOG_FOLDER
results_folder = RESULTS_FOLDER

# Create folders before using them
log_folder.mkdir(parents=True, exist_ok=True)
results_folder.mkdir(parents=True, exist_ok=True)

#Define Log Level
log_level = logging.DEBUG




def main():

    #Start of the script
    logger = setup_logger(name=app_name, log_file=log_folder / log_file, level=log_level)
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
    flat_attributes = flatten_attribute_details(attributes_details, folder_map)
    write_to_text(flat_attributes, results_folder / f"flat_attributes_{timestamp}.txt", "|")
    write_to_json(flat_attributes, results_folder / f"flat_attributes_{timestamp}.json")
    logger.info(f"Retrieved details for {len(attribute_list)} attributes")

    logout(base_url, auth_token, cookies, logger)
    
    logger.info("End of the script")

if __name__ == "__main__":
    main()
