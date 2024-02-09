from typing import Annotated
from fastapi import HTTPException, Depends
from managers.db import db_man
from models.models import User, Token
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def check_token(token: Annotated[str, Depends(oauth2_scheme)]) -> Token:
    token_data = db_man.get.token_db(token)
    if not token_data:
        raise HTTPException(status_code=401, detail='Fake token')
    token = Token(**token_data)
    return token


def authenticate_user(token: Annotated[Token, Depends(check_token)]) -> User:
    user_data = db_man.get.user_db(user_id=token.user_id)
    user = User(**user_data, token=token)

    if user.token.is_disabled:
        raise HTTPException(status_code=401, detail='Your token is disabled')

    return user

