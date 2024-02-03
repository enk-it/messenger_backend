from uuid import uuid4


def generate_token():
    return str(uuid4()) + '-' + str(uuid4())


# print(generate_token())
