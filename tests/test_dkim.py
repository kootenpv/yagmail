import base64
import logging
from pathlib import Path
from unittest.mock import Mock

import dkim


def get_txt_from_test_file(*args, **kwargs):
    dns_data_file = Path(__file__).parent / "domainkey-dns.txt"

    return Path(dns_data_file).read_bytes()


def _test_email_with_dkim(include_headers):
    from yagmail import SMTP
    from yagmail.dkim import DKIM

    private_key_path = Path(__file__).parent / "privkey.pem"

    private_key = private_key_path.read_bytes()

    dkim_obj = DKIM(
        domain=b"a.com",
        selector=b"selector",
        private_key=private_key,
        include_headers=include_headers,
    )

    yag = SMTP(
        user="a@a.com",
        host="smtp.blabla.com",
        port=25,
        dkim=dkim_obj,
    )

    yag.login = Mock()

    to = "b@b.com"

    recipients, msg_bytes = yag.send(
        to=to,
        subject="hello from tests",
        contents="important message",
        preview_only=True
    )

    msg_string = msg_bytes.decode("utf8")

    assert recipients == [to]
    assert "Subject: hello from tests" in msg_string
    text_b64 = base64.b64encode(b"important message").decode("utf8")
    assert text_b64 in msg_string

    dkim_string1 = "DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/simple; d=a.com; i=@a.com;\n " \
                   "q=dns/txt; s=selector; t="
    assert dkim_string1 in msg_string

    l = logging.getLogger()
    l.setLevel(level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    assert dkim.verify(
        message=msg_string.encode("utf8"),
        logger=l,
        dnsfunc=get_txt_from_test_file
    )

    return msg_string


def test_email_with_dkim():
    msg_string = _test_email_with_dkim(include_headers=[b"To", b"From", b"Subject"])

    dkim_string2 = "h=to : from : subject;"
    assert dkim_string2 in msg_string


def test_dkim_without_including_headers():
    msg_string = _test_email_with_dkim(include_headers=None)

    dkim_string_headers = "h=content-type : mime-version :\n date : subject : from : to : message-id : from;\n"
    assert dkim_string_headers in msg_string

