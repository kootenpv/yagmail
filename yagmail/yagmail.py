import logging
import time
import os
import keyring
import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.encoders
import mimetypes

try:
    from .error import YagConnectionClosed
    from .error import YagAddressError
    from .error import YagInvalidEmailAddress
    from .validate import validate_email_with_regex
    from .log import get_logger
except (ValueError, SystemError):
    # stupid fix to make it easy to load interactively
    from error import YagConnectionClosed
    from error import YagAddressError
    from error import YagInvalidEmailAddress
    from validate import validate_email_with_regex
    from log import get_logger

try:
    import lxml.html
except ImportError:
    pass


class raw(str):

    """ Ensure that a string is treated as text
        and will not receive 'magic'. """
    pass


class inline(str):

    """ Only needed when wanting to inline an image
        rather than attach it """
    pass


class SMTP():

    """ Connection is the class that contains the SMTP connection
        and allows messages to be send """

    def __init__(self, user=None, password=None, host='smtp.gmail.com',
                 port='587', smtp_starttls=True, smtp_set_debuglevel=0,
                 **kwargs):
        self.log = get_logger()
        self.set_logging()
        if user is None:
            user = self._find_user_home_path()
        self.user, self.useralias = self._make_addr_alias_user(user)
        self.is_closed = None
        self.host = host
        self.port = port
        self.starttls = smtp_starttls
        self.debuglevel = smtp_set_debuglevel
        self.kwargs = kwargs
        self.login(password)
        self.cache = {}
        self.unsent = []
        self.log.info(
            'Connected to SMTP @ %s:%s as %s', self.host, self.port, self.user)
        self.num_mail_sent = 0

    def set_logging(self, log_level=logging.ERROR, file_path_name=None):
        """
        This function allows to change the logging backend, either output or file as backend
        It also allows to set the logging level (whether to display only critical, error, info or debug.
        e.g.
        yag = yagmail.SMTP()
        yag.set_logging(yagmail.logging.DEBUG)  # to see everything

        and

        yagmail.set_logging(yagmail.logging.DEBUG, 'somelocalfile.log')

        lastly, a log_level of None will make sure there is no I/O.
        """
        self.log = get_logger(log_level, file_path_name)

    def send(self, to=None, subject=None, contents=None, cc=None, bcc=None,
             preview_only=False, use_cache=False, validate_email=True,
             throw_invalid_exception=False,
             headers=None):
        """ Use this to send an email with gmail"""
        addresses = self._resolveAddresses(
            to, cc, bcc, validate_email, throw_invalid_exception)
        if not addresses['recipients']:
            return {}
        msg = self._prepare_message(
            addresses, subject, contents, use_cache, headers)

        if preview_only:
            return addresses, msg.as_string()
        return self._attempt_send(addresses['recipients'], msg.as_string())

    def _attempt_send(self, recipients, msg_string):
        attempts = 0
        while attempts < 3:
            try:
                result = self.smtp.sendmail(self.user, recipients, msg_string)
                self.log.info('Message sent to %s', recipients)
                self.num_mail_sent += 1
                return result
            except smtplib.SMTPServerDisconnected as e:
                self.log.error(e)
                attempts += 1
                time.sleep(attempts * 3)
        self.unsent.append((recipients, msg_string))
        return False

    def send_unsent(self):
        """
        Emails that were not being able to send will be stored in self.unsent.
        Use this function to attempt to send these again
        """
        for i in range(len(self.unsent)):
            recipients, msg_string = self.unsent.pop(i)
            self._attempt_send(recipients, msg_string)

    def close(self):
        """ Close the connection to the SMTP server """
        self.is_closed = True
        self.smtp.quit()
        self.log.info(
            'Closed SMTP @ %s:%s as %s', self.host, self.port, self.user)

    def handle_password(self, password):
        if password is None:
            password = keyring.get_password('yagmail', self.user)
            if password is None:
                password = keyring.get_password('yagmail', self.user)
            if password is None:
                import getpass
                password = getpass.getpass(
                    'Password for <{}>: '.format(self.user))
                answer = ''
                # Python 2 fix
                while answer != 'y' and answer != 'n':
                    prompt_string = 'Save username and password in keyring? [y/n]: '
                    # pylint: disable=undefined-variable
                    try:
                        answer = raw_input(prompt_string).strip()
                    except NameError:
                        answer = input(prompt_string).strip()
                if answer == 'y':
                    register(self.user, password)
        return password

    def login(self, password):
        """
        Login to the SMTP server using password.
        This only needs to be manually run when the connection to the SMTP server was closed by the user.
        """
        self.smtp = smtplib.SMTP(self.host, self.port, **self.kwargs)
        self.smtp.set_debuglevel(self.debuglevel)
        if self.starttls is not None:
            self.smtp.ehlo()
            if self.starttls:
                self.smtp.starttls()
            else:
                self.smtp.starttls(**self.starttls)
            self.smtp.ehlo()
        self.is_closed = False
        # skip login for test cases
        if 'py.test' == self.user or 'py.test' == password:
            return
        password = self.handle_password(password)
        self.smtp.login(self.user, password)

    def _resolveAddresses(self, to, cc, bcc, validate_email,
                          throw_invalid_exception):
        """ Handle the targets addresses, adding aliases when defined """
        addresses = {'recipients': []}
        if to is not None:
            self._make_addr_alias_target(to, addresses, 'To')
        elif cc is not None and bcc is not None:
            self._make_addr_alias_target(
                [self.user, self.useralias], addresses, 'To')
        else:
            addresses['recipients'].append(self.user)
        if cc is not None:
            self._make_addr_alias_target(cc, addresses, 'Cc')
        if bcc is not None:
            self._make_addr_alias_target(bcc, addresses, 'Bcc')
        if validate_email:
            for email_addr in addresses['recipients']:
                try:
                    validate_email_with_regex(email_addr)
                except YagInvalidEmailAddress as e:
                    if throw_invalid_exception:
                        raise e
                    else:
                        self.log.error(e)
                        addresses['recipients'].remove(email_addr)
        return addresses

    def _prepare_message(self, addresses, subject, contents,
                         use_cache, headers):
        """ Prepare a MIME message """
        if self.is_closed:
            raise YagConnectionClosed('Login required again')
        if isinstance(contents, str):
            contents = [contents]
        has_included_images, content_objects = self._prepare_contents(
            contents, use_cache)
        msg = MIMEMultipart()
        if headers is not None:
            # Strangely, msg does not have an update method, so then manually.
            for k, v in headers.items():
                msg[k] = v

        msg_alternative = MIMEMultipart('alternative')
        msg_related = MIMEMultipart('related')
        msg.attach(msg_alternative)
        self._add_subject(msg, subject)
        self._add_recipients(msg, addresses)
        htmlstr = ''
        altstr = []
        if has_included_images:
            msg.preamble = "This message is best displayed using a MIME capable email reader."
        if contents is not None:
            for content_object, content_string in zip(content_objects,
                                                      contents):
                if content_object['main_type'] == 'image':
                    # aliased image {'path' : 'alias'}
                    if (isinstance(content_string, dict) and
                            len(content_string) == 1):
                        for x in content_string:
                            hashed_ref = str(abs(hash(x)))
                            alias = content_string[x]
                        # pylint: disable=undefined-loop-variable
                        content_string = x
                    else:
                        alias = os.path.basename(content_string)
                        hashed_ref = str(abs(hash(alias)))

                    # if string is `inline`, inline, else, attach
                    # pylint: disable=unidiomatic-typecheck
                    if type(content_string) == inline:
                        htmlstr += '<img src="cid:{}" title="{}"/>'.format(
                            hashed_ref, alias)
                        content_object['mime_object'].add_header(
                            'Content-ID', '<{}>'.format(hashed_ref))
                        altstr.append(
                            '-- img {} should be here -- '.format(alias))

                if content_object['encoding'] == 'base64':
                    email.encoders.encode_base64(content_object['mime_object'])
                    msg.attach(content_object['mime_object'])
                else:
                    content_string = content_string.replace('\n', '<br>')
                    htmlstr += '<div>{}</div>'.format(content_string)
                    altstr.append(content_string)

        msg_related.attach(MIMEText(htmlstr, 'html'))
        msg_alternative.attach(MIMEText('\n'.join(altstr)))
        msg_alternative.attach(msg_related)
        return msg

    def _prepare_contents(self, contents, use_cache):
        mime_objects = []
        has_included_images = False
        if contents is not None:
            for content in contents:
                if use_cache:
                    if content not in self.cache:
                        content_object = self._get_mime_object(content)
                        self.cache[content] = content_object
                    content_object = self.cache[content]
                else:
                    content_object = self._get_mime_object(content)
                if content_object['main_type'] == 'image':
                    has_included_images = True
                mime_objects.append(content_object)
        return has_included_images, mime_objects

    def _add_recipients(self, msg, addresses):
        msg['From'] = '{} <{}>'.format(self.useralias, self.user)
        if 'To' in addresses:
            msg['To'] = addresses['To']
        else:
            msg['To'] = self.useralias
        if 'Cc' in addresses:
            msg['Cc'] = addresses['Cc']
        if 'Bcc' in addresses:
            msg['Bcc'] = addresses['Bcc']

    @staticmethod
    def _find_user_home_path():
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()

    @staticmethod
    def _make_addr_alias_user(x):
        if isinstance(x, str):
            if '@' not in x:
                x += '@gmail.com'
            return (x, x)
        if isinstance(x, dict):
            if len(x) == 1:
                return (list(x.keys())[0], list(x.values())[0])
        raise YagAddressError

    @staticmethod
    def _make_addr_alias_target(x, addresses, which):
        if isinstance(x, str):
            addresses['recipients'].append(x)
            addresses['To'] = x
            return addresses
        if isinstance(x, list) or isinstance(x, tuple):
            if not all([isinstance(k, str) for k in x]):
                raise YagAddressError
            addresses['recipients'].extend(x)
            addresses[which] = '; '.join(x)
            return addresses
        if isinstance(x, dict):
            addresses['recipients'].extend(x.keys())
            addresses[which] = '; '.join(x.values())
            return addresses
        raise YagAddressError

    @staticmethod
    def _add_subject(msg, Subject):
        if not Subject:
            return
        if isinstance(Subject, list):
            Subject = ' '.join(Subject)
        msg['Subject'] = Subject

    def _get_mime_object(self, content_string):
        content_object = {
            'mime_object': None,
            'encoding': None,
            'main_type': None,
            'sub_type': None
        }
        if isinstance(content_string, dict):
            for x in content_string:
                content_string, content_name = x, content_string[x]
        else:
            content_name = os.path.basename(content_string)

        # pylint: disable=unidiomatic-typecheck
        is_raw = type(content_string) == raw
        if os.path.isfile(content_string) and not is_raw:
            with open(content_string, 'rb') as f:
                content_object['encoding'] = 'base64'
                content = f.read()
        else:
            content_object['main_type'] = 'text'
            try:
                if not is_raw:
                    html_tree = lxml.html.fromstring(content_string)
                    if (html_tree.find('.//*') is not None or
                            html_tree.tag != 'p'):
                        content_object['mime_object'] = MIMEText(
                            content_string, 'html')
                        content_object['sub_type'] = 'html'
                if content_object['mime_object'] is None:
                    content_object['mime_object'] = MIMEText(content_string)
            except NameError:
                self.log.error(
                    "Sending as text email since `lxml` is not installed")
                content_object['mime_object'] = MIMEText(content_string)
            if content_object['sub_type'] is None:
                content_object['sub_type'] = 'plain'
            return content_object

        if content_object['main_type'] is None:
            content_type, _ = mimetypes.guess_type(content_string)

            if content_type is not None:
                content_object['main_type'], content_object[
                    'sub_type'] = content_type.split('/')

        if (content_object['main_type'] is None or
                content_object['encoding'] is not None):
            if content_object['encoding'] != 'base64':
                content_object['main_type'] = 'application'
                content_object['sub_type'] = 'octet-stream'

        mime_object = MIMEBase(
            content_object['main_type'], content_object['sub_type'],
            name=content_name)
        mime_object.set_payload(content)
        content_object['mime_object'] = mime_object
        return content_object

    def feedback(self,
                 message="Awesome features! You made my day! How can I contribute? Winter is coming."):
        """ Most important function. Please send me feedback :-) """
        self.send('kootenpv@gmail.com', 'Yagmail feedback', message)


class SMTP_SSL(SMTP):

    def login(self, password):
        if self.port == '587':
            self.port = '465'
        self.smtp = smtplib.SMTP_SSL(self.host, self.port, **self.kwargs)
        self.smtp.set_debuglevel(self.debuglevel)
        password = self.handle_password(password)
        self.smtp.login(self.user, password)
        self.is_closed = False


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring
         so it can be used in yagmail
    """
    keyring.set_password('yagmail', username, password)


def main():
    """ This is the function that is run from commandline with `yagmail` """
    import argparse
    parser = argparse.ArgumentParser(
        description='Send a (g)mail with yagmail.')
    parser.add_argument(
        '-to', '-t', help='Send an email to address "TO"', nargs='+')
    parser.add_argument('-subject', '-s', help='Subject of email', nargs='+')
    parser.add_argument('-contents', '-c', help='Contents to send', nargs='+')
    parser.add_argument('-user', '-u', help='Username')
    parser.add_argument(
        '-password', '-p',
        help='Preferable to use keyring rather than password here')
    args = parser.parse_args()
    SMTP(args.user, args.password).send(
        to=args.to, subject=args.subject, contents=args.contents)
