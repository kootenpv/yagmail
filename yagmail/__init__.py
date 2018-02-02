__project__ = 'yagmail'
__version__ = "0.10.209"

from yagmail.error import YagConnectionClosed
from yagmail.error import YagAddressError
from yagmail.__main__ import register
from yagmail.sender import SMTP
from yagmail.sender import logging
from yagmail.sender import raw
from yagmail.sender import inline
