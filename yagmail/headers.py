import time
import random
import hashlib
from yagmail.compat import text_type
from yagmail.error import YagAddressError


def resolve_addresses(user, useralias, to, cc, bcc):
    """ Handle the targets addresses, adding aliases when defined """
    addresses = {"recipients": []}
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


def make_addr_alias_user(email_addr):
    if isinstance(email_addr, text_type):
        if "@" not in email_addr:
            email_addr += "@gmail.com"
        return (email_addr, email_addr)
    if isinstance(email_addr, dict):
        if len(email_addr) == 1:
            return (list(email_addr.keys())[0], list(email_addr.values())[0])
    raise YagAddressError


def make_addr_alias_target(x, addresses, which):
    if isinstance(x, text_type):
        addresses["recipients"].append(x)
        addresses[which] = x
    elif isinstance(x, list) or isinstance(x, tuple):
        if not all([isinstance(k, text_type) for k in x]):
            raise YagAddressError
        addresses["recipients"].extend(x)
        addresses[which] = ",".join(x)
    elif isinstance(x, dict):
        addresses["recipients"].extend(x.keys())
        addresses[which] = ",".join(x.values())
    else:
        raise YagAddressError


def add_subject(msg, subject):
    if not subject:
        return
    if isinstance(subject, list):
        subject = " ".join(subject)
    msg["Subject"] = subject


def add_recipients_headers(user, useralias, msg, addresses):
    # Quoting the useralias so it should match display-name from https://tools.ietf.org/html/rfc5322 ,
    # even if it's an email address.
    msg["From"] = '"{0}" <{1}>'.format(useralias.replace("\\", "\\\\").replace('"', '\\"'), user)
    if "To" in addresses:
        msg["To"] = addresses["To"]
    else:
        msg["To"] = useralias
    if "Cc" in addresses:
        msg["Cc"] = addresses["Cc"]


def add_message_id(msg, message_id=None, group_messages=True):
    if message_id is None:
        if group_messages:
            addr = " ".join(sorted([msg["From"], msg["To"]])) + msg.get("Subject", "None")
        else:
            addr = str(time.time() + random.random())
        message_id = "<" + hashlib.md5(addr.encode()).hexdigest() + "@yagmail>"
    msg["Message-ID"] = message_id
