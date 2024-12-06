from fastapi import APIRouter, HTTPException, Request
from libs.lb_database import filter_data, add_data, update_data, delete_data, get_data_by_id, UserDTO, LoginDTO
from applications.utils.utils_auth import TokenData, SetUserDTO
from typing import Callable
from datetime import datetime, timedelta
import jwt
import bcrypt

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
        user = get_data_by_attribute("user", "username", login_dto.username)
        if not user:
            raise HTTPException(status_code=401, detail="Credenziali errate")
        hashed_password = self.hash_password(login_dto.password)
        if user.password != hashed_password:
            raise HTTPException(status_code=401, detail="Credenziali errate")
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token}
    
    def register(self, request: Request, register_dto: UserDTO):
        hashed_password = self.hash_password(register_dto.password)
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
    
    def hash_password(self, password: str) -> str:
        # Convert password to bytes and generate salt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        
        # Hash the password with the generated salt
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        return hashed_password.decode('utf-8')