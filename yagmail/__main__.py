import argparse

from yagmail.sender import Client

try:
    import keyring
except (ImportError, NameError, RuntimeError):
    keyring = None  # type: ignore


def register(username: str, password: str) -> None:
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    if keyring is None:
        raise ImportError("keyring package is not installed.")
    keyring.set_password("yagmail", username, password)


def main() -> None:
    """ This is the function that is run from commandline with `yagmail` """
    parser = argparse.ArgumentParser(description="Send a (g)mail with yagmail.")
    parser.add_argument("-to", "-t", help='Send an email to address "TO"', nargs="+")
    parser.add_argument("-subject", "-s", help="Subject of email", nargs="+")
    parser.add_argument("-contents", "-c", help="Contents to send", nargs="+")
    parser.add_argument("-attachments", "-a", help="Attachments to attach", nargs="+")
    parser.add_argument("-user", "-u", help="Username")
    parser.add_argument(
        "-password", "-p", help="Preferable to use keyring rather than password here"
    )
    args = parser.parse_args()
    if args.to is None:
        parser.print_help()
        return
    yag = Client(args.user, args.password)

    yag.send(to=args.to, subject=args.subject, contents=args.contents, attachments=args.attachments)
