from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Union, Optional
from modules.md_database.md_database import LockRecordType
from modules.md_database.interfaces.card_registry import CardRegistry, AddCardRegistryDTO, SetCardRegistryDTO
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.delete_all_data import delete_all_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.get_data_by_attributes import get_data_by_attributes
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.unlock_record_by_id import unlock_record_by_id
from applications.utils.utils import get_query_params
from applications.router.anagrafic.web_sockets import WebSocket
from applications.middleware.super_admin import is_super_admin


class CardRegistryRouter(WebSocket):
    def __init__(self):
        super().__init__()

        self.router = APIRouter()

        self.router.add_api_route('/list', self.getListCardRegistry, methods=['GET'])
        self.router.add_api_route('', self.addCard, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/{id}', self.setCard, methods=['PATCH'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/{id}', self.deleteCard, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.deleteAllCards, methods=['DELETE'], dependencies=[Depends(is_super_admin)])

    async def getListCardRegistry(
        self,
        query_params: Dict[str, Union[str, int]] = Depends(get_query_params),
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None
    ):
        try:
            if limit is not None:
                del query_params["limit"]
            if offset is not None:
                del query_params["offset"]
            if order_by is not None:
                del query_params["order_by"]
            if order_direction is not None:
                del query_params["order_direction"]
            sort = (order_by, order_direction if order_direction else 'asc') if order_by else ('date_created', 'desc')
            data, total_rows = filter_data("card-registry", query_params, limit, offset, None, None, sort)
            return {
                "data": data,
                "total_rows": total_rows
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")

    async def addCard(self, body: AddCardRegistryDTO):
        try:
            data = add_data("card-registry", body.dict())
            card = CardRegistry(**data).json()
            await self.broadcastAddAnagrafic("card-registry", {"card-registry": card})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 400)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)

    async def setCard(self, request: Request, id: int, body: SetCardRegistryDTO):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "card-registry", "idRecord": id, "type": LockRecordType.UPDATE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"Devi bloccare la tessera con id '{id}' prima di modificarla")
            data = update_data("card-registry", id, body.dict())
            card = CardRegistry(**data).json()
            await self.broadcastUpdateAnagrafic("card-registry", {"card-registry": card})
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

    async def deleteCard(self, request: Request, id: int):
        locked_data = None
        try:
            locked_data = get_data_by_attributes('lock_record', {"table_name": "card-registry", "idRecord": id, "type": LockRecordType.DELETE, "user_id": request.state.user.id})
            if not locked_data:
                raise HTTPException(status_code=403, detail=f"Devi bloccare la tessera con id '{id}' prima di eliminarla")
            # Check if the card code is currently assigned to an open access
            card = get_data_by_id("card-registry", id)
            if card:
                from modules.md_database.md_database import SessionLocal, Access, AccessStatus
                with SessionLocal() as session:
                    open_access = session.query(Access).filter(
                        Access.idCardRegistry == id,
                        Access.status != AccessStatus.CLOSED
                    ).first()
                    if open_access:
                        raise HTTPException(status_code=400, detail=f"La tessera è assegnata ad una prenotazione aperta e non può essere eliminata")
            data = delete_data("card-registry", id)
            card = CardRegistry(**data).json()
            await self.broadcastDeleteAnagrafic("card-registry", {"card-registry": card})
            return data
        except Exception as e:
            status_code = getattr(e, 'status_code', 404)
            detail = getattr(e, 'detail', str(e))
            raise HTTPException(status_code=status_code, detail=detail)
        finally:
            if locked_data:
                unlock_record_by_id(locked_data["id"])

    async def deleteAllCards(self):
        try:
            # Only delete cards not assigned to open accesses
            from modules.md_database.md_database import SessionLocal, Access, AccessStatus, CardRegistry as CardRegistryModel
            with SessionLocal() as session:
                open_card_ids = {a.idCardRegistry for a in session.query(Access).filter(
                    Access.status != AccessStatus.CLOSED,
                    Access.idCardRegistry != None
                ).all()}
                cards_to_delete = session.query(CardRegistryModel).filter(
                    ~CardRegistryModel.id.in_(open_card_ids)
                ).all()
                deleted_count = len(cards_to_delete)
                preserved_count = session.query(CardRegistryModel).filter(
                    CardRegistryModel.id.in_(open_card_ids)
                ).count()
                total_records = session.query(CardRegistryModel).count()
                for card in cards_to_delete:
                    session.delete(card)
                session.commit()
            return {
                "deleted_count": deleted_count,
                "preserved_count": preserved_count,
                "total_records": total_records
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{e}")
