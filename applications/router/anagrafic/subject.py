from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response
from typing import Dict, Union, Optional
from modules.md_database.md_database import upload_file_datas_required_columns
from modules.md_database.dtos.subject import Subject, AddSubjectDTO, SetSubjectDTO, FilterSubjectDTO
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.load_datas_into_db import load_datas_into_db
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from modules.md_database.functions.get_data_by_id import get_data_by_id
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket
import json

class SubjectRouter(WebSocket):
    def __init__(self):
        super().__init__()
        
        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListSubjects, methods=['GET'])
        self.router.add_api_route('', self.addSubject, methods=['POST'])
        self.router.add_api_route('/{id}', self.setSubject, methods=['PATCH'])
        self.router.add_api_route('/{id}', self.deleteSubject, methods=['DELETE'])
        self.router.add_api_route('', self.deleteAllSubjects, methods=['DELETE'])
        self.router.add_api_route('/upload-file', self.upload_file, methods=['POST'])

    async def getListSubjects(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None):
        try:
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            data, total_rows = filter_data("subject", query_params, limit, offset, ('date_created', 'desc'))
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addSubject(self, body: AddSubjectDTO):
        try:
            if body.social_reason and get_data_by_attribute("subject", "social_reason", body.social_reason):
                raise ValueError(f"La ragione sociale '{body.social_reason}' è già esistente")
            if body.cfpiva and get_data_by_attribute("subject", "cfpiva", body.cfpiva):
                raise ValueError(f"La CF/P.Iva '{body.cfpiva}' è già esistente")
            data = add_data("subject", body.dict())
            await self.broadcastAddAnagrafic("subject", Subject(**data).dict())
            return data
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def setSubject(self, id: int, body: SetSubjectDTO):
        try:
            if body.social_reason:
                subject = get_data_by_attribute("subject", "social_reason", body.social_reason)
                if subject and subject["id"] != id:
                    raise ValueError(f"La ragione sociale '{body.social_reason}' è già esistente")
            if body.cfpiva:
                subject = get_data_by_attribute("subject", "cfpiva", body.cfpiva)
                if subject and subject["id"] != id:
                    raise ValueError(f"La CF/P.Iva '{body.cfpiva}' è già esistente")
            data = update_data("subject", id, body.dict())
            await self.broadcastUpdateAnagrafic("subject", Subject(**data).dict())
            return data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"{e}")

        return {"message": "Data updated successfully"}

    async def deleteSubject(self, id: int):
        try:
            subject = get_data_by_id("subject", id)
            if subject and len(subject["reservations"]) > 0:
                raise ValueError(f"Non puoi eliminare il soggetto con id '{id}' perchè è assegnato a delle pesate salvate")
            data = delete_data("subject", id)
            await self.broadcastDeleteAnagrafic("subject", Subject(**data).dict())
            return data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"{e}")
        return {"message": "Data deleted successfully"}

    async def deleteAllSubjects(self):
        try:
            deleted_count, preserved_count, total_records = delete_all_data_if_not_correlations("subject")
            return {
                "deleted_count": deleted_count,
                "preserved_count": preserved_count,
                "total_records": total_records
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def upload_file(self, file: UploadFile = File(...)):
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

            # Definizione delle colonne richieste
            required_column = upload_file_datas_required_columns["subject"]

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
            length = load_datas_into_db("subject", data)

            return {"message": f"{length} records loaded successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")