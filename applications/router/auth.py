from fastapi import APIRouter, HTTPException, Request
from libs.lb_database import filter_data, add_data, update_data, delete_data, get_data_by_id, UserDTO, LoginDTO
from applications.utils.utils_auth import TokenData
from typing import Callable
from datetime import datetime, timedelta
import jwt

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
        # Qui puoi aggiungere la logica di autenticazione dell'utente (ad esempio, controllo su DB)
        if username == "testuser" and password == "password123":  # Esempio statico
            access_token = create_access_token(data={"sub": username})
            return {"access_token": access_token}
        else:
            raise HTTPException(status_code=401, detail="Credenziali errate")
    
    def register(self, register_dto: UserDTO):
        pass
    
    def me(self):
        pass

    def set_me(self):
        pass
    
    def get_users(self):
        pass
    
    def get_user_by_id(self, id: int):
        pass
    
    def delete_user_by_id(self, id: int):
        pass