# ruff: noqa: I001
__project__ = "yagmail"
__version__ = "0.16.0"

from yagmail.error import YagConnectionClosed, YagAddressError
from yagmail.password import register
from yagmail.sender import SMTP, logging, Client
from yagmail.utils import raw, inline
from yagmail.async_core.aio import AsyncSMTP, AIOSMTP, AsyncClient

__all__ = [
    "YagConnectionClosed",
    "YagAddressError",
    "register",
    "SMTP",
    "logging",
    "raw",
    "inline",
    "AsyncSMTP",
    "AIOSMTP",
    "Client",
    "AsyncClient",
]
