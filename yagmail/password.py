from typing import Optional

try:
    import keyring
except (ImportError, NameError, RuntimeError):
    keyring = None  # type: ignore


def handle_password(user: str, password: Optional[str]) -> str:  # pragma: no cover
    """ Handles getting the password"""
    if password is None:
        try:
            if keyring is None:
                raise NameError("keyring is not imported")
            password = keyring.get_password("yagmail", user)
        except NameError as e:
            print(
                "'keyring' cannot be loaded. Try 'pip install keyring' or continue without. See https://github.com/kootenpv/yagmail"
            )
            raise e
        if password is None:
            import getpass

            password = getpass.getpass(f"Password for <{user}>: ")
            answer = ""
            while answer != "y" and answer != "n":
                prompt_string = "Save username and password in keyring? [y/n]: "
                answer = input(prompt_string).strip()
            if answer == "y":
                register(user, password)
    return password


def register(username: str, password: str) -> None:
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    if keyring is None:
        raise ImportError("keyring package is not installed.")
    keyring.set_password("yagmail", username, password)
