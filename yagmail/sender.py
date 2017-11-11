# when there is a bcc a different message has to be sent to the bcc
# person, to show that they are bcc'ed

import os
import sys
import time
import logging
import mimetypes
import smtplib
import email.encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


from yagmail.error import YagConnectionClosed
from yagmail.error import YagAddressError
from yagmail.validate import validate_email_with_regex
from yagmail.log import get_logger
from yagmail.oauth2 import get_oauth2_info, get_oauth_string

try:
    import keyring
except (ImportError, NameError, RuntimeError):
    pass


PY3 = sys.version_info[0] == 3
text_type = (str,) if PY3 else (str, unicode)


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail """
    keyring.set_password('yagmail', username, password)


class raw(str):
    """ Ensure that a string is treated as text and will not receive 'magic'. """
    pass


class inline(str):
    """ Only needed when wanting to inline an image rather than attach it """
    pass


class SMTP():
    """ :class:`yagmail.SMTP` is a magic wrapper around
    ``smtplib``'s SMTP connection, and allows messages to be sent."""

    def __init__(self, user=None, password=None, host='smtp.gmail.com', port=None,
                 smtp_starttls=None, smtp_ssl=True, smtp_set_debuglevel=0,
                 smtp_skip_login=False, encoding="utf-8", oauth2_file=None,
                 soft_email_validation=True, **kwargs):
        self.log = get_logger()
        self.set_logging()
        if smtp_skip_login and user is None:
            user = ''
        elif user is None:
            user = self._find_user_home_path()
        self.user, self.useralias = self._make_addr_alias_user(user)
        self.soft_email_validation = soft_email_validation
        if soft_email_validation:
            validate_email_with_regex(self.user)
        self.is_closed = None
        self.host = host
        self.port = str(port) if port is not None else '465' if smtp_ssl else '587'
        self.smtp_starttls = smtp_starttls
        self.ssl = smtp_ssl
        self.smtp_skip_login = smtp_skip_login
        self.debuglevel = smtp_set_debuglevel
        self.encoding = encoding
        self.kwargs = kwargs
        if oauth2_file is not None:
            self.login_oauth2(oauth2_file)
        else:
            self.login(password)
        self.cache = {}
        self.unsent = []
        self.log.info('Connected to SMTP @ %s:%s as %s', self.host, self.port, self.user)
        self.num_mail_sent = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_closed:
            self.close()
        return False

    @property
    def connection(self):
        return smtplib.SMTP_SSL if self.ssl else smtplib.SMTP

    @property
    def starttls(self):
        if self.smtp_starttls is None:
            return False if self.ssl else True
        return self.smtp_starttls

    def set_logging(self, log_level=logging.ERROR, file_path_name=None):
        """
        This function allows to change the logging backend, either output or file as backend
        It also allows to set the logging level (whether to display only critical/error/info/debug.
        for example::

            yag = yagmail.SMTP()
            yag.set_logging(yagmail.logging.DEBUG)  # to see everything

        and::

            yagmail.set_logging(yagmail.logging.DEBUG, 'somelocalfile.log')

        lastly, a log_level of :py:class:`None` will make sure there is no I/O.
        """
        self.log = get_logger(log_level, file_path_name)

    def send(self, to=None, subject=None, contents=None, attachments=None, cc=None, bcc=None,
             preview_only=False, headers=None):
        """ Use this to send an email with gmail"""
        addresses = self._resolve_addresses(to, cc, bcc)
        if not addresses['recipients']:
            return {}
        msg = self._prepare_message(addresses, subject, contents, attachments, headers)

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
        Emails that were not being able to send will be stored in :attr:`self.unsent`.
        Use this function to attempt to send these again
        """
        for i in range(len(self.unsent)):
            recipients, msg_string = self.unsent.pop(i)
            self._attempt_send(recipients, msg_string)

    def close(self):
        """ Close the connection to the SMTP server """
        self.is_closed = True
        try:
            self.smtp.quit()
        except (TypeError, AttributeError, smtplib.SMTPServerDisconnected):
            pass

    def _handle_password(self, password):
        """ Handles getting the password"""
        if password is None:
            try:
                password = keyring.get_password('yagmail', self.user)
            except NameError as e:
                print("'keyring' cannot be loaded. Try 'pip install keyring' or continue without. See https://github.com/kootenpv/yagmail")
                raise e
            if password is None:
                import getpass
                password = getpass.getpass(
                    'Password for <{0}>: '.format(self.user))
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
        Login to the SMTP server using password. `login` only needs to be manually run when the
        connection to the SMTP server was closed by the user.
        """
        self.smtp = self.connection(self.host, self.port, **self.kwargs)
        self.smtp.set_debuglevel(self.debuglevel)
        if self.starttls:
            self.smtp.ehlo()
            if self.starttls is True:
                self.smtp.starttls()
            else:
                self.smtp.starttls(**self.starttls)
            self.smtp.ehlo()
        self.is_closed = False
        if not self.smtp_skip_login:
            password = self._handle_password(password)
            self.smtp.login(self.user, password)

    def login_oauth2(self, oauth2_file):
        self.smtp = self.connection(self.host, self.port, **self.kwargs)
        self.smtp.set_debuglevel(self.debuglevel)
        oauth2_info = get_oauth2_info(oauth2_file)
        auth_string = get_oauth_string(self.user, oauth2_info)
        self.smtp.ehlo(oauth2_info["google_client_id"])
        if self.starttls is True:
            self.smtp.starttls()
        self.smtp.docmd('AUTH', 'XOAUTH2 ' + auth_string)

    def _resolve_addresses(self, to, cc, bcc):
        """ Handle the targets addresses, adding aliases when defined """
        addresses = {'recipients': []}
        if to is not None:
            self._make_addr_alias_target(to, addresses, 'To')
        elif cc is not None and bcc is not None:
            self._make_addr_alias_target([self.user, self.useralias], addresses, 'To')
        else:
            addresses['recipients'].append(self.user)
        if cc is not None:
            self._make_addr_alias_target(cc, addresses, 'Cc')
        if bcc is not None:
            self._make_addr_alias_target(bcc, addresses, 'Bcc')
        if self.soft_email_validation:
            for email_addr in addresses['recipients']:
                validate_email_with_regex(email_addr)
        return addresses

    def _prepare_message(self, addresses, subject, contents, attachments, headers):
        """ Prepare a MIME message """
        if self.is_closed:
            raise YagConnectionClosed('Login required again')
        if isinstance(contents, text_type):
            contents = [contents]
        if isinstance(attachments, text_type):
            attachments = [attachments]

        # merge contents and attachments for now.
        if attachments is not None:
            for a in attachments:
                if not os.path.isfile(a):
                    raise TypeError("'{0}' is not a valid filepath".format(a))
            contents = attachments if contents is None else contents + attachments

        has_included_images, content_objects = self._prepare_contents(contents)
        msg = MIMEMultipart()
        if headers is not None:
            # Strangely, msg does not have an update method, so then manually.
            for k, v in headers.items():
                msg[k] = v
        if headers is None or not "Date" in headers:
            msg["Date"] = formatdate()

        msg_alternative = MIMEMultipart('alternative')
        msg_related = MIMEMultipart('related')
        msg_related.attach("-- HTML goes here --")
        msg.attach(msg_alternative)
        self._add_subject(msg, subject)
        self._add_recipients_headers(msg, addresses)
        htmlstr = ''
        altstr = []
        if has_included_images:
            msg.preamble = "This message is best displayed using a MIME capable email reader."

        if contents is not None:
            for content_object, content_string in zip(content_objects,
                                                      contents):
                if content_object['main_type'] == 'image':
                    # all image objects need base64 encoding, so do it now
                    email.encoders.encode_base64(content_object['mime_object'])
                    # aliased image {'path' : 'alias'}
                    if isinstance(content_string, dict) and len(content_string) == 1:
                        for key in content_string:
                            hashed_ref = str(abs(hash(key)))
                            alias = content_string[key]
                        # pylint: disable=undefined-loop-variable
                        content_string = key
                    else:
                        alias = os.path.basename(str(content_string))
                        hashed_ref = str(abs(hash(alias)))

                    # TODO: I should probably remove inline now that there is "attachments"
                    # if string is `inline`, inline, else, attach
                    # pylint: disable=unidiomatic-typecheck
                    if type(content_string) == inline:
                        htmlstr += '<img src="cid:{0}" title="{1}"/>'.format(hashed_ref, alias)
                        content_object['mime_object'].add_header(
                            'Content-ID', '<{0}>'.format(hashed_ref))
                        altstr.append('-- img {0} should be here -- '.format(alias))
                        # inline images should be in related MIME block
                        msg_related.attach(content_object['mime_object'])
                    else:
                        # non-inline images get attached like any other attachment
                        msg.attach(content_object['mime_object'])

                else:
                    if content_object['encoding'] == 'base64':
                        email.encoders.encode_base64(content_object['mime_object'])
                        msg.attach(content_object['mime_object'])
                    elif content_object['sub_type'] not in ["html", "plain"]:
                        msg.attach(content_object['mime_object'])
                    else:
                        content_string = content_string.replace('\n', '<br>')
                        try:
                            htmlstr += '<div>{0}</div>'.format(content_string)
                        except UnicodeEncodeError:
                            htmlstr += u'<div>{0}</div>'.format(content_string)
                        altstr.append(content_string)

        msg_related.get_payload()[0] = MIMEText(htmlstr, 'html', _charset=self.encoding)
        msg_alternative.attach(MIMEText('\n'.join(altstr), _charset=self.encoding))
        msg_alternative.attach(msg_related)
        return msg

    def _prepare_contents(self, contents):
        mime_objects = []
        has_included_images = False
        if contents is not None:
            for content in contents:
                content_object = self._get_mime_object(content)
                if content_object['main_type'] == 'image':
                    has_included_images = True
                mime_objects.append(content_object)
        return has_included_images, mime_objects

    def _add_recipients_headers(self, msg, addresses):
        # Quoting the useralias so it should match display-name from https://tools.ietf.org/html/rfc5322 ,
        # even if it's an email address.
        msg['From'] = '"{0}" <{1}>'.format(self.useralias.replace(
            '\\', '\\\\').replace('"', '\\"'), self.user)
        if 'To' in addresses:
            msg['To'] = addresses['To']
        else:
            msg['To'] = self.useralias
        if 'Cc' in addresses:
            msg['Cc'] = addresses['Cc']

    @staticmethod
    def _find_user_home_path():
        with open(os.path.expanduser("~/.yagmail")) as f:
            return f.read().strip()

    @staticmethod
    def _make_addr_alias_user(email_addr):
        if isinstance(email_addr, text_type):
            if '@' not in email_addr:
                email_addr += '@gmail.com'
            return (email_addr, email_addr)
        if isinstance(email_addr, dict):
            if len(email_addr) == 1:
                return (list(email_addr.keys())[0], list(email_addr.values())[0])
        raise YagAddressError

    @staticmethod
    def _make_addr_alias_target(x, addresses, which):
        if isinstance(x, text_type):
            addresses['recipients'].append(x)
            addresses[which] = x
        elif isinstance(x, list) or isinstance(x, tuple):
            if not all([isinstance(k, text_type) for k in x]):
                raise YagAddressError
            addresses['recipients'].extend(x)
            addresses[which] = '; '.join(x)
        elif isinstance(x, dict):
            addresses['recipients'].extend(x.keys())
            addresses[which] = '; '.join(x.values())
        else:
            raise YagAddressError

    @staticmethod
    def _add_subject(msg, subject):
        if not subject:
            return
        if isinstance(subject, list):
            subject = ' '.join(subject)
        msg['Subject'] = subject

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
            try:
                content_name = os.path.basename(str(content_string))
            except UnicodeEncodeError:
                content_name = os.path.basename(content_string)
        # pylint: disable=unidiomatic-typecheck
        is_raw = type(content_string) == raw
        if os.path.isfile(content_string) and not is_raw:
            with open(content_string, 'rb') as f:
                content_object['encoding'] = 'base64'
                content = f.read()
        else:
            content_object['main_type'] = 'text'

            if is_raw:
                content_object['mime_object'] = MIMEText(content_string, _charset=self.encoding)
            else:
                content_object['mime_object'] = MIMEText(
                    content_string, 'html', _charset=self.encoding)
                content_object['sub_type'] = 'html'

            if content_object['sub_type'] is None:
                content_object['sub_type'] = 'plain'
            return content_object

        if content_object['main_type'] is None:
            content_type, _ = mimetypes.guess_type(content_string)

            if content_type is not None:
                content_object['main_type'], content_object['sub_type'] = content_type.split('/')

        if (content_object['main_type'] is None or
                content_object['encoding'] is not None):
            if content_object['encoding'] != 'base64':
                content_object['main_type'] = 'application'
                content_object['sub_type'] = 'octet-stream'

        mime_object = MIMEBase(content_object['main_type'], content_object['sub_type'],
                               name=content_name)
        mime_object.set_payload(content)
        content_object['mime_object'] = mime_object
        return content_object

    def feedback(self, message="Awesome features! You made my day! How can I contribute?"):
        """ Most important function. Please send me feedback :-) """
        self.send('kootenpv@gmail.com', 'Yagmail feedback', message)

    def __del__(self):
        try:
            if not self.is_closed:
                self.close()
        except AttributeError:
            pass


class SMTP_SSL(SMTP):

    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn("It is now possible to simply use 'SMTP' with smtp_ssl=True",
                      category=DeprecationWarning)
        kwargs["smtp_ssl"] = True
        super(SMTP_SSL, self).__init__(*args, **kwargs)
