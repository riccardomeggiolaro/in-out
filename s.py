from fastapi import FastAPI
from pyngrok import ngrok
import uvicorn

ngrok.set_auth_token("2mbKhRzUKfW6okLpCDGbZDB2r19_5bs5RDKWrXvNb1b5wKC8M")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# Aggiungi qui altre route e funzionalità del tuo script

# Configura ngrok
ngrok_tunnel = ngrok.connect(8000)
print('Public URL:', ngrok_tunnel.public_url)

# Avvia il server
uvicorn.run(app, port=8000)