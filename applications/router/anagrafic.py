from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response
from typing import Dict, Union, Optional
import libs.lb_log as lb_log
from libs.lb_database import VehicleDTO, SocialReasonDTO, MaterialDTO, filter_data, add_data, update_data, delete_data, delete_all_data, load_records_into_db, required_columns, required_dtos
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params

class AnagraficRouter:
    def __init__(self):
        self.router = APIRouter()
        
        self.router.add_api_route('/list/{anagrafic}', self.getListAnagrafic, methods=['GET'])
        self.router.add_api_route('/{anagrafic}', self.addAnagrafic, methods=['POST'])
        self.router.add_api_route('/{anagrafic}/{id}', self.setAnagrafic, methods=['PATCH'])
        self.router.add_api_route('/{anagrafic}/{id}', self.deleteAnagrafic, methods=['DELETE'])
        self.router.add_api_route('/{anagrafic}', self.deleteAllAnagrafic, methods=['DELETE'])
        self.router.add_api_route('/upload-file/{anagrafic}', self.upload_file, methods=['POST'])

    async def getListAnagrafic(self, anagrafic: str, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None):
        if anagrafic not in required_columns:
            raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")
        try:
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            data, total_rows = filter_data(anagrafic, query_params, limit, offset)
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addAnagrafic(self, anagrafic: str, body: Union[VehicleDTO, SocialReasonDTO, MaterialDTO]):
        if anagrafic not in required_columns:
            raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

        # Definizione delle colonne richieste
        required_dto = required_dtos[anagrafic]

        data_parsed = required_dto(**body.dict())

        if not isinstance(data_parsed, required_dto):
            raise HTTPException(status_code=400, detail=f"Invalid body for {anagrafic}")

        try:
            add_data(anagrafic, data_parsed.dict())
            return {"message": "Data added successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def setAnagrafic(self, anagrafic: str, id: int, body: Union[VehicleDTO, SocialReasonDTO, MaterialDTO]):
        if anagrafic not in required_columns:
            raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

        # Definizione delle colonne richieste
        required_dto = required_dtos[anagrafic]

        data_parsed = required_dto(**body.dict())

        lb_log.warning(data_parsed)

        if not isinstance(data_parsed, required_dto):
            raise HTTPException(status_code=400, detail=f"Invalid body for {anagrafic}")

        try:
            update_data(anagrafic, id, data_parsed.dict())
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"{e}")

        return {"message": "Data updated successfully"}

    async def deleteAnagrafic(self, anagrafic: str, id: int):
        if anagrafic not in required_columns:
            raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

        try:
            delete_data(anagrafic, id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"{e}")
        return {"message": "Data deleted successfully"}

    async def deleteAllAnagrafic(self, anagrafic: str):
        if anagrafic not in required_columns:
            raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")
        try:
            length = delete_all_data(anagrafic)
            return {"message": f"{length} records deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def upload_file(self, anagrafic: str, file: UploadFile = File(...)):
        # Verifica l'estensione del file
        if file.content_type not in ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            raise HTTPException(status_code=400, detail="File type not supported")

        try:
            # Leggi il file in base al tipo di contenuto
            if file.content_type == "text/csv":
                df = pd.read_csv(file.file)
            elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df = pd.read_excel(file.file)

            # Rimuovi le colonne senza titolo (solitamente con nome 'Unnamed') e verifica che non ci siano
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            if anagrafic not in required_columns:
                raise HTTPException(status_code=400, detail=f"Anagrafic {anagrafic} is not supported")

            # Definizione delle colonne richieste
            required_column = required_columns[anagrafic]

            allowed_columns = set(required_column.keys())

            # Verifica se ci sono colonne non previste
            if not set(df.columns).issubset(allowed_columns):
                unexpected_columns = set(df.columns) - allowed_columns
                raise HTTPException(status_code=400, detail=f"Unexpected columns found: {', '.join(unexpected_columns)}")

            # Aggiungi le colonne mancanti con valore None e verifica i tipi delle colonne esistenti
            for column, expected_type in required_column.items():
                if column not in df.columns:
                    df[column] = None  # Colonna assente nel file, aggiunta con valori null
                else:
                    # Verifica il tipo di dati della colonna esistente e consenti celle vuote
                    if not df[column].map(lambda x: pd.isna(x) or isinstance(x, expected_type)).all():
                        raise HTTPException(status_code=400, detail=f"Column '{column}' must be of type {expected_type} if present")

            # Sostituisci valori NaN, Inf e -Inf con None
            df = df.replace([np.nan, np.inf, -np.inf], None)

        except Exception as e:
            # Log dell'errore e risposta HTTP 500
            lb_log.error(f"Error reading file: {e}")
            raise HTTPException(status_code=500, detail="Error reading file") from e

        # Converti i dati in JSON
        data = df.to_dict(orient="records")

        try:
            # Salva i dati nel database
            length = load_records_into_db(anagrafic, data)

            return {"message": f"{length} records loaded successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")