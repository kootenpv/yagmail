__project__ = 'yagmail'
__version__ = "0.4.110"

from .error import YagConnectionClosed
from .error import YagAddressError
from .yagmail import SMTP
from .yagmail import register
from .yagmail import logging
from .yagmail import raw
from .yagmail import inline
