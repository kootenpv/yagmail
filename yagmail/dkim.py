from typing import NamedTuple

import dkim


class DKIM(NamedTuple):
    domain: str
    private_key: str
    include_headers: list
    selector: str


class DKIMHandler:

    def __init__(self, dkim: DKIM):
        self.dkim = dkim

    def add_dkim_sig_to_message(self, msg) -> None:
        # Based on example from:
        # https://github.com/russellballestrini/russell.ballestrini.net/blob/master/content/
        # 2018-06-04-quickstart-to-dkim-sign-email-with-python.rst
        sig = dkim.sign(
            message=msg.as_bytes(),
            selector=self.dkim.selector,
            domain=self.dkim.domain,
            privkey=self.dkim.private_key,
            include_headers=self.dkim.include_headers,
        )
        # add the dkim signature to the email message headers.
        # decode the signature back to string_type because later on
        # the call to msg.as_string() performs it's own bytes encoding...
        msg["DKIM-Signature"] = sig[len("DKIM-Signature: "):].decode()
