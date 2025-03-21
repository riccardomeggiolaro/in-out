import requests
from datetime import datetime
from urllib.parse import urlparse, urlunparse

def capture_camera_image(camera_url):
    date_capture = None
    image_data = None
    file_size = None
    status = None
    
    try:
        # Parse the URL to extract credentials if present
        parsed_url = urlparse(camera_url)
        
        # Make the HTTP request (credentials in URL will be used automatically)
        response = requests.get(
            camera_url,
            stream=True,
            verify=False  # For cameras using self-signed certificates
        )
        
        # Check if the request was successful
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
            "date": date_capture,
            "image": image_data,
            "size": file_size,
            "status": status
        }