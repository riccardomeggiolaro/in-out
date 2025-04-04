import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
from urllib.parse import urlparse

def capture_camera_image(camera_url, timeout=5):
    date_capture = None
    image_data = None
    file_size = None
    status = None
    error_details = None

    try:
        # Estrae username e password dalla URL
        parsed_url = urlparse(camera_url)
        username = parsed_url.username
        password = parsed_url.password

        # Effettua la richiesta HTTP con autenticazione digest
        response = requests.get(
            camera_url,
            auth=HTTPDigestAuth(username, password),
            stream=True,
            verify=False,  # Aggiungiamo questo se la telecamera usa HTTPS con certificato auto-firmato
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