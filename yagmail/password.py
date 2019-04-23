try:
    import keyring
except (ImportError, NameError, RuntimeError):
    pass


def handle_password(user, password):  # pragma: no cover
    """ Handles getting the password"""
    if password is None:
        try:
            password = keyring.get_password("yagmail", user)
        except NameError as e:
            print(
                "'keyring' cannot be loaded. Try 'pip install keyring' or continue without. See https://github.com/kootenpv/yagmail"
            )
            raise e
        if password is None:
            import getpass

            password = getpass.getpass("Password for <{0}>: ".format(user))
            answer = ""
            # Python 2 fix
            while answer != "y" and answer != "n":
                prompt_string = "Save username and password in keyring? [y/n]: "
                # pylint: disable=undefined-variable
                try:
                    answer = raw_input(prompt_string).strip()
                except NameError:
                    answer = input(prompt_string).strip()
            if answer == "y":
                register(user, password)
    return password


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    keyring.set_password("yagmail", username, password)
