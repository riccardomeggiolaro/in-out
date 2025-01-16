import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime

def capture_camera_image(camera_url, username, password):
    date_capture = None
    image_data = None
    file_size = None
    status = None

    try:
        # Effettua la richiesta HTTP con autenticazione digest
        response = requests.get(
            camera_url,
            auth=HTTPDigestAuth(username, password),
            stream=True,
            verify=False  # Aggiungiamo questo se la telecamera usa HTTPS con certificato auto-firmato
        )
        
        # Verifica se la richiesta è andata a buon fine
        response.raise_for_status()

        date_capture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_data = response.content
        file_size = len(image_data)
        status = "success"
    except requests.exceptions.RequestException as e:
        date_capture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_data = None
        file_size = 0
        status = f'error: {str(e)}'
    finally:
        return {
            "date_capture": date_capture,
            "image_data": image_data,
            "file_size": file_size,
            "status": status
        }