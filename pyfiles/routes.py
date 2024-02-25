from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile
from fastapi.responses import FileResponse

from managers.db import db_man as db
from managers.ws import ws_man
from managers.auth import authenticate_user

from models.requests import RegisterData, LoginData, SendData, ReadData
from models.response import ResponseBearerToken, ResponseChats, ResponseMessages, ResponseUsers
from models.models import User, Token, WsUser, Message, ChatView, PublicUser, JPEGImage

from pyfiles.utils import generate_name, generate_token
from typing import Annotated
from PIL import Image
import io
import os

router = APIRouter()


@router.get("/api/share/avatar/{url}")
async def get_avatar(url: str) -> FileResponse:
    if url not in os.listdir('./share/'):
        # raise HTTPException(status_code=404, detail='No image with this url exists')
        url = 'avatar.png'
    response = FileResponse('./share/' + url)
    return response


@router.post("/api/set_avatar/")
async def set_avatar(file: UploadFile, user: Annotated[User, Depends(authenticate_user)]):
    image = JPEGImage(file=file)
    contents = await image.file.read()
    pil_image = Image.open(io.BytesIO(contents))
    try:
        Image.open(io.BytesIO(contents)).verify()
    except Exception as e:
        raise HTTPException(status_code=400, detail='Bad File Error. Check if your file broken and try again later.')

    filename = generate_name() + '.jpg'
    pil_image.save('./share/' + filename)
    db.update.user_avatar(user_id=user.token.user_id, avatar=filename)

    return {'ok': True, 'filename': filename}


@router.post("/api/login/")
async def login(request: LoginData) -> ResponseBearerToken:
    if not db.exist.user(username=request.username):
        raise HTTPException(status_code=400, detail='User with this username does not exists.')
    try:
        user = User(**db.get.user_db(request.username, request.hashed_password))
    except Exception as e:
        raise HTTPException(status_code=400, detail='Wrong password.')
    token_db = db.create.token(user.user_id, request.client_id, generate_token())
    bearer_token = ResponseBearerToken(**token_db)

    return bearer_token  # {"token": bearer_token}


@router.post("/api/register/")
async def register(request: RegisterData) -> ResponseBearerToken:
    if db.exist.user(username=request.username):
        raise HTTPException(status_code=400, detail='User with this username already exists.')
    user_db = db.create.user(request.username, request.hashed_password)
    user = PublicUser(**user_db)

    token_db = db.create.token(user.user_id, request.client_id, generate_token())
    bearer_token = ResponseBearerToken(**token_db)

    return bearer_token


@router.get("/api/get_chats/")
async def get_chats(user: Annotated[User, Depends(authenticate_user)]) -> ResponseChats:
    return ResponseChats(chats=db.get.chats_db(user_id=user.token.user_id))


@router.get("/api/get_users/")
async def get_users(user: Annotated[User, Depends(authenticate_user)]) -> ResponseUsers:
    users_data = db.get.users_db()
    online_users = ws_man.get.online_users()

    response = ResponseUsers(users=users_data)

    for online_user in online_users:
        for user in response.users:
            if user.user_id == online_user:
                user.is_online = True

    return response
    # return ResponseUsers(chats=get_chats_db(user_id=user.token.user_id))


@router.get("/api/get_messages/")
async def get_messages(user: Annotated[User, Depends(authenticate_user)], chat_id: int,
                       oldest_message_id: int = -1) -> ResponseMessages:
    messages = db.get.messages_db(user_id=user.token.user_id, chat_id=chat_id, oldest_message_id=oldest_message_id)
    response = ResponseMessages(messages=messages)

    return response


# todo message editing.
# todo message deleting.


@router.post("/api/send_message/")
async def send_message(request: SendData, user: Annotated[User, Depends(authenticate_user)]):
    if not request.content:
        raise HTTPException(status_code=400, detail="Empty messages are not allowed")

    chat_participants = db.get.chat_participants(request.chat_id)
    if user.token.user_id not in chat_participants:
        raise HTTPException(status_code=403, detail='You have no access in this chat')

    message_db = db.create.message(user.token.user_id, request.chat_id, request.content, chat_participants)

    new_message = Message(**message_db)

    await ws_man.notify.new_message(new_message, chat_participants)

    return {'ok': True}


@router.post("/api/read_message/")
async def read_message(request: ReadData, user: Annotated[User, Depends(authenticate_user)]):
    # rework to list usage
    chat_participants = db.get.chat_participants(request.chat_id)
    if user.token.user_id not in chat_participants:
        raise HTTPException(status_code=403, detail='You have no access in this chat')

    db.update.message_read(user.token.user_id, request.chat_id, request.messages_ids, request.users_ids)

    await ws_man.notify.message_read(user.token.user_id, request.chat_id, request.messages_ids, request.users_ids)

    return {'ok': True}


@router.get("/api/start_chat/")
async def start_chat(user_id: int, user: Annotated[User, Depends(authenticate_user)]):
    user_1 = user_id
    user_2 = user.user_id

    if user_1 == user_2:
        raise HTTPException(status_code=400, detail="You cannot start chat with yourself")

    if not db.exist.user(user_1):
        raise HTTPException(status_code=400, detail='This user doesnt exist')

    if db.exist.private_chat(user_1, user_2):
        raise HTTPException(status_code=400, detail='This chat already exist')

    chat_db = db.create.chat(user_id, user.token.user_id)

    chat = ChatView(**chat_db)

    await ws_man.notify.new_chat(chat)

    return {'ok': True}


@router.websocket("/api_ws/websocket_connection/")
async def websocket_endpoint(websocket: WebSocket) -> None:  # , user: Annotated[User, Depends(authenticate_user_ws)]
    # print(user)
    await ws_man.connect(websocket)
    try:
        await websocket.send_text('{"info":"Provide your Bearer token"}')
        data = await websocket.receive_text()

        await ws_man.authenticate_ws(websocket, data)

        await websocket.send_text('{"info":"Auth succeeded"}')
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print('disconnected')
        ws_man.disconnect(websocket)
        await websocket.close()
    except Exception as e:
        await websocket.send_text('{"error":{error}}'.format(error=e))
        ws_man.disconnect(websocket)
        await websocket.close()
