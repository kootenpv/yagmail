import os


class raw(str):
    """ Ensure that a string is treated as text and will not receive 'magic'. """

    pass


class inline(str):
    """ Only needed when wanting to inline an image rather than attach it """

    pass


def find_user_home_path():
    with open(os.path.expanduser("~/.yagmail")) as f:
        return f.read().strip()
