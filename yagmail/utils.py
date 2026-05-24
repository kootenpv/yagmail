import os
from typing import Optional


class raw(str):
    """ Ensure that a string is treated as text and will not receive 'magic'. """

    pass


class inline(str):
    """ Only needed when wanting to inline an image rather than attach it """

    pass


def find_user_home_path() -> Optional[str]:
    path = os.path.expanduser("~/.yagmail")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read().strip()
