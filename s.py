from fastapi import FastAPI, Query, HTTPException, Depends, Path
import uvicorn
from pydantic import BaseModel

# Definisci il DTO
class InstanceWeigherDTO(BaseModel):
    name: str

# Simula una funzione di ricerca per l'esistenza dell'istanza
def find_instance(name: str):
    # Implementa la logica di verifica qui
    return name in ["valid_instance1", "valid_instance2"]

# Funzione di validazione comune
def validate_instance_weigher(name: str):
    if not find_instance(name):
        raise HTTPException(status_code=404, detail='Name instance does not exist')
    return name

# Dipendenza per validare il parametro
async def get_instance_weigher(name: str = Depends(validate_instance_weigher)):
    return InstanceWeigherDTO(name=name)

app = FastAPI()

@app.get("/hello/{name}")
async def hello(names: str = Depends(get_instance_weigher)):
    return {"message": f"Hello {name}"}

@app.get("/goodbye/{name}")
async def goodbye(name: str = Depends(get_instance_weigher)):
    return {"message": f"Goodbye {name}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)