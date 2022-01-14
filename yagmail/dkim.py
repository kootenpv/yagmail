from email.mime.base import MIMEBase
from typing import NamedTuple

try:
    import dkim
except ImportError:
    dkim = None
    pass


class DKIM(NamedTuple):
    domain: bytes
    private_key: bytes
    include_headers: list
    selector: bytes


def add_dkim_sig_to_message(msg: MIMEBase, dkim_obj: DKIM) -> None:
    if dkim is None:
        raise RuntimeError("dkim package not installed")

    # Based on example from:
    # https://github.com/russellballestrini/russell.ballestrini.net/blob/master/content/
    # 2018-06-04-quickstart-to-dkim-sign-email-with-python.rst
    sig = dkim.sign(
        message=msg.as_bytes(),
        selector=dkim_obj.selector,
        domain=dkim_obj.domain,
        privkey=dkim_obj.private_key,
        include_headers=dkim_obj.include_headers,
    )
    # add the dkim signature to the email message headers.
    # decode the signature back to string_type because later on
    # the call to msg.as_string() performs it's own bytes encoding...
    msg["DKIM-Signature"] = sig[len("DKIM-Signature: "):].decode()
