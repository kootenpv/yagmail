from pathlib import Path
from unittest.mock import Mock


def test_email_with_dkim():
    from yagmail import SMTP
    from yagmail.dkim import DKIM

    private_key_path = Path(__file__).parent / "privkey.pem"

    private_key = private_key_path.read_bytes()

    dkim = DKIM(
        domain=b"a.com",
        selector=b"selector",
        private_key=private_key,
        include_headers=[b"To", b"From", b"Subject"]
    )
    yag = SMTP(
        user="a@a.com",
        host="smtp.blabla.com",
        port=25,
        dkim=dkim,
    )

    yag.login = Mock()

    to = "b@b.com"

    recipients, msg_string = yag.send(
        to=to,
        subject="hello from tests",
        contents="important message",
        preview_only=True
    )

    assert recipients == [to]

    dkim_string1 = "DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/simple; d=a.com; i=@a.com;\n " \
                   "q=dns/txt; s=selector; t="
    assert dkim_string1 in msg_string

    dkim_string2 = "h=to : from : subject;"
    assert dkim_string2 in msg_string

    assert "Subject: hello from tests" in msg_string