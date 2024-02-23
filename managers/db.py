import typing
import psycopg2
import psycopg2.extras
from typing import Any, List
import datetime


class Manager:
    def __init__(self):
        # self.connection = psycopg2.connect(user="silencer",
        #                                    password="swassswass",
        #                                    host="127.0.0.1",
        #                                    port="5432",
        #                                    dbname="messenger")

        self.connection = psycopg2.connect(user="jakiro",
                                           password="swass",
                                           host="192.168.0.17",
                                           port="5432",
                                           dbname="messenger")

        cursor = self.connection.cursor()
        print("Информация о сервере PostgreSQL")
        print(self.connection.get_dsn_parameters(), "\n")
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("Вы подключены к - ", record, "\n")

        self.get = Get(self.connection)
        self.exist = Exist(self.connection)
        self.create = Create(self.connection)
        self.update = Update(self.connection)


class Get():
    def __init__(self, connection):
        self.connection = connection

    def user_db(self, username: str = None, hashed_password: str = None, user_id: int = None) -> typing.Tuple:
        if user_id is None and (username is None and hashed_password is None):
            raise Exception('Bad Args')

        if (username is not None) and (hashed_password is not None) and (user_id is not None):
            raise Exception('Bad Args')

        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if user_id is not None:
            query = f"SELECT * FROM public.users WHERE user_id=%s"
            data = (user_id,)
        else:
            query = f"SELECT * FROM public.users WHERE username=%s and hashed_password=%s"
            data = (username, hashed_password)

        cursor.execute(query, data)
        result = cursor.fetchone()
        cursor.close()

        if result is None:
            return {}
        else:
            return dict(result)

    def users_db(self) -> typing.List:
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = f"SELECT * FROM public.users"

        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        if result is None:
            return []
        else:
            result = list(map(dict, result))
            return result

    def token_db(self, token: str) -> dict[Any, Any]:
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = f"SELECT * FROM public.tokens WHERE token='{token}'"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return {}
        else:
            return dict(result)

    def chats_db(self, user_id: int) -> List[Any]:
        """returns list with chats. Each chat contains filed messages, where each message contains fields: \n user_id,\n
                 chat_id,\n message_id,\n content,\n datetime,\n  is_read, \n  incoming. \nNeeds both chat_id and user_id
                 because different users can have different messages statuses (e.g. read/deleted) """
        cursor = self.connection.cursor()
        query = f"SELECT chat_id FROM public.party WHERE user_id={user_id}"
        cursor.execute(query)
        chat_ids = [i[0] for i in cursor.fetchall()]
        cursor.close()

        chats = []

        for chat_id in chat_ids:
            chat = self.chat_db(chat_id, user_id)
            chats.append(chat)

        return chats

    def chat_db(self, chat_id: int, user_id: int):
        """returns single chat. Chat contains filed messages, where each message contains fields: \n user_id,\n
         chat_id,\n message_id,\n content,\n datetime,\n  is_read, \n  incoming. \nNeeds both chat_id and user_id
         because different users can have different messages statuses (e.g. read/deleted) """
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = f"SELECT * FROM public.chats WHERE chat_id={chat_id}"
        cursor.execute(query)

        chat = dict(cursor.fetchone())
        cursor.close()

        messages = self.messages_db(user_id, chat_id)  # todo
        chat['messages'] = messages

        if chat['is_private']:
            chat['title'] = self.__interlocutor_username(chat_id, user_id)
            chat['avatar_url'] = self.__interlocutor_avatar_url(chat_id, user_id)

        return chat

    def messages_db(self, user_id: int, chat_id: int, oldest_message_id: int = -1) -> List[Any]:
        """returns list with messages, where each message contains fields: \n
        user_id, \n
        chat_id, \n
        message_id, \n
        content, \n
        datetime, \n
        is_read, \n
        incoming"""
        messages_cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # query = f"SELECT * FROM public.messages, public.statuses WHERE public.messages.chat_id={chat_id} AND public.statuses.is_deleted=false ORDER BY public.messages.message_id DESC"

        query = f"""SELECT public.messages.user_id, public.messages.message_id, public.messages.content, public.messages.datetime, is_read FROM public.messages, public.statuses WHERE 
public.messages.chat_id={chat_id} AND 
public.statuses.user_id={user_id} AND 
public.statuses.chat_id={chat_id} AND 
public.statuses.message_id=public.messages.message_id AND
public.statuses.is_deleted=false 
ORDER BY public.messages.message_id DESC;"""

        messages_cursor.execute(query)
        messages = []
        # statuses_cursor = self.connection.cursor()
        for message in messages_cursor.fetchall():
            message = dict(message)

            # query = f"SELECT is_read FROM public.statuses WHERE chat_id=%s AND user_id=%s and message_id=%s and is_deleted=%s"
            # data = (chat_id, user_id, message['message_id'], False)
            # statuses_cursor.execute(query, data)
            #
            # is_read = statuses_cursor.fetchone()[0]
            # message['is_read'] = is_read

            message['chat_id'] = chat_id

            message['incoming'] = message['user_id'] != user_id

            if (message['message_id'] < oldest_message_id) or (oldest_message_id == -1):
                messages.append(message)
            if len(messages) == 40:
                break

        # messages = [dict(message) for message in cursor.fetchall()]
        # print(messages)
        messages_cursor.close()
        # statuses_cursor.close()
        return messages

    def chat_participants(self, chat_id: int) -> List[Any]:
        """takes chat_id and returns list with that chat's participant's ids"""
        cursor = self.connection.cursor()
        query = f"SELECT user_id FROM public.party WHERE chat_id={chat_id}"

        cursor.execute(query)

        result = cursor.fetchall()

        cursor.close()

        if result is None:
            return []
        else:
            return [i[0] for i in result]

    def user_avatar_url(self, user_id: int) -> str:
        """returns avatar's url for current user"""

        cursor = self.connection.cursor()
        query = f"SELECT avatar_url FROM public.users WHERE user_id=%s;"

        data = (user_id,)

        cursor.execute(query, data)

        result = cursor.fetchone()[0]

        cursor.close()
        return result

    def __interlocutor_avatar_url(self, chat_id: int, user_id: int) -> str:
        """gets one's user_id and returns his interlocutor's username. Works only in private chats"""
        users = self.chat_participants(chat_id)
        if len(users) != 2:
            raise Exception('Critical Chat Error. Private chat doesnt have 2 users')
        users.remove(user_id)
        interlocutor_id = users[0]

        interlocutor = self.user_db(user_id=interlocutor_id)
        return interlocutor['avatar_url']

    def __interlocutor_username(self, chat_id: int, user_id: int) -> str:
        """gets one's user_id and returns his interlocutor's username. Works only in private chats"""
        users = self.chat_participants(chat_id)
        if len(users) != 2:
            raise Exception('Critical Chat Error. Private chat doenst have 2 users')
        users.remove(user_id)
        interlocutor_id = users[0]

        interlocutor = self.user_db(user_id=interlocutor_id)
        return interlocutor['username']


class Exist:
    def __init__(self, connection):
        self.connection = connection

    def user(self, user_id: int = None, username: str = None, email: str = None) -> bool:
        cursor = self.connection.cursor()

        if user_id is not None:
            query = f"SELECT * FROM public.users WHERE user_id={user_id}"
        elif username is not None:
            query = f"SELECT * FROM public.users WHERE username='{username}'"
        elif email is not None:
            query = f"SELECT * FROM public.users WHERE email='{email}'"

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()

        return result is not None

    def private_chat(self, user_1: int, user_2: int) -> bool:
        cursor = self.connection.cursor()

        query = "SELECT chat_id from public.party WHERE user_id=%s;"
        data = (user_1, )
        cursor.execute(query, data)
        user_1_chats = set(cursor.fetchall())
        if user_1_chats == set():
            return False

        query = f"SELECT chat_id from public.party WHERE user_id=%s;"
        data = (user_2, )
        cursor.execute(query, data)
        user_2_chats = set(cursor.fetchall())
        if user_2_chats == set():
            return False

        query = f"SELECT chat_id from public.chats WHERE is_private=%s;"
        data = (True, )
        cursor.execute(query, data)
        private_chats = set(cursor.fetchall())
        if private_chats == set():
            return False

        users_common_chats = user_1_chats.intersection(user_2_chats)
        if users_common_chats == set():
            return False

        users_private_chat = users_common_chats.intersection(private_chats)
        if users_private_chat == set():
            return False

        # if len(users_private_chat) > 1:
        #     raise Exception('More than one private chat for current users')

        return True


class Create:
    def __init__(self, connection):
        self.connection = connection

    def user(self, username: str, hashed_password: str) -> dict:
        """creates new user and returns new user's data"""
        cursor = self.connection.cursor()

        date = int(datetime.datetime.timestamp(datetime.datetime.now()))

        query = "INSERT INTO public.users (username, hashed_password, last_login) VALUES (%s, %s, %s) RETURNING user_id"

        data = (username, hashed_password, date)

        cursor.execute(query, data)
        user_id = cursor.fetchone()[0]
        cursor.close()
        self.connection.commit()

        result = {
            'user_id': user_id,
            'username': username,
            'last_login': date
        }

        return result

    def token(self, user_id: int, client_id: str, token: str) -> dict:
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = f"INSERT INTO public.tokens (token, user_id, client_id, is_disabled) VALUES (%s, %s, %s, %s)"
        data = (token, user_id, client_id, False)
        cursor.execute(query, data)
        self.connection.commit()
        cursor.close()

        result = {
            'token': token,
            'user_id': user_id,
            'client_id': client_id,
            'is_disabled': False
        }

        return result

    def message(self, user_id: int, chat_id: int, content: str, chat_participants: List) -> dict:
        time = int(datetime.datetime.timestamp(datetime.datetime.now()))

        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        message_id = self.__last_message_id(chat_id) + 1

        query = "INSERT INTO public.messages (message_id, chat_id, user_id, content, datetime) VALUES (%s, %s, %s, %s, %s)"
        data = (message_id, chat_id, user_id, content, time)
        cursor.execute(query, data)
        self.connection.commit()

        for chat_part_user_id in chat_participants:
            query = "INSERT INTO public.statuses (user_id, chat_id, message_id, is_deleted, is_read) VALUES (%s, %s, %s, %s, %s)"
            data = (chat_part_user_id, chat_id, message_id, False, False)
            cursor.execute(query, data)

        self.connection.commit()

        cursor.close()

        result = {'message_id': message_id, 'chat_id': chat_id, 'user_id': user_id, 'content': content,
                  'datetime': time, 'is_read': False}

        return result

    def chat(self, user_1: int, user_2: int) -> dict:
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        new_chat_id = self.__last_chat_id() + 1

        query = "INSERT INTO public.party (chat_id, user_id) VALUES (%s, %s);"

        data = (new_chat_id, user_1)
        cursor.execute(query, data)

        data = (new_chat_id, user_2)
        cursor.execute(query, data)

        query = "INSERT INTO public.chats (chat_id, title, is_private) VALUES (%s, %s, %s);"
        data = (new_chat_id, '', True)
        cursor.execute(query, data)
        self.connection.commit()
        cursor.close()

        result = {
            'chat_id': new_chat_id,
            'title': '',
            'is_private': True
        }

        return result

    def __last_message_id(self, chat_id: int) -> int:
        cursor = self.connection.cursor()

        query = f"SELECT message_id FROM public.messages WHERE chat_id={chat_id} ORDER BY message_id DESC fetch first 1 rows only;"

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return 0
        else:
            return result[0]

    def __last_chat_id(self) -> int:
        cursor = self.connection.cursor()

        query = f"SELECT chat_id FROM public.chats ORDER BY chat_id DESC fetch first 1 rows only;"

        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return 0
        else:
            return result[0]


class Update:
    def __init__(self, connection):
        self.connection = connection

    def user_avatar(self, user_id: int, file_name: str) -> None:
        cursor = self.connection.cursor()

        query = "UPDATE public.users SET avatar_url=%s WHERE user_id=%s;"

        data = (file_name, user_id)

        cursor.execute(query, data)
        cursor.close()
        self.connection.commit()

    def message_read(self, reader_id: int, chat_id: int, messages_ids: list, messages_owners_ids: list) -> None:
        cursor = self.connection.cursor()

        for message_id, owner_id in zip(messages_ids, messages_owners_ids):
            query = "UPDATE public.statuses SET is_read=%s WHERE user_id=%s AND chat_id=%s AND message_id=%s"
            data = (True, reader_id, chat_id, message_id)
            cursor.execute(query, data)
            data = (True, owner_id, chat_id, message_id)
            cursor.execute(query, data)

        cursor.close()
        self.connection.commit()


db_man = Manager()

if __name__ == '__main__':
    # print(manager.get.user_db(username='natures', hashed_password='swass'))
    print(db_man.get.user_avatar_url(user_id=210))

if __name__ == '__main__':
    # print(tuple(request.model_dump(mode='dicts').values()))
    # print(get_chats_data(23))
    # print(get_last_message_id(user_id=23, chat_id=4))
    # print(get_chat_participants(chat_id=4))
    # print(create_message(23, 4, 'test messag2', 1706190200))
    # print(private_chat_exist(23, 26))
    pass
