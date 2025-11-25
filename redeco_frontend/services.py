import requests
from django.conf import settings


class RedeCoAPIError(Exception):
    pass


def get_token(username: str, password: str, timeout: int = 10) -> str:
    """Call the REDECO auth endpoint to obtain token_access.

    The Postman collection indicates the token endpoint is:
    https://api.condusef.gob.mx/auth/users/token/

    Note: Postman used GET with a JSON body; we'll mirror that behaviour using
    requests.request so the library will send the JSON payload even on GET.
    """
    base = getattr(settings, 'REDECO_API_BASE', 'https://api.condusef.gob.mx')
    url = f"{base.rstrip('/')}/auth/users/token/"
    payload = {"username": username, "password": password}

    try:
        resp = requests.request('GET', url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise RedeCoAPIError(f"Error connecting to REDECO API: {exc}") from exc

    if resp.status_code >= 400:
        # try to surface a concise JSON error message if present
        try:
            data = resp.json()
        except Exception:
            # non-json body
            raise RedeCoAPIError(f"API returned {resp.status_code}: {resp.text}")

        # helper to extract human-friendly message from various shapes
        def _extract_message(d):
            if not isinstance(d, dict):
                return None
            for key in ('message', 'msg', 'detail', 'error'):
                v = d.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, list) and v:
                    return '; '.join(str(x) for x in v)

            # nested common containers
            for nested_key in ('data', 'user', 'errors'):
                nested = d.get(nested_key)
                if isinstance(nested, dict):
                    m = _extract_message(nested)
                    if m:
                        return m

            # fallback: return first string value
            for v in d.values():
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None

        msg = _extract_message(data) or f"API returned {resp.status_code}"
        raise RedeCoAPIError(msg)

    try:
        data = resp.json()
    except ValueError:
        raise RedeCoAPIError("API did not return JSON")

    # The API may return different shapes. Known examples:
    # - {'data': {'token_access': '...'}}
    # - {'msg': 'Login exitoso!!!', 'user': {'token_access': '...'}}
    # - {'token': '...'}
    token = None
    if isinstance(data, dict):
        # direct keys
        token = data.get('token') or data.get('access')

        # common nested location used in examples
        if not token:
            nested = data.get('data')
            if isinstance(nested, dict):
                token = nested.get('token_access') or nested.get('token') or nested.get('access')

        # another known shape: data contains 'user' with token_access
        if not token:
            user = data.get('user')
            if isinstance(user, dict):
                token = user.get('token_access') or user.get('token') or user.get('access')

    # fallback: search any string value that looks like a JWT
    if not token and isinstance(data, dict):
        for v in data.values():
            if isinstance(v, str) and v.count('.') == 2:
                token = v
                break

    if not token:
        raise RedeCoAPIError(f"Unable to find token in API response: {data}")

    return token


def call_public_endpoint(path: str, params: dict = None, timeout: int = 10) -> dict:
    """Call a public (non-authenticated) REDECO API endpoint.

    Args:
        path: the endpoint path (e.g. 'catalogos/medio-recepcion')
        params: query parameters as dict (optional)
        timeout: request timeout in seconds

    Returns:
        dict: parsed JSON response from API

    Raises:
        RedeCoAPIError: if request fails or returns error status
    """
    base = getattr(settings, 'REDECO_API_BASE', 'https://api.condusef.gob.mx')
    url = f"{base.rstrip('/')}/{path.lstrip('/')}"

    try:
        resp = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise RedeCoAPIError(f"Error connecting to REDECO API: {exc}") from exc

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            raise RedeCoAPIError(f"API returned {resp.status_code}: {resp.text}")

        def _extract_message(d):
            if not isinstance(d, dict):
                return None
            for key in ('message', 'msg', 'detail', 'error'):
                v = d.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, list) and v:
                    return '; '.join(str(x) for x in v)

            for nested_key in ('data', 'errors', 'response'):
                nested = d.get(nested_key)
                if isinstance(nested, dict):
                    m = _extract_message(nested)
                    if m:
                        return m

            for v in d.values():
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None

        msg = _extract_message(data) or f"API returned {resp.status_code}"
        raise RedeCoAPIError(msg)

    try:
        return resp.json()
    except ValueError:
        raise RedeCoAPIError("API did not return JSON")


def call_protected_endpoint(path: str, token: str, params: dict = None, timeout: int = 10) -> dict:
    """Call an authenticated REDECO API endpoint.

    Args:
        path: the endpoint path (e.g. 'catalogos/causas-list/')
        token: JWT token to use in Authorization header
        params: query parameters as dict (optional)
        timeout: request timeout in seconds

    Returns:
        dict: parsed JSON response from API

    Raises:
        RedeCoAPIError: if request fails or returns error status
    """
    base = getattr(settings, 'REDECO_API_BASE', 'https://api.condusef.gob.mx')
    url = f"{base.rstrip('/')}/{path.lstrip('/')}"

    # Ensure token has Bearer prefix if not already present
    auth_token = token if token.startswith('Bearer ') else f'Bearer {token}'
    
    headers = {
        'Authorization': auth_token,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise RedeCoAPIError(f"Error connecting to REDECO API: {exc}") from exc

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            raise RedeCoAPIError(f"API returned {resp.status_code}: {resp.text}")

        def _extract_message(d):
            if not isinstance(d, dict):
                return None
            for key in ('message', 'msg', 'detail', 'error'):
                v = d.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, list) and v:
                    return '; '.join(str(x) for x in v)

            for nested_key in ('data', 'errors', 'response'):
                nested = d.get(nested_key)
                if isinstance(nested, dict):
                    m = _extract_message(nested)
                    if m:
                        return m

            for v in d.values():
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None

        msg = _extract_message(data) or f"API returned {resp.status_code}"
        raise RedeCoAPIError(msg)

    try:
        return resp.json()
    except ValueError:
        raise RedeCoAPIError("API did not return JSON")


def post_reune_consultas_general(token: str, payload, timeout: int = 15) -> dict:
    """POST to REUNE consultas/general with Authorization header.

    Args:
        token: JWT token string to place in Authorization header (no Bearer prefix unless required).
        payload: Python dict/list to send as JSON body (e.g., the envio_3er_trim array).
        timeout: request timeout seconds.

    Returns:
        dict: parsed JSON response from REUNE API.

    Raises:
        RedeCoAPIError: on network errors, HTTP errors, or non-JSON responses.
    """
    base = getattr(settings, 'REUNE_API_BASE', 'https://api-reune.condusef.gob.mx')
    url = f"{base.rstrip('/')}/reune/consultas/general"

    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.Timeout:
        raise RedeCoAPIError(
            "Timeout al conectar con la API REUNE. El servidor no respondió a tiempo. "
            "Por favor, intenta nuevamente en unos minutos."
        )
    except requests.ConnectionError:
        raise RedeCoAPIError(
            "Error de conexión con la API REUNE. Verifica que la URL sea correcta y que el servidor esté disponible. "
            f"URL intentada: {url}"
        )
    except requests.RequestException as exc:
        raise RedeCoAPIError(f"Error al conectar con la API REUNE: {exc}") from exc

    # Handle specific HTTP error codes with friendly messages
    if resp.status_code == 502:
        raise RedeCoAPIError(
            "Error 502 Bad Gateway: El servidor REUNE no está disponible temporalmente. "
            "Esto puede deberse a mantenimiento o problemas del servidor. "
            "Por favor, intenta nuevamente más tarde o contacta a CONDUSEF para verificar el estado del servicio."
        )
    elif resp.status_code == 503:
        raise RedeCoAPIError(
            "Error 503 Service Unavailable: El servidor REUNE está temporalmente fuera de servicio. "
            "Por favor, intenta nuevamente más tarde."
        )
    elif resp.status_code == 504:
        raise RedeCoAPIError(
            "Error 504 Gateway Timeout: El servidor REUNE tardó demasiado en responder. "
            "Por favor, intenta nuevamente."
        )
    elif resp.status_code == 401:
        raise RedeCoAPIError(
            "Error 401 Unauthorized: Token inválido o expirado. "
            "Genera un nuevo token desde la página principal."
        )
    elif resp.status_code == 403:
        raise RedeCoAPIError(
            "Error 403 Forbidden: No tienes permisos para acceder a este recurso. "
            "Verifica que tu token tenga los permisos necesarios."
        )
    elif resp.status_code >= 400:
        # Try to extract detailed error message from response
        try:
            data = resp.json()
        except Exception:
            raise RedeCoAPIError(f"API REUNE retornó error {resp.status_code}: {resp.text[:200]}")

        # REUNE negative example uses keys: message and errors by folio
        msg = None
        if isinstance(data, dict):
            msg = data.get('message') or data.get('msg') or data.get('detail') or data.get('error')
        raise RedeCoAPIError(msg or f"API REUNE retornó error {resp.status_code}")

    try:
        return resp.json()
    except ValueError:
        raise RedeCoAPIError("La API REUNE no retornó un JSON válido en la respuesta")


def create_queja(token: str, payload, timeout: int = 20) -> dict:
    """POST a REDECO /redeco/quejas para crear una queja.

    Args:
        token: JWT token string to use in Authorization header.
        payload: dict with the queja data (matching Postman sample).
        timeout: seconds for request timeout.

    Returns:
        dict: parsed JSON response from REDECO.

    Raises:
        RedeCoAPIError on network/API errors.
    """
    base = getattr(settings, 'REDECO_API_BASE', 'https://api.condusef.gob.mx')
    url = f"{base.rstrip('/')}/redeco/quejas"

    # Ensure token has Bearer prefix if not already present
    auth_token = token if token.startswith('Bearer ') else f'Bearer {token}'
    
    headers = {
        'Authorization': auth_token,
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.Timeout:
        raise RedeCoAPIError("Timeout al conectar con la API REDECO. Por favor intenta nuevamente más tarde.")
    except requests.ConnectionError:
        raise RedeCoAPIError(f"Error de conexión con la API REDECO. URL intentada: {url}")
    except requests.RequestException as exc:
        raise RedeCoAPIError(f"Error al conectar con la API REDECO: {exc}") from exc

    if resp.status_code in (200, 201):
        try:
            return resp.json()
        except Exception:
            return {'status': 'ok', 'code': resp.status_code, 'text': resp.text}

    # Handle common errors with friendly messages
    if resp.status_code == 401:
        raise RedeCoAPIError("Error 401 Unauthorized: token inválido o expirado. Genera un nuevo token.")
    if resp.status_code == 403:
        raise RedeCoAPIError("Error 403 Forbidden: no tienes permisos para crear quejas.")
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            raise RedeCoAPIError(f"API REDECO retornó error {resp.status_code}: {resp.text[:200]}")

        # Try to extract message
        msg = None
        if isinstance(data, dict):
            msg = data.get('message') or data.get('msg') or data.get('detail') or data.get('error')
        raise RedeCoAPIError(msg or f"API REDECO retornó error {resp.status_code}")
