import asyncio
import socket
import ssl
from smtplib import (
    SMTPAuthenticationError,
    SMTPConnectError,
    SMTPDataError,
    SMTPException,
    SMTPHeloError,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
    SMTPServerDisconnected,
)
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import yagmail
from yagmail.dkim import DKIM
from yagmail.headers import AddressInput


async def upgrade_to_tls(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    ssl_context: ssl.SSLContext,
    server_hostname: str
) -> None:
    """Upgrade an existing stream connection to TLS, compatible with Python 3.8+."""
    if hasattr(writer, "start_tls"):
        await writer.start_tls(ssl_context, server_hostname=server_hostname)
    else:
        # Fallback for Python 3.8 - 3.10
        loop = asyncio.get_running_loop()
        protocol = writer.transport.get_protocol()
        new_transport = await loop.start_tls(
            writer.transport,
            protocol,
            ssl_context,
            server_side=False,
            server_hostname=server_hostname
        )
        writer._transport = new_transport  # type: ignore[attr-defined]
        reader._transport = new_transport  # type: ignore[attr-defined]
        if hasattr(protocol, "_replace_writer"):
            protocol._replace_writer(writer)  # type: ignore[attr-defined]


class RawAsyncSMTP:
    """A raw asyncio-based SMTP protocol client."""

    def __init__(
        self,
        host: str = "smtp.gmail.com",
        port: int = 465,
        local_hostname: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.host = host
        self.port = port
        self.local_hostname = local_hostname or socket.getfqdn()
        self.timeout = timeout
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self, use_tls: bool = False, start_tls: bool = False) -> None:
        if use_tls:
            ssl_context = ssl.create_default_context()
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, ssl=ssl_context),
                timeout=self.timeout
            )
        else:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )

        code, message = await self.read_response()
        if code != 220:
            raise SMTPConnectError(code, message)

        await self.ehlo()

        if start_tls or (not use_tls and "STARTTLS" in message):
            await self.starttls()

    async def read_response(self) -> Tuple[int, str]:
        if self.reader is None:
            raise SMTPServerDisconnected("Not connected")
        code = -1
        lines = []
        while True:
            try:
                line = await asyncio.wait_for(self.reader.readline(), timeout=self.timeout)
            except asyncio.TimeoutError:
                raise socket.timeout("SMTP connection timed out")
            if not line:
                raise SMTPServerDisconnected("Connection closed unexpectedly")
            line_str = line.decode("utf-8", errors="ignore").rstrip("\r\n")
            lines.append(line_str)
            if len(line_str) >= 3:
                try:
                    code = int(line_str[:3])
                except ValueError:
                    pass
                if len(line_str) >= 4 and line_str[3] == '-':
                    continue
                else:
                    break
            else:
                break
        return code, "\n".join(lines)

    async def ehlo(self) -> None:
        if self.writer is None:
            raise SMTPServerDisconnected("Not connected")
        self.writer.write(f"EHLO {self.local_hostname}\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 250:
            self.writer.write(f"HELO {self.local_hostname}\r\n".encode())
            await self.writer.drain()
            code, message = await self.read_response()
            if code != 250:
                raise SMTPHeloError(code, message)

    async def starttls(self, ssl_context: Optional[ssl.SSLContext] = None) -> None:
        if self.writer is None or self.reader is None:
            raise SMTPServerDisconnected("Not connected")
        self.writer.write(b"STARTTLS\r\n")
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 220:
            raise SMTPException(f"STARTTLS failed: {message}")

        if ssl_context is None:
            ssl_context = ssl.create_default_context()

        await upgrade_to_tls(self.reader, self.writer, ssl_context, self.host)
        await self.ehlo()

    async def login(self, user: str, password: str) -> None:
        if self.writer is None:
            raise SMTPServerDisconnected("Not connected")
        import base64

        auth_plain = base64.b64encode(f"\0{user}\0{password}".encode()).decode("utf-8")
        self.writer.write(f"AUTH PLAIN {auth_plain}\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()

        if code == 235:
            return

        self.writer.write(b"AUTH LOGIN\r\n")
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 334:
            raise SMTPAuthenticationError(code, message)

        user_b64 = base64.b64encode(user.encode("utf-8")).decode("utf-8")
        self.writer.write(f"{user_b64}\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 334:
            raise SMTPAuthenticationError(code, message)

        pass_b64 = base64.b64encode(password.encode("utf-8")).decode("utf-8")
        self.writer.write(f"{pass_b64}\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 235:
            raise SMTPAuthenticationError(code, message)

    async def login_oauth2(self, user: str, auth_string: str) -> None:
        if self.writer is None:
            raise SMTPServerDisconnected("Not connected")
        self.writer.write(f"AUTH XOAUTH2 {auth_string}\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 235:
            if code == 334:
                self.writer.write(b"\r\n")
                await self.writer.drain()
                code, message = await self.read_response()
            raise SMTPAuthenticationError(code, message)

    async def sendmail(
        self, from_addr: str, to_addrs: Union[str, List[str]], msg: str
    ) -> Dict[str, Any]:
        if self.writer is None:
            raise SMTPServerDisconnected("Not connected")
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]

        self.writer.write(f"MAIL FROM:<{from_addr}>\r\n".encode())
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 250:
            raise SMTPSenderRefused(code, message.encode("utf-8"), from_addr)

        errors = {}
        success_count = 0
        for addr in to_addrs:
            self.writer.write(f"RCPT TO:<{addr}>\r\n".encode())
            await self.writer.drain()
            code, message = await self.read_response()
            if code not in (250, 251):
                errors[addr] = (code, message.encode("utf-8"))
            else:
                success_count += 1

        if success_count == 0:
            raise SMTPRecipientsRefused(errors)

        self.writer.write(b"DATA\r\n")
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 354:
            raise SMTPDataError(code, message)

        lines = msg.splitlines()
        body_lines = []
        for line in lines:
            if line.startswith("."):
                body_lines.append("." + line)
            else:
                body_lines.append(line)
        body = "\r\n".join(body_lines) + "\r\n.\r\n"

        self.writer.write(body.encode("utf-8"))
        await self.writer.drain()
        code, message = await self.read_response()
        if code != 250:
            raise SMTPDataError(code, message)

        return errors

    async def quit(self) -> None:
        if self.writer is not None:
            try:
                self.writer.write(b"QUIT\r\n")
                await self.writer.drain()
                await self.read_response()
            except Exception:
                pass
            finally:
                self.close()

    def close(self) -> None:
        if self.writer is not None:
            try:
                self.writer.close()
            except Exception:
                pass
            self.writer = None
            self.reader = None


class AsyncClient(yagmail.Client):
    """
    Asynchronous version of yagmail.Client.
    Provides non-blocking versions of login, send, send_unsent, and close
    using Python's built-in asyncio event loop and raw socket streams.
    """

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
        super().__init__(
            user=user,
            password=password,
            host=host,
            port=port,
            smtp_starttls=smtp_starttls,
            smtp_ssl=smtp_ssl,
            smtp_set_debuglevel=smtp_set_debuglevel,
            smtp_skip_login=smtp_skip_login,
            encoding=encoding,
            oauth2_file=oauth2_file,
            soft_email_validation=soft_email_validation,
            dkim=dkim,
            **kwargs
        )
        self.is_closed = True
        self.smtp: Optional[RawAsyncSMTP] = None  # type: ignore[assignment]

    @property
    def send_lock(self) -> asyncio.Lock:
        if not hasattr(self, "_send_lock"):
            self._send_lock = asyncio.Lock()
        return self._send_lock

    @property
    def login_lock(self) -> asyncio.Lock:
        if not hasattr(self, "_login_lock"):
            self._login_lock = asyncio.Lock()
        return self._login_lock

    async def login(self) -> None:  # type: ignore[override]
        """Connect and login to the SMTP server asynchronously."""
        async with self.login_lock:
            if self.smtp is not None and not self.is_closed:
                return
            use_tls = str(self.port) == "465"
            self.smtp = RawAsyncSMTP(
                host=self.host,
                port=int(self.port),
                timeout=self.kwargs.get("timeout", 30.0)
            )
            await self.smtp.connect(use_tls=use_tls, start_tls=bool(self.starttls))

            if not self.smtp_skip_login:
                if self.oauth2_file is not None:
                    if isinstance(self.credentials, dict):
                        auth_string = self.get_oauth_string(self.user, self.credentials)
                        await self.smtp.login_oauth2(self.user, auth_string)
                    else:
                        raise TypeError("OAuth2 credentials must be a dictionary")
                else:
                    password = self.handle_password(
                        self.user,
                        self.credentials if isinstance(self.credentials, str) else None,
                    )
                    await self.smtp.login(self.user, password)

            self.is_closed = False

    async def send(  # type: ignore[override]
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
        """Send an email asynchronously."""
        recipients, msg_strings = self.prepare_send(
            to=to,
            subject=subject,
            contents=contents,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            headers=headers,
            prettify_html=prettify_html,
            message_id=message_id,
            group_messages=group_messages,
        )
        if preview_only:
            return recipients, msg_strings

        async with self.send_lock:
            if self.smtp is None or self.is_closed:
                await self.login()
            return await self._attempt_send_async(recipients, msg_strings)

    async def _attempt_send_async(
        self, recipients: List[str], msg_strings: str
    ) -> Union[Dict[str, Any], bool]:
        if self.smtp is None:
            raise SMTPServerDisconnected("Not connected")
        attempts = 0
        while attempts < 3:
            try:
                result = await self.smtp.sendmail(self.user, recipients, msg_strings)
                self.log.info("Message sent to %s", recipients)
                self.num_mail_sent += 1
                return result
            except SMTPServerDisconnected as e:
                self.log.error(e)
                self.is_closed = True
                attempts += 1
                if attempts < 3:
                    try:
                        await self.login()
                    except Exception as reconnect_err:
                        self.log.error("Failed to reconnect during retry: %s", reconnect_err)
                await asyncio.sleep(attempts * 3)
        self.unsent.append((recipients, msg_strings))
        return False

    async def send_unsent(self) -> None:  # type: ignore[override]
        """Attempt to send unsent emails asynchronously."""
        async with self.send_lock:
            if self.smtp is None or self.is_closed:
                await self.login()

            unsent_copy = list(self.unsent)
            self.unsent.clear()
            for recipients, msg_strings in unsent_copy:
                await self._attempt_send_async(recipients, msg_strings)

    async def close(self) -> None:  # type: ignore[override]
        """Synchronous-like close method that raises error to match aioyagmail API."""
        raise ValueError("Should be `async with` or use `await aclose()`")

    async def aclose(self) -> None:
        """Close the SMTP connection asynchronously."""
        async with self.send_lock:
            self.is_closed = True
            if self.smtp is not None:
                try:
                    await self.smtp.quit()
                except Exception:
                    pass
                finally:
                    self.smtp = None

    async def __aenter__(self) -> "AsyncClient":
        await self.login()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        if not self.is_closed:
            await self.aclose()
        return False

    def __del__(self) -> None:
        try:
            if not self.is_closed:
                self.is_closed = True
                if self.smtp is not None:
                    self.smtp.close()
                    self.smtp = None
        except Exception:
            pass


# For backward compatibility
AsyncSMTP = AsyncClient
AIOSMTP = AsyncClient
