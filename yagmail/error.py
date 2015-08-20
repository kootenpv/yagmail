"""Contains the exceptions"""


class YagConnectionClosed(Exception):

    """
    The connection object has been closed by the user.
    This object can be used to send emails again after logging in,
    using self.login().
    """
    pass


class YagAddressError(Exception):

    """
    This means that the address was given in an invalid format.
    Note that From can either be a string, or a dictionary where the key is an email,
    and the value is an alias {'sample@gmail.com', 'Sam'}. In the case of 'to',
    it can either be a string (email), a list of emails (email addresses without aliases)
    or a dictionary where keys are the email addresses and the values indicate the aliases.
    Furthermore, it does not do any validation of whether an email exists.
    """
    pass


class YagInvalidEmailAddress(Exception):

    """
    Note that this will only filter out syntax mistakes in emailaddresses.
    If a human would think it is probably a valid email, it will most likely pass.
    However, it could still very well be that the actual emailaddress has simply
    not be claimed by anyone (so then this function fails to devalidate).
    """
    pass
