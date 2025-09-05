from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from typing import Dict, Union, Optional
from modules.md_database.md_database import upload_file_datas_required_columns, LockRecordType
from modules.md_database.interfaces.driver import Driver, AddDriverDTO, SetDriverDTO
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.delete_all_data_if_not_correlations import delete_all_data_if_not_correlations
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.load_datas_into_db import load_datas_into_db
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
import pandas as pd
import numpy as np
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket
from applications.middleware.writable_user import is_writable_user

class DriverRouter(WebSocket):
    def __init__(self):
        super().__init__()

        self.router = APIRouter()
        
        self.router.add_api_route('/list', self.getListDrivers, methods=['GET'])
        self.router.add_api_route('', self.addDriver, methods=['POST'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/{id}', self.setDriver, methods=['PATCH'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/{id}', self.deleteDriver, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('', self.deleteAllDrivers, methods=['DELETE'], dependencies=[Depends(is_writable_user)])
        self.router.add_api_route('/upload-file', self.upload_file, methods=['POST'], dependencies=[Depends(is_writable_user)])

    async def getListDrivers(self, query_params: Dict[str, Union[str, int]] = Depends(get_query_params), limit: Optional[int] = None, offset: Optional[int] = None):
        try:
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            data, total_rows = filter_data("driver", query_params, limit, offset, None, None, ('date_created', 'desc'))
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addDriver(self, body: AddDriverDTO):
        try:
            data = add_data("driver", body.dict())
            driver = Driver(**data).json()
            await self.broadcastAddAnagrafic("driver", {"driver": driver})
            await self.broadcastAddAnagrafic("access", {"driver": driver})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setDriver(self, request: Request, id: int, body: SetDriverDTO):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "driver", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the driver with id '{id}' before to update that")
            data = update_data("driver", id, body.dict())
            driver = Driver(**data).json()
            await self.broadcastUpdateAnagrafic("driver", {"driver": driver})
            await self.broadcastUpdateAnagrafic("access", {"driver": driver})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            if status_code == 400:
                locked_data = None
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def deleteDriver(self, request:Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "driver", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"You need to block the driver with id '{id}' before to update that")
            check_driver_accesses = get_data_by_id("driver", id)
            if check_driver_accesses and len(check_driver_accesses["accesses"]) > 0:
                raise HTTPException(status_code=400, detail=f"L'autista con id '{id}' è assegnato a delle pesate salvate")
            data = delete_data("driver", id)
            driver = Driver(**data).json()
            await self.broadcastDeleteAnagrafic("driver", {"driver": driver})
            await self.broadcastDeleteAnagrafic("access", {"driver": driver})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def deleteAllDrivers(self):
        try:
            deleted_count, preserved_count, total_records = delete_all_data_if_not_correlations("driver")
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
            required_column = upload_file_datas_required_columns["driver"]

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
            length = load_datas_into_db("driver", data)

            return {"message": f"{length} records loaded successfully"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")