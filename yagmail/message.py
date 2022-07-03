import datetime
import email.encoders
import io
import json
import mimetypes
import os
import sys
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from yagmail.dkim import add_dkim_sig_to_message
from yagmail.headers import add_message_id
from yagmail.headers import add_recipients_headers
from yagmail.headers import add_subject
from yagmail.utils import raw, inline

PY3 = sys.version_info[0] > 2


def dt_converter(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def serialize_object(content):
    is_marked_up = False
    if isinstance(content, (dict, list, tuple, set)):
        content = "<pre>" + json.dumps(content, indent=4, default=dt_converter) + "</pre>"
        is_marked_up = True
    elif "DataFrame" in content.__class__.__name__:
        try:
            content = content.render()
        except AttributeError:
            content = content.to_html()
        is_marked_up = True
    return is_marked_up, content


def prepare_message(
    user,
    useralias,
    addresses,
    subject,
    contents,
    attachments,
    headers,
    encoding,
    prettify_html=True,
    message_id=None,
    group_messages=True,
    dkim=None,
):
    # check if closed!!!!!! XXX
    """Prepare a MIME message"""

    if not isinstance(contents, (list, tuple)):
        if contents is not None:
            contents = [contents]
    if not isinstance(attachments, (list, tuple)):
        if attachments is not None:
            attachments = [attachments]
    # merge contents and attachments for now.
    if attachments is not None:
        for a in attachments:
            if not isinstance(a, io.IOBase) and not os.path.isfile(a):
                msg = "{a} must be a valid filepath or file handle (instance of io.IOBase). {a} is of type {tp}"
                raise TypeError(msg.format(a=a, tp=type(a)))
        contents = attachments if contents is None else contents + attachments

    if contents is not None:
        contents = [serialize_object(x) for x in contents]

    has_included_images, content_objects = prepare_contents(contents, encoding)
    if contents is not None:
        contents = [x[1] for x in contents]

    msg = MIMEMultipart()
    if headers is not None:
        # Strangely, msg does not have an update method, so then manually.
        for k, v in headers.items():
            msg[k] = v
    if headers is None or "Date" not in headers:
        msg["Date"] = formatdate()

    msg_alternative = MIMEMultipart("alternative")
    msg_related = MIMEMultipart("related")
    msg_related.attach("-- HTML goes here --")
    msg.attach(msg_alternative)
    add_subject(msg, subject)
    add_recipients_headers(user, useralias, msg, addresses)
    add_message_id(msg, message_id, group_messages)
    htmlstr = ""
    altstr = []
    if has_included_images:
        msg.preamble = "This message is best displayed using a MIME capable email reader."

    if contents is not None:
        for content_object, content_string in zip(content_objects, contents):
            if content_object["main_type"] == "image":
                # all image objects need base64 encoding, so do it now
                email.encoders.encode_base64(content_object["mime_object"])
                # aliased image {'path' : 'alias'}
                if isinstance(content_string, dict) and len(content_string) == 1:
                    for key in content_string:
                        hashed_ref = str(abs(hash(key)))
                        alias = content_string[key]
                    # pylint: disable=undefined-loop-variable
                    content_string = key
                else:
                    alias = os.path.basename(str(content_string))
                    hashed_ref = str(abs(hash(alias)))

                # TODO: I should probably remove inline now that there is "attachments"
                # if string is `inline`, inline, else, attach
                # pylint: disable=unidiomatic-typecheck
                if type(content_string) == inline:
                    htmlstr += '<img src="cid:{0}" title="{1}"/>'.format(hashed_ref, alias)
                    content_object["mime_object"].add_header("Content-ID", "<{0}>".format(hashed_ref))
                    altstr.append("-- img {0} should be here -- ".format(alias))
                    # inline images should be in related MIME block
                    msg_related.attach(content_object["mime_object"])
                else:
                    # non-inline images get attached like any other attachment
                    msg.attach(content_object["mime_object"])

            else:
                if content_object["encoding"] == "base64":
                    email.encoders.encode_base64(content_object["mime_object"])
                    msg.attach(content_object["mime_object"])
                elif content_object["sub_type"] not in ["html", "plain"]:
                    msg.attach(content_object["mime_object"])
                else:
                    if not content_object["is_marked_up"]:
                        content_string = content_string.replace("\n", "<br>")
                    try:
                        htmlstr += "<div>{0}</div>".format(content_string)
                        if PY3 and prettify_html:
                            import premailer

                            htmlstr = premailer.transform(htmlstr)
                    except UnicodeEncodeError:
                        htmlstr += u"<div>{0}</div>".format(content_string)
                    altstr.append(content_string)

    msg_related.get_payload()[0] = MIMEText(htmlstr, "html", _charset=encoding)
    msg_alternative.attach(MIMEText("\n".join(altstr), _charset=encoding))
    msg_alternative.attach(msg_related)

    if dkim is not None:
        add_dkim_sig_to_message(msg, dkim)

    return msg


def prepare_contents(contents, encoding):
    mime_objects = []
    has_included_images = False
    if contents is not None:
        unnamed_attachment_id = 1
        for is_marked_up, content in contents:
            if isinstance(content, io.IOBase):
                if not hasattr(content, "name"):
                    # If the IO object has no name attribute, give it one.
                    content.name = "attachment_{}".format(unnamed_attachment_id)

            content_object = get_mime_object(is_marked_up, content, encoding)
            if content_object["main_type"] == "image":
                has_included_images = True
            mime_objects.append(content_object)
    return has_included_images, mime_objects


def get_mime_object(is_marked_up, content_string, encoding):
    content_object = {
        "mime_object": None,
        "encoding": None,
        "main_type": None,
        "sub_type": None,
        "is_marked_up": is_marked_up,
    }
    try:
        content_name = os.path.basename(str(content_string))
    except UnicodeEncodeError:
        content_name = os.path.basename(content_string)
    # pylint: disable=unidiomatic-typecheck
    is_raw = type(content_string) == raw
    try:
        is_file = os.path.isfile(content_string)
    except ValueError:
        is_file = False
        content_name = str(abs(hash(content_string)))
    except TypeError:
        # This happens when e.g. tuple is passed.
        is_file = False
    if not is_raw and is_file:
        with open(content_string, "rb") as f:
            content_object["encoding"] = "base64"
            content = f.read()

    elif isinstance(content_string, io.IOBase):
        content = content_string.read()
        # no need to except AttributeError, as we set missing name attributes in the `prepare_contents` function
        content_name = os.path.basename(content_string.name)
        content_object["encoding"] = "base64"

    else:
        content_object["main_type"] = "text"

        if is_raw:
            content_object["mime_object"] = MIMEText(content_string, _charset=encoding)
        else:
            content_object["mime_object"] = MIMEText(content_string, "html", _charset=encoding)
            content_object["sub_type"] = "html"

        if content_object["sub_type"] is None:
            content_object["sub_type"] = "plain"
        return content_object

    if content_object["main_type"] is None:
        # Guess the mimetype with the filename
        content_type, _ = mimetypes.guess_type(content_name)

        if content_type is not None:
            content_object["main_type"], content_object["sub_type"] = content_type.split("/")

    if content_object["main_type"] is None or content_object["encoding"] is not None:
        if content_object["encoding"] != "base64":
            content_object["main_type"] = "application"
            content_object["sub_type"] = "octet-stream"

    # Fixed the problem in issue: https://github.com/kootenpv/yagmail/issues/242
    if content_object["main_type"] == 'text' and content_object["sub_type"] == 'plain':
        content_object["main_type"] = 'application'
        content_object["sub_type"] = 'octet-stream'

    mime_object = MIMEBase(content_object["main_type"], content_object["sub_type"], name=(encoding, "", content_name))
    mime_object.set_payload(content)
    if content_object["main_type"] == "application":
        mime_object.add_header("Content-Disposition", "attachment", filename=content_name)
    content_object["mime_object"] = mime_object
    return content_object
