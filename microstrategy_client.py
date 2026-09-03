# Cliente con estado de sesión y funciones anteriores de compatibilidad.
# La migración de main.py y metadata.py puede hacerse en una segunda etapa.
import logging
from urllib.parse import urlsplit
import requests


class MicroStrategyClient:
    """Gestiona una sesión de MicroStrategy para un único proyecto.

    Conserva URL, proyecto y logger; Session administra cookies, encabezados
    y conexiones HTTP reutilizables. No comparte la instancia entre hilos.
    No reintenta solicitudes automáticamente, especialmente operaciones POST.

    Las consultas devuelven Response o None ante errores HTTP/de conexión.
    Un login fallido produce RuntimeError. close() libera recursos locales;
    logout() solicita el cierre de la sesión remota y devuelve un booleano.
    """

    def __init__(self, base_url, project_id, logger=None, timeout=3600):
        """Configura el cliente sin iniciar sesión ni realizar llamadas HTTP.
        timeout: Segundos de espera para requests; también admite la tupla
            (conexión, lectura). No representa un plazo total de ejecución.
        """
        # Inicializa el logger antes de validar para registrar errores de configuración.
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        if not isinstance(base_url, str) or not base_url.strip():
            self.logger.error("__init__: base_url debe ser una URL no vacía.")
            raise ValueError("base_url debe ser una URL no vacía.")
        try:
            parsed = urlsplit(base_url.strip())
        except ValueError:
            self.logger.error("__init__: no se pudo interpretar la URL base.")
            raise ValueError("no se pudo interpretar la URL base.")
        if (parsed.scheme not in ("https", "http") or not parsed.netloc
                or parsed.username or parsed.password or parsed.query
                or parsed.fragment):
            self.logger.error("__init__: se requiere una URL HTTP(S) sin credenciales ni parámetros.")
            raise ValueError("base_url debe ser una URL HTTP(S) sin credenciales ni parámetros.")
        if not isinstance(project_id, str) or not project_id.strip():
            self.logger.error("__init__: project_id debe ser un identificador no vacío.")
            raise ValueError("project_id debe ser un identificador no vacío.")

        self.base_url = base_url.strip().rstrip("/")
        self.project_id = project_id
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-MSTR-ProjectID": project_id
        })
        self._closed = False

    @property
    def auth_token(self):
        """Obtiene el token almacenado en la sesión, o None antes del login."""
        return self.session.headers.get("X-MSTR-AuthToken")

    def _ensure_open(self):
        if self._closed:
            self.logger.error("_ensure_open: el cliente está cerrado; creá una nueva instancia.")
            raise RuntimeError("El cliente está cerrado; creá una nueva instancia.")

    def _request(self, method, endpoint, params=None, json_body=None, timeout=None):
        """Envía una solicitud a una ruta de la API configurada.
        No registra cuerpos, cookies, credenciales ni tokens. No sigue
        redirecciones automáticamente para evitar reenviar encabezados sensibles.
        """
        self._ensure_open()
        if not isinstance(endpoint, str) or not endpoint:
            self.logger.error("_request: endpoint debe ser una ruta no vacía.")
            raise ValueError("endpoint debe ser una ruta no vacía.")
        try:
            parsed = urlsplit(endpoint)
        except ValueError:
            self.logger.error("_request: no se pudo interpretar la ruta de la API.")
            raise
        if (parsed.scheme or parsed.netloc or endpoint.startswith("//")
                or "\\" in endpoint or ".." in parsed.path.split("/")
                or parsed.query or parsed.fragment):
            self.logger.error("_request: usá una ruta relativa de la API y parámetros en params.")
            raise ValueError("Usá una ruta relativa de la API y pasá los parámetros en params.")

        try:
            response = self.session.request(
                method=method,
                url=f"{self.base_url}/{endpoint.lstrip('/')}",
                params=params,
                json=json_body,
                timeout=self.timeout if timeout is None else timeout,
                allow_redirects=False
            )
        except requests.exceptions.RequestException as exc:
            self.logger.error("_request: error de comunicación con MicroStrategy (%s).", type(exc).__name__)
            return None
        except Exception as exc:
            # Conserva la propagación de errores inesperados. Se registra solo
            # el tipo: el texto de la excepción podría contener datos sensibles.
            self.logger.error("_request: error inesperado al enviar la solicitud (%s).", type(exc).__name__)
            raise

        if not 200 <= response.status_code < 300:
            self.logger.error("MicroStrategy devolvió HTTP %s.", response.status_code)
            response.close()
            return None
        return response

    def login(self, username, password, login_mode=1):
        """Autentica y guarda el token; Session conserva las cookies recibidas.

        Mantiene applicationId=project_id del flujo anterior. No guarda la
        contraseña como atributo de la instancia ni la registra en los logs.
        """
        self._ensure_open()
        if self.auth_token:
            self.logger.error("login: ya hay una sesión activa; ejecutá logout() primero.")
            raise RuntimeError("Ya hay una sesión activa; ejecutá logout() primero.")
        if not username or not password:
            self.logger.error("login: se requieren usuario y contraseña.")
            raise ValueError("Se requieren usuario y contraseña.")

        response = self._request("POST", "/auth/login", json_body={
            "loginMode": login_mode,
            "username": username,
            "password": password,
            "applicationId": self.project_id
        })
        if response is None:
            self.session.cookies.clear()
            self.logger.error("login: no se pudo iniciar sesión en MicroStrategy.")
            raise RuntimeError("No se pudo iniciar sesión en MicroStrategy.")
        try:
            token = response.headers.get("X-MSTR-AuthToken")
        finally:
            response.close()
        if not token:
            self.session.cookies.clear()
            self.logger.error("login: la respuesta no contiene X-MSTR-AuthToken.")
            raise RuntimeError("La respuesta de login no contiene X-MSTR-AuthToken.")

        self.session.headers["X-MSTR-AuthToken"] = token
        self.logger.info("Autenticación en MicroStrategy completada.")

    def api_call(self, method, endpoint, params=None, json_body=None, timeout=None):
        """Consulta la API usando automáticamente token, proyecto y cookies.

        endpoint: Ruta como /model/attributes/{id}, no la URL completa.
        Retorna Response o None; comprobar None antes de llamar a json().
        Las excepciones de decodificación JSON corresponden al consumidor.
        """
        self._ensure_open()
        if not self.auth_token:
            self.logger.error("api_call: no hay sesión autenticada; ejecutá login() primero.")
            raise RuntimeError("Primero debés ejecutar login().")
        return self._request(method, endpoint, params, json_body, timeout)

    def logout(self):
        """Cierra la sesión remota; devuelve True si se cerró o no había token.

        Si la solicitud falla devuelve False y conserva el token para permitir
        otro intento. Solo registra éxito después de una respuesta HTTP 2xx.
        """
        if not self.auth_token:
            return True
        response = self._request("POST", "/auth/logout")
        if response is None:
            self.logger.warning("No se pudo confirmar el cierre de la sesión remota.")
            return False
        response.close()
        self.session.headers.pop("X-MSTR-AuthToken", None)
        self.session.cookies.clear()
        self.logger.info("Sesión de MicroStrategy cerrada.")
        return True

    def close(self):
        """Libera conexiones locales. No sustituye a logout() en el servidor."""
        if not self._closed:
            try:
                self.session.close()
                self.session.headers.pop("X-MSTR-AuthToken", None)
                self.session.cookies.clear()
                self._closed = True
            except Exception as exc:
                self.logger.error("close: error al liberar los recursos locales (%s).", type(exc).__name__)
                raise

    def __enter__(self):
        """Permite usar la instancia con with; el login sigue siendo explícito."""
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Intenta logout y siempre libera los recursos locales al salir."""
        if exc_type is not None:
            # Registra la salida anormal sin exponer el mensaje de la excepción.
            # La excepción original continúa propagándose al devolver False.
            self.logger.error("__exit__: el bloque with terminó con una excepción (%s).", exc_type.__name__)
        try:
            self.logout()
        finally:
            self.close()
        return False

# Compatibilidad temporal: las funciones siguientes mantienen los imports
# actuales de main.py y metadata.py. Todavía no utilizan la nueva clase.
# Se conservan sin cambios funcionales y se retirarán al migrar los consumidores.

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