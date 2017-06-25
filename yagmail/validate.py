""" Module for validating emails.
"Forked" only the regexp part from the "validate_email", see copyright below.
The reason is that if you plan on sending out loads of emails or
doing checks can actually get you blacklisted, if it would be reliable at all.
However, this regexp is the best one I've come accross, so props to Syrus Akbary.
"""

# -----------------------------------------------------------------------------------------------

# RFC 2822 - style email validation for Python
# (c) 2012 Syrus Akbary <me@syrusakbary.com>
# Extended from (c) 2011 Noel Bush <noel@aitools.org>
# for support of mx and user check
# This code is made available to you under the GNU LGPL v3.
#
# This module provides a single method, valid_email_address(),
# which returns True or False to indicate whether a given address
# is valid according to the 'addr-spec' part of the specification
# given in RFC 2822.  Ideally, we would like to find this
# in some other library, already thoroughly tested and well-
# maintained.  The standard Python library email.utils
# contains a parse_addr() function, but it is not sufficient
# to detect many malformed addresses.
#
# This implementation aims to be faithful to the RFC, with the
# exception of a circular definition (see comments below), and
# with the omission of the pattern components marked as "obsolete".

import re


try:
    from .error import YagInvalidEmailAddress
except (ValueError, SystemError):
    # stupid fix to make it easy to load interactively
    from error import YagInvalidEmailAddress

# All we are really doing is comparing the input string to one
# gigantic regular expression.  But building that regexp, and
# ensuring its correctness, is made much easier by assembling it
# from the "tokens" defined by the RFC.  Each of these tokens is
# tested in the accompanying unit test file.
#
# The section of RFC 2822 from which each pattern component is
# derived is given in an accompanying comment.
#
# (To make things simple, every string below is given as 'raw',
# even when it's not strictly necessary.  This way we don't forget
# when it is necessary.)
#
# see 2.2.2. Structured Header Field Bodies
WSP = r'[ \t]'
# see 2.2.3. Long Header Fields
CRLF = r'(?:\r\n)'
# see 3.2.1. Primitive Tokens
NO_WS_CTL = r'\x01-\x08\x0b\x0c\x0f-\x1f\x7f'
# see 3.2.2. Quoted characters
QUOTED_PAIR = r'(?:\\.)'
FWS = r'(?:(?:' + WSP + r'*' + CRLF + r')?' + \
      WSP + \
    r'+)'                                            # see 3.2.3. Folding white space and comments
CTEXT = r'[' + NO_WS_CTL + \
        r'\x21-\x27\x2a-\x5b\x5d-\x7e]'              # see 3.2.3
CCONTENT = r'(?:' + CTEXT + r'|' + \
           QUOTED_PAIR + \
    r')'                        # see 3.2.3 (NB: The RFC includes COMMENT here
# as well, but that would be circular.)
COMMENT = r'\((?:' + FWS + r'?' + CCONTENT + \
          r')*' + FWS + r'?\)'                       # see 3.2.3
CFWS = r'(?:' + FWS + r'?' + COMMENT + ')*(?:' + \
       FWS + '?' + COMMENT + '|' + FWS + ')'         # see 3.2.3
ATEXT = r'[\w!#$%&\'\*\+\-/=\?\^`\{\|\}~]'           # see 3.2.4. Atom
ATOM = CFWS + r'?' + ATEXT + r'+' + CFWS + r'?'      # see 3.2.4
DOT_ATOM_TEXT = ATEXT + r'+(?:\.' + ATEXT + r'+)*'   # see 3.2.4
DOT_ATOM = CFWS + r'?' + DOT_ATOM_TEXT + CFWS + r'?'  # see 3.2.4
QTEXT = r'[' + NO_WS_CTL + \
        r'\x21\x23-\x5b\x5d-\x7e]'                   # see 3.2.5. Quoted strings
QCONTENT = r'(?:' + QTEXT + r'|' + \
           QUOTED_PAIR + r')'                        # see 3.2.5
QUOTED_STRING = CFWS + r'?' + r'"(?:' + FWS + \
    r'?' + QCONTENT + r')*' + FWS + \
    r'?' + r'"' + CFWS + r'?'
LOCAL_PART = r'(?:' + DOT_ATOM + r'|' + \
             QUOTED_STRING + \
    r')'                    # see 3.4.1. Addr-spec specification
DTEXT = r'[' + NO_WS_CTL + r'\x21-\x5a\x5e-\x7e]'    # see 3.4.1
DCONTENT = r'(?:' + DTEXT + r'|' + \
           QUOTED_PAIR + r')'                        # see 3.4.1
DOMAIN_LITERAL = CFWS + r'?' + r'\[' + \
    r'(?:' + FWS + r'?' + DCONTENT + \
    r')*' + FWS + r'?\]' + CFWS + r'?'  # see 3.4.1
DOMAIN = r'(?:' + DOT_ATOM + r'|' + \
         DOMAIN_LITERAL + r')'                       # see 3.4.1
ADDR_SPEC = LOCAL_PART + r'@' + DOMAIN               # see 3.4.1

# A valid address will match exactly the 3.4.1 addr-spec.
VALID_ADDRESS_REGEXP = '^' + ADDR_SPEC + '$'


def validate_email_with_regex(email_address):
    """
    Note that this will only filter out syntax mistakes in emailaddresses.
    If a human would think it is probably a valid email, it will most likely pass.
    However, it could still very well be that the actual emailaddress has simply
    not be claimed by anyone (so then this function fails to devalidate).
    """
    if not re.match(VALID_ADDRESS_REGEXP, email_address):
        emsg = 'Emailaddress "{}" is not valid according to RFC 2822 standards'.format(
            email_address)
        raise YagInvalidEmailAddress(emsg)
    # apart from the standard, I personally do not trust email addresses without dot.
    if "." not in email_address and "localhost" not in email_address.lower():
        raise YagInvalidEmailAddress("Missing dot in emailaddress")
