try:
    import keyring
except (ImportError, NameError, RuntimeError):
    pass


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    keyring.set_password('yagmail', username, password)
