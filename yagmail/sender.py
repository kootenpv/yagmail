# when there is a bcc a different message has to be sent to the bcc
# person, to show that they are bcc'ed

import logging
import smtplib
import time
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

from yagmail.dkim import DKIM
from yagmail.headers import AddressInput, make_addr_alias_user, resolve_addresses
from yagmail.log import get_logger
from yagmail.message import prepare_message
from yagmail.oauth2 import get_oauth2_info, get_oauth_string
from yagmail.password import handle_password
from yagmail.utils import find_user_home_path
from yagmail.validate import validate_email_with_regex


class Client:
    """ :class:`yagmail.Client` is a magic wrapper around
    ``smtplib``'s SMTP connection, and allows messages to be sent."""

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[Union[str, Dict[str, Any]]] = None,
        host: str = "smtp.gmail.com",
        port: Optional[Union[int, str]] = None,
        smtp_starttls: Optional[Union[bool, dict]] = None,
        smtp_ssl: bool = True,
        smtp_set_debuglevel: int = 0,
        smtp_skip_login: bool = False,
        encoding: str = "utf-8",
        oauth2_file: Optional[str] = None,
        soft_email_validation: bool = True,
        dkim: Optional[DKIM] = None,
        **kwargs: Any
    ):
        self.log = get_logger()
        self.set_logging()
        self.soft_email_validation = soft_email_validation
        if oauth2_file is not None:
            oauth2_info = get_oauth2_info(oauth2_file, user)
            if user is None:
                user = oauth2_info["email_address"]
        if smtp_skip_login and user is None:
            user = ""
        elif user is None:
            user = find_user_home_path()
        if user is None:
            raise ValueError(
                "No user provided. Pass `user=` to Client(), or create ~/.yagmail "
                "containing your email address."
            )
        self.user, self.useralias = make_addr_alias_user(user)
        if soft_email_validation:
            validate_email_with_regex(self.user)
        self.is_closed: Optional[bool] = None
        self.host = host
        self.port = str(port) if port is not None else "465" if smtp_ssl else "587"
        self.smtp_starttls = smtp_starttls
        self.ssl = smtp_ssl
        self.smtp_skip_login = smtp_skip_login
        self.debuglevel = smtp_set_debuglevel
        self.encoding = encoding
        self.kwargs = kwargs
        self.cache: Dict[Any, Any] = {}
        self.unsent: List[Tuple[List[str], str]] = []
        self.num_mail_sent = 0
        self.oauth2_file = oauth2_file
        self.credentials = password if oauth2_file is None else oauth2_info
        self.dkim = dkim
        self.smtp: Union[smtplib.SMTP, smtplib.SMTP_SSL] = None  # type: ignore

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        if not self.is_closed:
            self.close()
        return False

    @property
    def connection(self) -> Union[Type[smtplib.SMTP_SSL], Type[smtplib.SMTP]]:
        return smtplib.SMTP_SSL if self.ssl else smtplib.SMTP

    @property
    def starttls(self) -> Union[bool, dict]:
        if self.smtp_starttls is None:
            return False if self.ssl else True
        return self.smtp_starttls

    def set_logging(
        self, log_level: Optional[int] = logging.ERROR, file_path_name: Optional[str] = None
    ) -> None:
        """
        This function allows to change the logging backend, either output or file as backend
        It also allows to set the logging level (whether to display only critical/error/info/debug.
        for example::

            yag = yagmail.Client()
            yag.set_logging(yagmail.logging.DEBUG)  # to see everything

        and::

            yagmail.set_logging(yagmail.logging.DEBUG, 'somelocalfile.log')

        lastly, a log_level of :py:class:`None` will make sure there is no I/O.
        """
        self.log = get_logger(log_level, file_path_name)

    def prepare_send(
        self,
        to: Optional[AddressInput] = None,
        subject: Optional[Union[str, List[str]]] = None,
        contents: Optional[Any] = None,
        attachments: Optional[Any] = None,
        cc: Optional[AddressInput] = None,
        bcc: Optional[AddressInput] = None,
        headers: Optional[Dict[str, str]] = None,
        prettify_html: bool = True,
        message_id: Optional[str] = None,
        group_messages: bool = True,
    ) -> Tuple[List[str], str]:
        addresses = resolve_addresses(self.user, self.useralias, to, cc, bcc)

        if self.soft_email_validation:
            for email_addr in addresses["recipients"]:
                validate_email_with_regex(email_addr)

        msg = prepare_message(
            self.user,
            self.useralias,
            addresses,
            subject,
            contents,
            attachments,
            headers,
            self.encoding,
            prettify_html,
            message_id,
            group_messages,
            self.dkim,
        )

        recipients = addresses["recipients"]
        msg_strings = msg.as_string()
        return recipients, msg_strings

    def send(
        self,
        to: Optional[AddressInput] = None,
        subject: Optional[Union[str, List[str]]] = None,
        contents: Optional[Any] = None,
        attachments: Optional[Any] = None,
        cc: Optional[AddressInput] = None,
        bcc: Optional[AddressInput] = None,
        preview_only: bool = False,
        headers: Optional[Dict[str, str]] = None,
        prettify_html: bool = True,
        message_id: Optional[str] = None,
        group_messages: bool = True,
    ) -> Union[Tuple[List[str], str], Dict[str, Any], bool]:
        """ Use this to send an email with gmail"""
        self.login()
        recipients, msg_strings = self.prepare_send(
            to,
            subject,
            contents,
            attachments,
            cc,
            bcc,
            headers,
            prettify_html,
            message_id,
            group_messages,
        )
        if preview_only:
            return recipients, msg_strings

        return self._attempt_send(recipients, msg_strings)

    def _attempt_send(self, recipients: List[str], msg_strings: str) -> Union[Dict[str, Any], bool]:
        attempts = 0
        while attempts < 3:
            try:
                result = self.smtp.sendmail(self.user, recipients, msg_strings)
                self.log.info("Message sent to %s", recipients)
                self.num_mail_sent += 1
                return result
            except smtplib.SMTPServerDisconnected as e:
                self.log.error(e)
                attempts += 1
                if attempts < 3:
                    try:
                        self.login()
                    except Exception as reconnect_err:
                        self.log.error("Failed to reconnect during retry: %s", reconnect_err)
                time.sleep(attempts * 3)
        self.unsent.append((recipients, msg_strings))
        return False

    def send_unsent(self) -> None:
        """
        Emails that were not being able to send will be stored in :attr:`self.unsent`.
        Use this function to attempt to send these again
        """
        for i in range(len(self.unsent)):
            recipients, msg_strings = self.unsent.pop(i)
            self._attempt_send(recipients, msg_strings)

    def close(self) -> None:
        """ Close the connection to the SMTP server """
        self.is_closed = True
        try:
            self.smtp.quit()
        except (TypeError, AttributeError, smtplib.SMTPServerDisconnected):
            pass

    def login(self) -> None:
        """ Connect and login to the SMTP server. """
        if self.oauth2_file is not None:
            if isinstance(self.credentials, dict):
                self._login_oauth2(self.credentials)
            else:
                raise TypeError("OAuth2 credentials must be a dictionary")
        else:
            self._login(self.credentials)

    def _login(self, password: Any) -> None:
        """
        Login to the SMTP server using password. `login` only needs to be manually run when the
        connection to the SMTP server was closed by the user.
        """
        self.smtp = self.connection(self.host, self.port, **self.kwargs)  # type: ignore
        self.smtp.set_debuglevel(self.debuglevel)
        if self.starttls:
            self.smtp.ehlo()
            if self.starttls is True:
                self.smtp.starttls()
            else:
                self.smtp.starttls(**self.starttls)  # type: ignore
            self.smtp.ehlo()
        self.is_closed = False
        if not self.smtp_skip_login:
            password = self.handle_password(self.user, password)
            self.smtp.login(self.user, password)
        self.log.info("Connected to SMTP @ %s:%s as %s", self.host, self.port, self.user)

    @staticmethod
    def handle_password(user: str, password: Optional[str]) -> str:
        return handle_password(user, password)

    @staticmethod
    def get_oauth_string(user: str, oauth2_info: Dict[str, Any]) -> str:
        return get_oauth_string(user, oauth2_info)

    def _login_oauth2(self, oauth2_info: Dict[str, Any]) -> None:
        if "email_address" in oauth2_info:
            oauth2_info = oauth2_info.copy()
            oauth2_info.pop("email_address")
        self.smtp = self.connection(self.host, self.port, **self.kwargs)  # type: ignore
        try:
            self.smtp.set_debuglevel(self.debuglevel)
        except AttributeError:
            pass
        auth_string = self.get_oauth_string(self.user, oauth2_info)
        self.smtp.ehlo(oauth2_info["google_client_id"])
        if self.starttls is True:
            self.smtp.starttls()
        self.smtp.docmd("AUTH", "XOAUTH2 " + auth_string)

    def feedback(
        self,
        message: str = "Awesome features! You made my day! How can I contribute?",
    ) -> None:
        """ Most important function. Please send me feedback :-) """
        self.send("kootenpv@gmail.com", "Yagmail feedback", message)

    def __del__(self) -> None:
        try:
            if not self.is_closed:
                self.close()
        except AttributeError:
            pass


SMTP = Client
