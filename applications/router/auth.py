from fastapi import APIRouter, HTTPException, Request
from libs.lb_database import filter_data, add_data, update_data, delete_data, get_data_by_id, get_data_by_attribute, UserDTO
from applications.utils.utils_auth import LoginDTO, SetUserDTO
from applications.utils.utils_auth import hash_password

class AuthRouter(APIRouter):
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route('/login', self.login, methods=['POST'])
        self.router.add_api_route('/register', self.register, methods=['POST'])
        self.router.add_api_route('/me', self.me, methods=['GET'])
        self.router.add_api_route('/me', self.set_me, methods=['PATCH'])
        self.router.add_api_route('/users', self.get_users, methods=['GET'])
        self.router.add_api_route('/users/{id}', self.get_user_by_id, methods=['GET'])
        self.router.add_api_route('/users/{id}', self.delete_user_by_id, methods=['DELETE'])

    def login(self, login_dto: LoginDTO):
        try:
            user = get_data_by_attribute("user", "username", login_dto.username)

            if user["password"] == hash_password(login_dto.password):
                return user

            return HTTPException(status_code=404, detail="Username or passwrdo is not valid")
        except Exception:
            return HTTPException(status_code=404, detail="Username or passwrdo is not valid")
    
    def register(self, request: Request, register_dto: UserDTO):
        hashed_password = hash_password(register_dto.password)
        register_dto.password = hashed_password
        if register_dto.level > request.state.user.level:
            raise HTTPException(status_code=401, detail="You are not authorized to perform this action, you are not an admin")
        return add_data("user", register_dto.dict())
    
    def me(self, request: Request):
        return request.state.user

    def set_me(self, request: Request, set_user_dto: SetUserDTO):
        return update_data("user", request.state.user.id, set_user_dto.dict())
    
    def get_users(self, request: Request):
        return filter_data("user", {"level": request.state.user.level})
    
    def get_user_by_id(self, request: Request, id: int):
        return get_data_by_id("user", id)
    
    def delete_user_by_id(self, request: Request, id: int):
        return delete_data("user", id)