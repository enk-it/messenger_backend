import typing

from models.models import WsUser, User, Token, ChatView
from models.response import WsNewMessage, WsNewChat
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from typing import List
# from managers.db import get_token_db, get_user_by_user_id, get_chat_participants, get_chat_db

from managers.db import manager as db_man

current_connections: List[WsUser] = []


async def connect(websocket: WebSocket):
    await websocket.accept()

    current_connections.append(WsUser(websocket=websocket))

    # print(current_connections, 'connected')


async def authenticate_ws(websocket: WebSocket, data):  # data='Bearer TOKEN'
    try:
        scheme, token = data.split(' ')
    except Exception as e:
        raise Exception('Auth failed. Check your Authorization data')

    if not data or scheme.lower() != "bearer":
        raise Exception('Auth failed. Check your Authorization data')

    token_data = db_man.get.token_db(token)
    if not token_data:
        raise Exception('Fake token')
    token = Token(**token_data)

    if token.is_disabled:
        raise Exception('Your token is disabled')

    user_data = db_man.get.user_db(user_id=token.user_id)
    user = User(**user_data, token=token)

    for connection in current_connections:
        if connection.websocket == websocket:
            connection.user = user
            connection.auth = True
            break

    # print(current_connections, 'authenticated')


def disconnect(websocket: WebSocket):
    global current_connections
    new_current_connections = []
    for connection in current_connections:
        if connection.websocket != websocket:
            new_current_connections.append(connection)
    current_connections = new_current_connections

    # print(current_connections, 'disconnected')


def get_user_ws(user_id) -> List[WsUser]:
    connections = []

    for connection in current_connections:
        if connection.user.token.user_id == user_id and connection.auth:
            connections.append(connection)

    return connections


def get_online_users() -> List[int]:
    users_id = set()
    for connection in current_connections:
        users_id.add(connection.user.token.user_id)
    return list(users_id)


async def notify_new_message(new_message, chat_participants):
    connections = []

    for participant in chat_participants:
        participant_wss = get_user_ws(participant)
        connections.extend(participant_wss)

    data = WsNewMessage(message=new_message)

    for connection in connections:

        data.message.incoming = data.message.user_id != connection.user.token.user_id

        await connection.websocket.send_text(data.model_dump_json())


async def notify_new_chat(new_chat):
    connections = []

    chat_participants = db_man.get.chat_participants(new_chat.chat_id)

    for participant in chat_participants:
        participant_wss = get_user_ws(participant)
        connections.extend(participant_wss)

    data = WsNewChat(chat=new_chat)

    for connection in connections:
        await connection.websocket.send_text(data.model_dump_json())

# async def send_personal_message(message: str, websocket: WebSocket):
#     await websocket.send_text(message)
#
#
# async def broadcast(message: str):
#     for connection in current_connections:
#         await connection.send_text(message)
