__project__ = "yagmail"
__version__ = "0.15.277"

from yagmail.error import YagConnectionClosed, YagAddressError
from yagmail.password import register
from yagmail.sender import SMTP, logging
from yagmail.utils import raw, inline

__all__ = [
    "YagConnectionClosed",
    "YagAddressError",
    "register",
    "SMTP",
    "logging",
    "raw",
    "inline",
]
