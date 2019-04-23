__project__ = "yagmail"
__version__ = "0.11.220"

from yagmail.error import YagConnectionClosed
from yagmail.error import YagAddressError
from yagmail.password import register
from yagmail.sender import SMTP
from yagmail.sender import logging
from yagmail.utils import raw
from yagmail.utils import inline
