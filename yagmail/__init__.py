from pkg_resources import get_distribution

__project__ = 'yagmail'
__version__ = get_distribution(__project__).version

from .error import YagConnectionClosed
from .error import YagAddressError
from .yagmail import Connect
from .yagmail import register
