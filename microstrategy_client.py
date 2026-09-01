#External libraries
import requests



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