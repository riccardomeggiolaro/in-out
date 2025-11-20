import requests
import json

# URL con i parametri di query
url = "http://10.0.6.71/api/command-weigher/weighing/auto?instance_name=1&weigher_name=P1&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwidXNlcm5hbWUiOiJjYW1jYXB0dXJlcGxhdGUiLCJwYXNzd29yZCI6bnVsbCwibGV2ZWwiOjAsImRlc2NyaXB0aW9uIjoiQ2FtIENhcHR1cmUgUGxhdGUiLCJkYXRlX2NyZWF0ZWQiOiIyMDI1LTEwLTI3VDE2OjE3OjA2LjEyNzQ4MCIsImV4cCI6NDkxNjQ1MTQxNn0.jzVtozMftUqxNfBB97gsvifkBThOHNwBtpyfaLMOB9g"

# Corpo della richiesta (body)
data = {
    "identify": "12345"
}

# Fare la richiesta POST con il corpo in formato JSON
response = requests.post(url, json=data)

# Controlla lo status e la risposta
if response.status_code == 200:
    print("Richiesta eseguita con successo!")
    print("Risposta:", response.json())  # Stampa la risposta JSON
else:
    print("Errore nella richiesta:", response.status_code)
    print("Messaggio di errore:", response.text)