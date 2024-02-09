from uuid import uuid4


def generate_token():
    return str(uuid4()) + '-' + str(uuid4())


def generate_name():
    return str(uuid4())

