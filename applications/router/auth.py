from fastapi import APIRouter, HTTPException, Request, Depends, status
from modules.md_database.functions.filter_data import filter_data
from modules.md_database.functions.add_data import add_data
from modules.md_database.functions.update_data import update_data
from modules.md_database.functions.delete_data import delete_data
from modules.md_database.functions.get_data_by_id import get_data_by_id
from modules.md_database.functions.get_data_by_attribute import get_data_by_attribute
from modules.md_database.interfaces.user import UserDTO, LoginDTO, SetUserDTO
from applications.utils.utils_auth import create_access_token
from applications.middleware.admin import is_admin

class AuthRouter(APIRouter):
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route('/login', self.login, methods=['POST'])
        self.router.add_api_route('/register', self.register, methods=['POST'], dependencies=[Depends(is_admin)])
        self.router.add_api_route('/me', self.me, methods=['GET'])
        self.router.add_api_route('/me', self.set_me, methods=['PATCH'])
        self.router.add_api_route('/users', self.get_users, methods=['GET'], dependencies=[Depends(is_admin)])
        self.router.add_api_route('/user/{id}', self.get_user_by_id, methods=['GET'], dependencies=[Depends(is_admin)])
        self.router.add_api_route('/user/{id}', self.set_user_by_id, methods=['PATCH'], dependencies=[Depends(is_admin)])
        self.router.add_api_route('/user/{id}', self.delete_user_by_id, methods=['DELETE'], dependencies=[Depends(is_admin)])

    def login(self, login_dto: LoginDTO):
        try:
            user = get_data_by_attribute("user", "username", login_dto.username)
            user["date_created"] = user["date_created"].isoformat()
            if user["password"] == login_dto.password:
                return {
                    "access_token": create_access_token(user)
                }
            # Se la password è errata, restituisci un errore generico
            raise HTTPException()
        except Exception as e:
            # Gestisce eventuali errori imprevisti (come la mancanza dell'utente)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    
    def register(self, request: Request, register_dto: UserDTO):
        if register_dto.level >= request.state.user.level:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "You cannot assign a higher or equal access level than your own. "
                    f"Your current access level is {request.state.user.level}, but you're trying to assign level {register_dto.level}."
                )
            )
        return add_data("user", register_dto.dict())
    
    def me(self, request: Request):
        return request.state.user

    def set_me(self, request: Request, set_dto: SetUserDTO):
        return update_data("user", request.state.user.id, set_dto.dict())
    
    def get_users(self, request: Request):
        return filter_data("user")
    
    def get_user_by_id(self, request: Request, id: int):
        return get_data_by_id("user", id)
    
    def set_user_by_id(self, request: Request, id: int, set_password_dto: SetUserDTO):
        try:
            user = get_data_by_id("user", id)
            if user and user["level"] >= request.state.user.level:
                return HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=(
                        f"You cannot delete a user with a higher or equal access level than your own. "
                        f"Your current access level is {request.state.user.level}, "
                        f"but you're trying to delete a user with access level {user['level']}."
                    )
                )
            return update_data("user", id, set_password_dto.dict())
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
    
    def delete_user_by_id(self, request: Request, id: int):
        try:
            user = get_data_by_id("user", id)
            if user:
                if user["id"] == request.state.user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"You cannot delete your self. "
                            f"Your id is {request.state.user.level}, "
                            f"but you're trying to delete a user with id {user['level']}"
                        )
                    )
                if user["level"] >= request.state.user.level:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=(
                            f"You cannot delete a user with a higher or equal access level than your own. "
                            f"Your current access level is {request.state.user.level}, "
                            f"but you're trying to delete a user with access level {user['level']}."
                        )
                    )
            return delete_data("user", id)
        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=str(e)
            )
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )