from yagmail.sender import SMTP
import sys

try:
    import keyring
except (ImportError, NameError, RuntimeError):
    pass


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    keyring.set_password("yagmail", username, password)


def main():
    """ This is the function that is run from commandline with `yagmail` """
    import argparse

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
    yag = SMTP(args.user, args.password)
    yag.send(to=args.to, subject=args.subject, contents=args.contents, attachments=args.attachments)
