from models.models import WsUser, User, Token
from models.response import WsNewMessage, WsNewChat
from fastapi import WebSocket
from typing import List
from managers.db import db_man


def _get_user_ws(user_id, current_connections) -> List[WsUser]:
    connections = []

    for connection in current_connections:
        if connection.user.token.user_id == user_id and connection.auth:
            connections.append(connection)

    return connections


def _get_online_users(current_connections) -> List[int]:
    users_id = set()
    for connection in current_connections:
        users_id.add(connection.user.token.user_id)
    return list(users_id)


class Notify:
    def __init__(self, current_connections):
        self.current_connections = current_connections

    async def new_message(self, new_message, chat_participants):
        connections = []

        for participant in chat_participants:
            participant_wss = _get_user_ws(participant, self.current_connections)
            connections.extend(participant_wss)

        data = WsNewMessage(message=new_message)

        for connection in connections:
            data.message.incoming = data.message.user_id != connection.user.token.user_id

            await connection.websocket.send_text(data.model_dump_json())

    async def new_chat(self, new_chat):
        connections = []

        chat_participants = db_man.get.chat_participants(new_chat.chat_id)

        for participant in chat_participants:
            participant_wss = _get_user_ws(participant, self.current_connections)
            connections.extend(participant_wss)

        for connection in connections:
            data = WsNewChat(chat=db_man.get.chat_db(new_chat.chat_id, connection.user.user_id))
            await connection.websocket.send_text(data.model_dump_json())


class Get:
    def __init__(self, current_connections):
        self.current_connections = current_connections

    def online_users(self):
        return _get_online_users(self.current_connections)


class Manager:
    def __init__(self):
        self.current_connections: List[WsUser] = []

        self.notify = Notify(self.current_connections)
        self.get = Get(self.current_connections)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        self.current_connections.append(WsUser(websocket=websocket))

    async def authenticate_ws(self, websocket: WebSocket, data):  # data='Bearer TOKEN'
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

        for connection in self.current_connections:
            if connection.websocket == websocket:
                connection.user = user
                connection.auth = True
                break

    def disconnect(self, websocket: WebSocket):
        new_current_connections = []
        for connection in self.current_connections:
            if connection.websocket != websocket:
                new_current_connections.append(connection)
        self.current_connections = new_current_connections


ws_man = Manager()
