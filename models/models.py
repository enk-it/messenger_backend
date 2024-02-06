import json

from pydantic import BaseModel, EmailStr, model_validator, Field, ConfigDict
from fastapi import WebSocket
from managers.db import manager as db_man
from typing import List


class Token(BaseModel):
    token: str
    user_id: int
    is_disabled: bool
    client_id: str


class PublicUser(BaseModel):
    username: str = Field(min_length=6, max_length=24)
    last_login: int | None = None
    user_id: int
    is_online: bool | None = None


class User(PublicUser):
    hashed_password: str
    token: Token | None = None

    @model_validator(mode='after')
    def check_username(self) -> 'User':
        username = self.username
        if not username:
            raise ValueError('Username can not be empty')
        if ' ' in username or '\n' in username:
            raise ValueError('Username can not contain whitespaces')
        if not db_man.exist.user(username=username):
            raise ValueError('No user found with this credentials')
        return self


class Message(BaseModel):
    message_id: int
    chat_id: int
    user_id: int
    content: str
    datetime: int

    incoming: bool | None = None

    is_read: bool


class ChatView(BaseModel):
    chat_id: int
    title: str | None = None
    is_private: bool

    messages: List[Message] | None = None


class WsUser(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user: User | None = None
    websocket: WebSocket
    auth: bool = False


if __name__ == '__main__':
    db_data = db_man.get.user_db("userNumberOne", "hashpasswd")

    asdUser = User(**db_data)

    print(asdUser)
