from yagmail.sender import SMTP
import sys

try:
    import keyring
except (ImportError, NameError, RuntimeError):
    pass


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    keyring.set_password('yagmail', username, password)


def main():
    """ This is the function that is run from commandline with `yagmail` """
    import argparse

    parser = argparse.ArgumentParser(description='Send a (g)mail with yagmail.')
    subparsers = parser.add_subparsers(dest="command")
    oauth = subparsers.add_parser('oauth')
    oauth.add_argument(
        '--user', '-u', required=True, help='The gmail username to register oauth2 for'
    )
    oauth.add_argument(
        '--file', '-f', required=True, help='The filepath to store the oauth2 credentials'
    )
    parser.add_argument('-to', '-t', help='Send an email to address "TO"', nargs='+')
    parser.add_argument('-subject', '-s', help='Subject of email', nargs='+')
    parser.add_argument('-contents', '-c', help='Contents to send', nargs='+')
    parser.add_argument('-attachments', '-a', help='Attachments to attach', nargs='+')
    parser.add_argument('-user', '-u', help='Username')
    parser.add_argument('-oauth2', '-o', help='OAuth2 file path')
    parser.add_argument(
        '-password', '-p', help='Preferable to use keyring rather than password here'
    )
    args = parser.parse_args()
    args.contents = (
        args.contents if args.contents else (sys.stdin.read() if not sys.stdin.isatty() else None)
    )
    if args.command == "oauth":
        user = args.user
        SMTP(args.user, oauth2_file=args.file)
        print("Succesful.")
    else:
        yag = SMTP(args.user, args.password, oauth2_file=args.oauth2)
        yag.send(
            to=args.to, subject=args.subject, contents=args.contents, attachments=args.attachments
        )
