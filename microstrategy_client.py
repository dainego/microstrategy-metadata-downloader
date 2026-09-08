# Clase que implementa las llamadas a las APIs de MicroStrategy y gestiona la sesión. 
# No depende de otros módulos del proyecto.

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

        # Valida la URL base y el project_id; no permite credenciales ni parámetros.
        try:
            parsed = urlsplit(base_url.strip())
        except ValueError:
            self.logger.error("__init__: no se pudo interpretar la URL base.")
            raise ValueError("no se pudo interpretar la URL base.")

        # Valida que la URL sea HTTP(S) y no contenga credenciales ni parámetros.
        if (parsed.scheme not in ("https", "http") or not parsed.netloc
                or parsed.username or parsed.password or parsed.query
                or parsed.fragment):
            self.logger.error("__init__: se requiere una URL HTTP(S) sin credenciales ni parámetros.")
            raise ValueError("base_url debe ser una URL HTTP(S) sin credenciales ni parámetros.")

        # Valida que project_id sea un identificador no vacío.
        if not isinstance(project_id, str) or not project_id.strip():
            self.logger.error("__init__: project_id debe ser un identificador no vacío.")
            raise ValueError("project_id debe ser un identificador no vacío.")

        #Define los atributos de la instancia y crea la sesión HTTP.
        self.base_url = base_url.strip().rstrip("/")
        self.project_id = project_id
        self.timeout = timeout
        self.session = requests.Session() # Crea objeto de la clase Session de requests para gestionar cookies y encabezados.
        self.session.headers.update({
            "Accept": "application/json",
            "X-MSTR-ProjectID": project_id
        })
        self._closed = False # Atributo que indica si la instancia está cerrada. Inicialmente es False.

    @property #decorador de Python que permite acceder a un método como si fuera un atributo de la instancia.
    def auth_token(self): #Propiedad que devuelve el token de autenticación almacenado en la sesión, o None si no hay sesión activa.
        """Obtiene el token almacenado en la sesión, o None antes del login."""
        return self.session.headers.get("X-MSTR-AuthToken")

    #Propiedad que verifica que la instancia no esté cerrada; lanza RuntimeError si lo está.
    def _ensure_open(self): 
        if self._closed:
            self.logger.error("_ensure_open: el cliente está cerrado; creá una nueva instancia.")
            raise RuntimeError("El cliente está cerrado; creá una nueva instancia.")

    #Propiedad que envía una solicitud HTTP a la API de MicroStrategy, manejando errores y devolviendo la respuesta o None.
    def _request(self, method, endpoint, params=None, json_body=None, timeout=None): #
        """Envía una solicitud a una ruta de la API configurada.
        No registra cuerpos, cookies, credenciales ni tokens. No sigue
        redirecciones automáticamente para evitar reenviar encabezados sensibles.
        """

        #Valida que la instancia no esté cerrada y que el endpoint sea una ruta relativa válida.
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
            #Envía la solicitud HTTP usando la sesión, con el método, endpoint, parámetros y cuerpo JSON proporcionados. No sigue redirecciones automáticamente.
            response = self.session.request(
                method=method,
                url=f"{self.base_url}/{endpoint.lstrip('/')}",
                params=params,
                json=json_body,
                timeout=self.timeout if timeout is None else timeout,
                allow_redirects=False
            )
        #Captura errores de conexión
        except requests.exceptions.RequestException as exc:
            self.logger.error("_request: error de comunicación con MicroStrategy (%s).", type(exc).__name__)
            return None
        #Captura otro tipo de errores inesperados
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

    #Propiedad que autentica al usuario y guarda el token de sesión; lanza RuntimeError si falla.
    def login(self, username, password, login_mode=1):
        """Autentica y guarda el token; Session conserva las cookies recibidas.

        Mantiene applicationId=project_id del flujo anterior. No guarda la
        contraseña como atributo de la instancia ni la registra en los logs.
        """

        #Verifica que la instancia no esté cerrada y que no haya sesión activa; lanza RuntimeError si ya hay sesión. Valida que username y password sean proporcionados; lanza ValueError si faltan.
        self._ensure_open()
        if self.auth_token:
            self.logger.error("login: ya hay una sesión activa; ejecutá logout() primero.")
            raise RuntimeError("Ya hay una sesión activa; ejecutá logout() primero.")

        #Verifica que se proporcionen tanto el nombre de usuario como la contraseña; lanza ValueError si alguno falta.
        if not username or not password:
            self.logger.error("login: se requieren usuario y contraseña.")
            raise ValueError("Se requieren usuario y contraseña.")

        #Envía la solicitud de login a la API de MicroStrategy con el nombre de usuario, contraseña, modo de login y project_id. Si no hay respuesta, limpia las cookies y lanza RuntimeError. Intenta obtener el token de autenticación de los encabezados de la respuesta; si no está presente, limpia las cookies y lanza RuntimeError. Si todo es exitoso, guarda el token en los encabezados de la sesión y registra que la autenticación se completó.
        response = self._request("POST", "/auth/login", json_body={
            "loginMode": login_mode,
            "username": username,
            "password": password,
            "applicationId": self.project_id
        })

        # Si no hay respuesta, limpia las cookies y lanza RuntimeError.
        if response is None:
            self.session.cookies.clear()
            self.logger.error("login: no se pudo iniciar sesión en MicroStrategy.")
            raise RuntimeError("No se pudo iniciar sesión en MicroStrategy.")

        # Intenta obtener el token de autenticación de los encabezados de la respuesta; si no está presente, 
        # limpia las cookies y lanza RuntimeError. Si todo es exitoso, guarda el token en los encabezados de la sesión y registra que la autenticación se completó.
        try:
            token = response.headers.get("X-MSTR-AuthToken")
        finally:
            response.close()
        if not token:
            self.session.cookies.clear()
            self.logger.error("login: la respuesta no contiene X-MSTR-AuthToken.")
            raise RuntimeError("La respuesta de login no contiene X-MSTR-AuthToken.")

        # Guarda el token en los encabezados de la sesión y registra que la autenticación se completó.
        self.session.headers["X-MSTR-AuthToken"] = token
        self.logger.info("Autenticación en MicroStrategy completada.")

    #Propiedad que realiza una llamada a la API usando el token de sesión, proyecto y cookies; devuelve la respuesta o None si falla. Lanza RuntimeError si no hay sesión activa.
    def api_call(self, method, endpoint, params=None, json_body=None, timeout=None):
        """Consulta la API usando automáticamente token, proyecto y cookies.

        endpoint: Ruta como /model/attributes/{id}, no la URL completa.
        Retorna Response o None; comprobar None antes de llamar a json().
        Las excepciones de decodificación JSON corresponden al consumidor.
        """
        #Verifica que la instancia no esté cerrada y que haya sesión activa; lanza RuntimeError si no hay sesión. Luego, realiza la solicitud a la API con los parámetros proporcionados. Devuelve la respuesta o None si falla.
        self._ensure_open()
        if not self.auth_token:
            self.logger.error("api_call: no hay sesión autenticada; ejecutá login() primero.")
            raise RuntimeError("Primero debés ejecutar login().")

        #Realiza la solicitud a la API con los parámetros proporcionados. Devuelve la respuesta o None si falla.
        return self._request(method, endpoint, params, json_body, timeout)

    # Propiedad que cierra la sesión remota y limpia los recursos locales; devuelve True si se cerró o no había token, False si falla. Lanza RuntimeError si la instancia está cerrada. 
    def logout(self):
        """Cierra la sesión remota; devuelve True si se cerró o no había token.

        Si la solicitud falla devuelve False y conserva el token para permitir
        otro intento. Solo registra éxito después de una respuesta HTTP 2xx.
        """
        # Si no hay token de autenticación, devuelve True. 
        # Luego, realiza la solicitud de logout a la API. 
        if not self.auth_token:
            return True
        response = self._request("POST", "/auth/logout")

        # Si no hay respuesta, registra una advertencia y devuelve False. 
        if response is None:
            self.logger.warning("No se pudo confirmar el cierre de la sesión remota.")
            return False

        #Si la respuesta es exitosa, limpia el token y las cookies de la sesión y registra que la sesión se cerró. 
        #Devuelve True si todo fue exitoso.
        response.close()
        self.session.headers.pop("X-MSTR-AuthToken", None)
        self.session.cookies.clear()
        self.logger.info("Sesión de MicroStrategy cerrada.")
        return True

    #Propiedad que libera recursos locales, cierra la sesión y limpia cookies; lanza RuntimeError si la instancia ya está cerrada.
    def close(self):
        """Libera conexiones locales. No sustituye a logout() en el servidor."""

        #Verifica que la instancia no esté cerrada; lanza RuntimeError si ya lo está. 
        if not self._closed:
            try:
                #Luego, intenta cerrar la sesión y limpiar los recursos locales. 
                self.session.close()
                self.session.headers.pop("X-MSTR-AuthToken", None)
                self.session.cookies.clear()
                self._closed = True
            #Si ocurre un error al liberar recursos, registra el error y vuelve a lanzar la excepción.
            except Exception as exc:
                self.logger.error("close: error al liberar los recursos locales (%s).", type(exc).__name__)
                raise

    #Propiedad que permite usar la instancia con la declaración with; el login sigue siendo explícito. Lanza RuntimeError si la instancia está cerrada.
    def __enter__(self):
        """Permite usar la instancia con with; el login sigue siendo explícito."""
        self._ensure_open()
        return self

    #Propiedad que permite usar la instancia con la declaración with; intenta cerrar la sesión y liberar recursos al salir. Lanza RuntimeError si la instancia está cerrada.
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

