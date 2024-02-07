from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends

from fastapi.responses import FileResponse

from managers.db import manager as db_man

from managers.ws import connect, disconnect, authenticate_ws
from managers.ws import get_online_users
from managers.ws import notify_new_message, notify_new_chat

from managers.auth import authenticate_user

from models.requests import RegisterData, LoginData, SendData
from models.response import ResponseBearerToken, ResponseChats, ResponseMessages, ResponseUsers
from models.models import User, Token, WsUser, Message, ChatView, PublicUser

import datetime
from typing import Annotated

router = APIRouter()


@router.get("/share/avatar/{url}")
async def get_avatar(url: str) -> FileResponse:
    return FileResponse('./share/' + url)



@router.post("/login/")
async def login(request: LoginData) -> ResponseBearerToken:
    user = User(**db_man.get.user_db(request.username, request.hashed_password))
    token_db = db_man.create.token(user.user_id, request.client_id)
    bearer_token = ResponseBearerToken(**token_db)

    return bearer_token  # {"token": bearer_token}


@router.post("/register/")
async def register(request: RegisterData) -> ResponseBearerToken:
    user_db = db_man.create.user(request.username, request.hashed_password)
    user = PublicUser(**user_db)
    token_db = db_man.create.token(user.user_id, request.client_id)
    bearer_token = ResponseBearerToken(**token_db)

    return bearer_token


@router.get("/get_chats/")
async def get_chats(user: Annotated[User, Depends(authenticate_user)]) -> ResponseChats:
    return ResponseChats(chats=db_man.get.chats_db(user_id=user.token.user_id))


@router.get("/get_users/")
async def get_users(user: Annotated[User, Depends(authenticate_user)]) -> ResponseUsers:
    users_data = db_man.get.users_db()
    online_users = get_online_users()

    response = ResponseUsers(users=users_data)

    for online_user in online_users:
        for user in response.users:
            if user.user_id == online_user:
                user.is_online = True

    print(users_data)

    return response
    # return ResponseUsers(chats=get_chats_db(user_id=user.token.user_id))


@router.get("/get_messages/")
async def get_messages(user: Annotated[User, Depends(authenticate_user)], chat_id: int,
                       oldest_message_id: int = -1) -> ResponseMessages:
    messages = db_man.get.messages_db(user_id=user.token.user_id, chat_id=chat_id, oldest_message_id=oldest_message_id)
    response = ResponseMessages(messages=messages)

    return response


@router.post("/send_message/")
async def send_message(request: SendData, user: Annotated[User, Depends(authenticate_user)]):
    if not request.content:
        raise HTTPException(status_code=400, detail="Empty messages are not allowed")

    chat_participants = db_man.get.chat_participants(request.chat_id)
    if user.token.user_id not in chat_participants:
        raise HTTPException(status_code=403, detail='You have no access in this chat')

    time = int(datetime.datetime.timestamp(datetime.datetime.now()))  # current time in timestamp

    message_db = db_man.create.message(user.token.user_id, request.chat_id, request.content, time, chat_participants)

    new_message = Message(**message_db)

    await notify_new_message(new_message, chat_participants)

    return {'ok': True}


@router.get("/start_chat/")
async def start_chat(user_id: int, user: Annotated[User, Depends(authenticate_user)]):
    user_1 = user_id
    user_2 = user.user_id

    if not db_man.exist.user(user_1):
        raise HTTPException(status_code=400, detail='This user doesnt exist')

    if db_man.exist.private_chat(user_1, user_2):
        raise HTTPException(status_code=400, detail='This chat already exist')

    chat_db = db_man.create.chat(user_id, user.token.user_id)

    chat = ChatView(**chat_db)

    await notify_new_chat(chat)

    return {'ok': True}


# todo get_usernames()
# todo along with registration and login you should give userId so that Client be able to verify
# whether some message his or not

@router.websocket("/websocket_connection/")
async def websocket_endpoint(websocket: WebSocket) -> None:  # , user: Annotated[User, Depends(authenticate_user_ws)]
    # print(user)
    await connect(websocket)
    try:
        await websocket.send_text('{"info":"Provide your Bearer token"}')
        data = await websocket.receive_text()

        await authenticate_ws(websocket, data)

        await websocket.send_text('{"info":"Auth succeeded"}')
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(websocket)
    except Exception as e:
        await websocket.send_text('{"error":{error}}'.format(error=e))
        disconnect(websocket)
        await websocket.close()
