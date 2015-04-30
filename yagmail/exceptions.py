"""Contains the exceptions"""

class UserNotFoundInKeyring(Exception):
    pass

class YagConnectionClosed(Exception):
    pass

class YagAddressError(Exception):
    pass

class YagContentError(Exception):
    pass
