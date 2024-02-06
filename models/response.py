from pydantic import BaseModel, Field
from models.models import ChatView, Message, PublicUser
from typing import List


class ResponseBearerToken(BaseModel):
    token: str = Field(description='Token that is used to auth')
    user_id: int
    client_id: str


class ResponseChats(BaseModel):
    chats: List[ChatView]


class ResponseMessages(BaseModel):
    messages: List[Message]


class ResponseUsers(BaseModel):
    users: List[PublicUser]


class WsNewMessage(BaseModel):
    info: str = 'newMessage'
    message: Message


class WsNewChat(BaseModel):
    info: str = 'newChat'
    chat: ChatView

