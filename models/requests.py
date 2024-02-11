from pydantic import BaseModel, model_validator, Field
from managers.db import db_man
from fastapi import HTTPException


class RegisterData(BaseModel):
    username: str
    hashed_password: str
    client_id: str

    @model_validator(mode='after')
    def check_username(self) -> 'RegisterData':
        username = self.username
        if not username:
            raise HTTPException(status_code=400, detail='Username can not be empty')
        if ' ' in username or '\n' in username:
            raise HTTPException(status_code=400, detail='Username can not contain whitespaces')
        if len(username) < 6:
            raise HTTPException(status_code=400, detail='Username must have at least 6 characters')
        if db_man.exist.user(username=username):
            raise HTTPException(status_code=400, detail='This username is already taken')
        return self

    @model_validator(mode='after')
    def check_client_id(self) -> 'RegisterData':
        client_id = self.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail='Client_id can not be empty')
        if ' ' in client_id or '\n' in client_id:
            raise HTTPException(status_code=400, detail='Client_id can not contain whitespaces')
        return self

    @model_validator(mode='after')
    def check_hashed_password(self) -> 'RegisterData':
        hashed_password = self.hashed_password
        if not hashed_password:
            raise HTTPException(status_code=400, detail='Password can not be empty')
        if ' ' in hashed_password or '\n' in hashed_password:
            raise HTTPException(status_code=400, detail='Password can not contain whitespaces')
        return self


class LoginData(BaseModel):
    username: str
    hashed_password: str
    client_id: str

    @model_validator(mode='after')
    def check_username(self) -> 'LoginData':

        username = self.username
        if not username:
            raise HTTPException(status_code=400, detail='Username can not be empty')
        if ' ' in username or '\n' in username:
            raise HTTPException(status_code=400, detail='Username can not contain whitespaces')
        if not db_man.exist.user(username=username):
            raise HTTPException(status_code=400, detail='No user found with this credentials')
        return self

    @model_validator(mode='after')
    def check_client_id(self) -> 'LoginData':
        client_id = self.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail='Client_id can not be empty')
        if ' ' in client_id or '\n' in client_id:
            raise HTTPException(status_code=400, detail='Client_id can not contain whitespaces')
        return self

    @model_validator(mode='after')
    def check_hashed_password(self) -> 'LoginData':
        hashed_password = self.hashed_password
        if not hashed_password:
            raise HTTPException(status_code=400, detail='Password can not be empty')
        if ' ' in hashed_password or '\n' in hashed_password:
            raise HTTPException(status_code=400, detail='Password can not contain whitespaces')
        return self


class SendData(BaseModel):
    chat_id: int
    content: str

