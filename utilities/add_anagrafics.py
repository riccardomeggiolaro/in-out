import pandas as pd
import requests
from io import BytesIO

# Dati
vehicles = [
    {"plate": "FX123AB", "description": "Bilico container", "tare": 7800},
    {"plate": "GD456CD", "description": "Cassone ribaltabile", "tare": 8200},
    {"plate": "HH789EF", "description": "Frigo 3 assi", "tare": 9100},
    {"plate": "IK321GH", "description": "Pianale lungo", "tare": 7500},
    {"plate": "LM654IJ", "description": "Telonato standard", "tare": 8000},
    {"plate": "NP987KL", "description": "Cisterna carburante", "tare": 9500},
    {"plate": "QR258MN", "description": "Portacontainer 40'", "tare": 8300},
    {"plate": "ST369OP", "description": "Pianale ribassato", "tare": 7700},
    {"plate": "UV741QR", "description": "Autotreno legname", "tare": 8800},
    {"plate": "WX852ST", "description": "Centinato doppio", "tare": 8100}
]

drivers = [
    {"social_reason": "Luca Rossi", "telephone": "+39 335 4125897"},
    {"social_reason": "Marco Bianchi", "telephone": "+39 347 9812365"},
    {"social_reason": "Giuseppe Verdi", "telephone": "+39 338 6245198"},
    {"social_reason": "Alessandro Neri", "telephone": "+39 333 7158420"},
    {"social_reason": "Francesco Galli", "telephone": "+39 340 2598741"},
    {"social_reason": "Davide Colombo", "telephone": "+39 345 6982143"},
    {"social_reason": "Matteo Ferri", "telephone": "+39 334 1205987"},
    {"social_reason": "Stefano Romano", "telephone": "+39 339 4581207"},
    {"social_reason": "Antonio Rinaldi", "telephone": "+39 347 9316428"},
    {"social_reason": "Roberto Moretti", "telephone": "+39 348 7512304"}
]

vectors = [
    {"social_reason": "Trasporti Nord Srl", "telephone": "+39 030 6587412", "cfpiva": "01234560987"},
    {"social_reason": "Logistica Sud Spa", "telephone": "+39 081 9854210", "cfpiva": "02345670125"},
    {"social_reason": "Spedizioni Italia Snc", "telephone": "+39 06 87451236", "cfpiva": "03456781236"},
    {"social_reason": "Autotrasporti Europa Srl", "telephone": "+39 045 6598714", "cfpiva": "04567892347"},
    {"social_reason": "Magazzini Verdi Spa", "telephone": "+39 02 99874521", "cfpiva": "05678903458"},
    {"social_reason": "Distribuzione Ovest Snc", "telephone": "+39 011 7548963", "cfpiva": "06789014569"},
    {"social_reason": "Traslochi Express Srl", "telephone": "+39 055 6987412", "cfpiva": "07890125670"},
    {"social_reason": "Autotrasporti Delta Spa", "telephone": "+39 0521 874569", "cfpiva": "08901236781"},
    {"social_reason": "LogiCenter Group Srl", "telephone": "+39 099 7458963", "cfpiva": "09012347892"},
    {"social_reason": "Cargo Point Italia Srl", "telephone": "+39 0721 985412", "cfpiva": "10123458903"}
]

subjects = [
    {"social_reason": "Cava San Pietro Srl", "telephone": "+39 030 7524896", "cfpiva": "01234560987"},
    {"social_reason": "Acciaierie Lombarde Spa", "telephone": "+39 02 69874512", "cfpiva": "02345670125"},
    {"social_reason": "Calcestruzzi Verdi Srl", "telephone": "+39 035 8745123", "cfpiva": "03456781236"},
    {"social_reason": "EcoRecuperi Nord Snc", "telephone": "+39 045 6598741", "cfpiva": "04567892347"},
    {"social_reason": "Mangimificio Italia Spa", "telephone": "+39 0521 9854712", "cfpiva": "05678903458"},
    {"social_reason": "Consorzio Agricolo Padano", "telephone": "+39 0376 7548963", "cfpiva": "06789014569"},
    {"social_reason": "Cementificio Delta Spa", "telephone": "+39 081 6987412", "cfpiva": "07890125670"},
    {"social_reason": "Metalli Fusi Srl", "telephone": "+39 099 8745698", "cfpiva": "08901236781"},
    {"social_reason": "Impianti Ecologici Centro", "telephone": "+39 06 74589632", "cfpiva": "09012347892"},
    {"social_reason": "Silos Cereali Romagna Snc", "telephone": "+39 0547 985412", "cfpiva": "10123458903"}
]

materials = [
    {"description": "Sabbia"},
    {"description": "Ghiaia"},
    {"description": "Cemento"},
    {"description": "Calcestruzzo"},
    {"description": "Terra"},
    {"description": "Asfalto"},
    {"description": "Mattoni"},
    {"description": "Ferro"},
    {"description": "Legno"},
    {"description": "Rottami metallici"},
    {"description": "Cereali"},
    {"description": "Mangimi"},
    {"description": "Plastica"},
    {"description": "Carta e cartone"},
    {"description": "Rifiuti misti"}
]

# Token di autenticazione
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJiYXJvbnBlc2kiLCJwYXNzd29yZCI6IiQyYiQxMiRQQUhFNGtoNmxuWG8zdzlTRjl0ajdPamVjbzkxdmdXNzVDcFM5QzBuM0JPNHNoYVdHR08ubSIsImxldmVsIjo0LCJkZXNjcmlwdGlvbiI6ImJhcm9ub3Blc2kiLCJkYXRlX2NyZWF0ZWQiOiIyMDI1LTEwLTMxVDEwOjIyOjEwLjIyODgyNiIsImV4cCI6NDkxNTUwNjk1OH0.EsGLRj73mXHK5hJ-FUyKyy51VKKMvIwODXMi5H4Kpos"

# Funzione per creare e inviare file xlsx
def create_and_upload_xlsx(data, filename, endpoint):
    buffer = BytesIO()
    df = pd.DataFrame(data)
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    
    files = {'file': (filename, buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
    
    try:
        response = requests.post(endpoint, files=files, headers=headers)
        print(f"{filename} → {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print("-" * 60)
        return response
    except Exception as e:
        print(f"Errore con {filename}: {e}")
        print("-" * 60)
        return None

# Base URL
base_url = "http://localhost/api/anagrafic"

# Carica tutti i file
print("Inizio caricamento file xlsx...\n")

create_and_upload_xlsx(vehicles, "vehicle", f"{base_url}/vehicle/upload-file")
create_and_upload_xlsx(drivers, "driver", f"{base_url}/driver/upload-file")
create_and_upload_xlsx(vectors, "vector", f"{base_url}/vector/upload-file")
create_and_upload_xlsx(subjects, "subject", f"{base_url}/subject/upload-file")
create_and_upload_xlsx(materials, "material", f"{base_url}/material/upload-file")

print("\nCaricamento completato!")