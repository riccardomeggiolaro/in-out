import requests
from requests.auth import HTTPDigestAuth
import sqlite3
from datetime import datetime
import io
import libs.lb_log as lb_log

def capture_camera_image(camera_url, username, password, save_dir="captured_images"):
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
        
        return {
            "date_capture": date_capture,
            "image_data": image_data,
            "file_size": file_size,
            "status": status
        }
    except requests.exceptions.RequestException as e:
        date_capture = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        image_data = None
        file_size = 0
        status = f'error: {str(e)}'

        return {
            "date_capture": date_capture,
            "image_data": image_data,
            "file_size": file_size,
            "status": status
        }

def save_image_capture(date_image, image_data, file_size):
    # Connetti al database e salva l'immagine
    conn = init_database()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO images (timestamp, image_data, file_size, status)
        VALUES (?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        image_data,
        file_size,
        'success'
    ))
    
    conn.commit()
    image_id = cursor.lastrowid
    
    return image_id

def init_database():
    """Inizializza il database e crea la tabella se non esiste"""
    conn = sqlite3.connect('camera_images.db')
    cursor = conn.cursor()
    
    # Crea la tabella per le immagini
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            image_data BLOB,
            file_size INTEGER,
            status TEXT
        )
    ''')
    
    conn.commit()
    return conn

if __name__ == "__main__":
    init_database()
    capture_camera_image(camera_url, username, password)