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

card_registry = [
  { "number": "A001", "code": "3C00CBC1A0" },
  { "number": "A002", "code": "3C00CBFD75" },
  { "number": "A003", "code": "3C00CBF455" },
  { "number": "A004", "code": "3C00B57B9A" },
  { "number": "A005", "code": "3C00CB92D2" },
  { "number": "A006", "code": "3C00CB52656" },
  { "number": "A007", "code": "3C00B71835" },
  { "number": "A008", "code": "3C00B5402B" },
  { "number": "A009", "code": "3C00CB78BA" },
  { "number": "A010", "code": "3C00B70E4C" },
  { "number": "A011", "code": "3C00B638A8" },
  { "number": "A012", "code": "3C00CA2603" },
  { "number": "A013", "code": "3C00CBE10D" },
  { "number": "A014", "code": "3C00C871BC" },
  { "number": "A015", "code": "3C00CAD737" },
  { "number": "A016", "code": "3C00B58FEC" },
  { "number": "A017", "code": "3C00CA5F12" },
  { "number": "A018", "code": "3C00CA04F8" },
  { "number": "A019", "code": "3C00CA03EB" },
  { "number": "A020", "code": "3C00CABD69" },
  { "number": "A021", "code": "3C00B5A760" },
  { "number": "A022", "code": "3C00CBAD19" },
  { "number": "A023", "code": "3C00CB43DF" },
  { "number": "A024", "code": "3C00B5D437" },
  { "number": "A025", "code": "3C00CA4B2A" },
  { "number": "A026", "code": "3C00CC2C04" },
  { "number": "A027", "code": "3C00B6C548" },
  { "number": "A028", "code": "3C00B6729B" },
  { "number": "A029", "code": "3C00CC41B3" },
  { "number": "A030", "code": "3C00C9D1DA" },
  { "number": "A031", "code": "3C00B65BAD" },
  { "number": "A032", "code": "3C00B431C3" },
  { "number": "A033", "code": "3C00B5D941" },
  { "number": "A034", "code": "3C00B54100" },
  { "number": "A035", "code": "3C00CBD3A8" },
  { "number": "A036", "code": "01154A7C55" },
  { "number": "A037", "code": "01154A6DBC" },
  { "number": "A038", "code": "01154A6777" },
  { "number": "A039", "code": "01154A91F9" },
  { "number": "A040", "code": "01154A84C3" },
  { "number": "A041", "code": "01154A8793" },
  { "number": "A042", "code": "01154A865E" },
  { "number": "A043", "code": "01154A5B57" },
  { "number": "A044", "code": "01154A8F83" },
  { "number": "A045", "code": "01154A5BFA" },
  { "number": "A046", "code": "01154A834C" },
  { "number": "A047", "code": "01154A901B" },
  { "number": "A048", "code": "01154A800D" },
  { "number": "A049", "code": "01154A5CCB" },
  { "number": "A050", "code": "01154A7906" }
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
create_and_upload_xlsx(card_registry, "card-registry", f"{base_url}/card-registry/upload-file")

print("\nCaricamento completato!")