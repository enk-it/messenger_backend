from typing import Annotated, Any
from fastapi import HTTPException, Depends
# from managers.db import get_token_db, get_user_by_user_id
from managers.db import manager as db_man
from models.models import User, Token
from fastapi.security import OAuth2PasswordBearer
# from fastapi import WebSocket
# from fastapi import WebSocketException

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


# def check_auth_scheme(request: WebSocket):
#     authorization = request.headers.get("Authorization")
#     try:
#         scheme, param = authorization.split(' ')
#     except Exception as e:
#         return WebSocketException(code=1008, reason='Auth failed. Check your Authorization header')
#
#     if not authorization or scheme.lower() != "bearer":
#         return WebSocketException(code=1008, reason='Auth failed. Check your Authorization Bearer header')
#
#     return param
#
#
# def check_token_ws(token: Annotated[Any, Depends(check_auth_scheme)]) -> Token:
#     token_data = get_token_db(token)
#     if not token_data:
#         raise WebSocketException(code=1008, reason='Fake token')
#     token = Token(**token_data)
#     return token
#
#
# def authenticate_user_ws(token: Annotated[Token, Depends(check_token_ws)]) -> User:
#     user_data = get_user_by_user_id(token.user_id)
#     user = User(**user_data, token=token)
#     return user
