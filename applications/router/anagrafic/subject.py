from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from typing import Dict, Union, Optional
from modules.md_database.md_database import upload_file_datas_required_columns, LockRecordType
from modules.md_database.interfaces.subject import Subject, AddSubjectDTO, SetSubjectDTO
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_all_data_if_not_correlations import delete_all_data_if_not_correlations
from modules.md_database.functions.load_datas_into_db import load_datas_into_db
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket

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
            data, total_rows = filter_data("subject", query_params, limit, offset, None, None, ('date_created', 'desc'))
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addSubject(self, body: AddSubjectDTO):
        try:
            data = add_data("subject", body.dict())
            subject = Subject(**data).json()
            await self.broadcastAddAnagrafic("subject", {"subject": subject})
            await self.broadcastAddAnagrafic("reservation", {"subject": subject})
            return data
        except Exception as e:
            # Verifica se l'eccezione ha un attributo 'status_code' e usa quello, altrimenti usa 404
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setSubject(self, request: Request, id: int, body: SetSubjectDTO):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "subject", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=400, detail=f"You need to block the subject with id '{id}' before to update that")
            data = update_data("subject", id, body.dict())
            subject = Subject(**data).json()
            await self.broadcastUpdateAnagrafic("subject", {"subject": subject})
            await self.broadcastUpdateAnagrafic("reservation", {"subject": subject})
            return data
        except Exception as e:
            # Verifica se l'eccezione ha un attributo 'status_code' e usa quello, altrimenti usa 404
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            if status_code == 400:
                locked_data = None
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def deleteSubject(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "subject", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the subject with id '{id}' before to update that")
            check_subject_reservations = get_data_by_id("subject", id)
            if check_subject_reservations and len(check_subject_reservations["reservations"]) > 0:
                raise HTTPException(status_code=400, detail=f"Il soggetto con id '{id}' è assegnato a delle pesate salvate")
            data = delete_data("subject", id)
            subject = Subject(**data).json()
            await self.broadcastDeleteAnagrafic("subject", {"subject": subject})
            await self.broadcastDeleteAnagrafic("reservation", {"subject": subject})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

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
            raise HTTPException(status_code=500, detail="Error reading file") from e

        # Converti i dati in JSON
        data = df.to_dict(orient="records")

        try:
            # Salva i dati nel database
            length = load_datas_into_db("subject", data)

            return {"message": f"{length} records loaded successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")