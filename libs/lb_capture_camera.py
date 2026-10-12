import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from datetime import datetime
from urllib.parse import urlparse, urlunparse

def capture_camera_image(camera_url, timeout=5):
    date_capture = None
    image_data = None
    file_size = None
    status = None
    error_details = None

    try:
        # Estrae username e password dalla URL e ricostruisce l'URL senza credenziali
        parsed_url = urlparse(camera_url)
        username = parsed_url.username
        password = parsed_url.password

        # Ricostruisce l'URL senza credenziali per evitare problemi con requests + Digest
        clean_netloc = parsed_url.hostname
        if parsed_url.port:
            clean_netloc = f"{clean_netloc}:{parsed_url.port}"
        clean_url = urlunparse((
            parsed_url.scheme,
            clean_netloc,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))

        auth = HTTPDigestAuth(username, password) if username else None

        # Effettua la richiesta HTTP con autenticazione digest
        response = requests.get(
            clean_url,
            auth=auth,
            stream=True,
            verify=False,  # Necessario se la telecamera usa HTTPS con certificato auto-firmato
            timeout=timeout
        )

        # Se Digest fallisce (alcune cam usano Basic), riprova con Basic
        if response.status_code == 401 and username:
            response = requests.get(
                clean_url,
                auth=HTTPBasicAuth(username, password),
                stream=True,
                verify=False,
                timeout=timeout
            )

        # Verifica se la richiesta è andata a buon fine
        response.raise_for_status()

        date_capture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_data = response.content
        file_size = len(image_data)
        status = "success"
    except requests.exceptions.RequestException as e:
        date_capture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_data = b""
        file_size = 0
        status = "error"
        error_details = e
    finally:
        return {
            "date": date_capture,
            "image": image_data,
            "size": file_size,
            "status": status,
            "error_details": error_details
        }
