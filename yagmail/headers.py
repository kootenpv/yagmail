import hashlib
import random
import time
from email.message import Message
from email.utils import formataddr
from typing import Any, Dict, List, Optional, Tuple, Union

from yagmail.error import YagAddressError

AddressInput = Union[str, List[str], Tuple[str, ...], Dict[str, str]]


def resolve_addresses(
    user: str,
    useralias: str,
    to: Optional[AddressInput],
    cc: Optional[AddressInput],
    bcc: Optional[AddressInput]
) -> Dict[str, Any]:
    """ Handle the targets addresses, adding aliases when defined """
    addresses: Dict[str, Any] = {"recipients": []}
    if to is not None:
        make_addr_alias_target(to, addresses, "To")
    elif cc is not None and bcc is not None:
        make_addr_alias_target([user, useralias], addresses, "To")
    else:
        addresses["recipients"].append(user)
    if cc is not None:
        make_addr_alias_target(cc, addresses, "Cc")
    if bcc is not None:
        make_addr_alias_target(bcc, addresses, "Bcc")
    return addresses


def make_addr_alias_user(email_addr: Union[str, Dict[str, str]]) -> Tuple[str, str]:
    if isinstance(email_addr, str):
        if "@" not in email_addr:
            email_addr += "@gmail.com"
        return (email_addr, email_addr)
    if isinstance(email_addr, dict):
        if len(email_addr) == 1:
            return (list(email_addr.keys())[0], list(email_addr.values())[0])
    raise YagAddressError


def make_addr_alias_target(x: AddressInput, addresses: Dict[str, Any], which: str) -> None:
    if isinstance(x, str):
        addresses["recipients"].append(x)
        addresses[which] = x
    elif isinstance(x, (list, tuple)):
        if not all([isinstance(k, str) for k in x]):
            raise YagAddressError
        addresses["recipients"].extend(x)
        addresses[which] = ",".join(x)
    elif isinstance(x, dict):
        addresses["recipients"].extend(x.keys())
        addresses[which] = ",".join(x.values())
    else:
        raise YagAddressError


def add_subject(msg: Message, subject: Optional[Union[str, List[str]]]) -> None:
    if not subject:
        return
    if isinstance(subject, list):
        subject = " ".join(subject)
    msg["Subject"] = subject


def add_recipients_headers(
    user: str, useralias: str, msg: Message, addresses: Dict[str, Any]
) -> None:
    # Quoting the useralias so it should match display-name from
    # https://tools.ietf.org/html/rfc5322 , even if it's an email address.
    # msg["From"] = '"{0}" <{1}>'.format(useralias.replace("\\", "\\\\").replace('"', '\\"'), user)
    # formataddr can support From chinese useralias, just like:
    # mail_user = {'notice@test.com': '中文测试'}
    msg['From'] = formataddr((useralias.replace("\\", "\\\\").replace('"', '\\"'), user))
    if "To" in addresses:
        msg["To"] = addresses["To"]
    else:
        msg["To"] = useralias
    if "Cc" in addresses:
        msg["Cc"] = addresses["Cc"]


def add_message_id(
    msg: Message, message_id: Optional[str] = None, group_messages: bool = True
) -> None:
    if message_id is None:
        from_val = msg.get("From", "")
        to_val = msg.get("To", "")
        subject_val = msg.get("Subject", "None")
        if group_messages:
            addr = " ".join(sorted([str(from_val), str(to_val)])) + str(subject_val)
        else:
            addr = str(time.time() + random.random())
        message_id = "<" + hashlib.md5(addr.encode()).hexdigest() + "@yagmail>"
    msg["Message-ID"] = message_id
