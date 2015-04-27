# yagmail -- Yet Another GMAIL client

The goal here is to make it as simple and painless as possible to send emails.

In the end, your code will look something like this:

```python
import yagmail
yag = yagmail.Connect('mygmailusername')
yag.send('to@someone.com', 'subject', 'body')
```

Or a one-liner (connection will automatically close):
```python
yagmail.Connect('mygmailusername').send('to@someone.com', 'subject', 'body')
```

Note that it will read the password securely from your keyring (read below). If you don't want this, you can also initialize with:

```python
yag = yagmail.Connect('mygmailusername', 'mygmailpassword')
```

but honestly, do you want to have your password written in your script?

### Install

For Python 2.x and Python 3.x respectively:

```python
pip install yagmail
pip3 install yagmail
```

### Add yagmail to your keyring

[keyring quoted](https://pypi.python.org/pypi/keyring#what-is-python-keyring-lib):
> The Python `keyring` lib provides a easy way to access the system keyring service from python. It can be used in any application that needs safe password storage. 

You know you want it. Set it up by running once:

```python
yagmail.register('mygmailusername', 'mygmailpassword')
```

In fact, it is just a wrapper for `keyring.set_password('yagmail', 'mygmailusername', 'mygmailpassword')`.

### Start a connection

```python
yag = yagmail.Connect('mygmailusername')
```

Note that this connection is reusable, closable and when it leaves scope will auto-destroy.

### Usability 

Defining some variables:

```python
to = 'santa@someone.com'
to2 = 'easterbunny@someone.com
to3 = 'sky@pip-package.com'
subject = 'This is obviously the subject'
body = 'This is obviously the body'
html = '<a href="https://pypi.python.org/pypi/sky/">Click me!</a>'
img = '/local/file/bunny.png'
```

All variables are optional, and know that not even `To` is required (you'll send an email to yourself):

```python
yag.send(To = to, Subject = subject, Body = body)
yag.send(To = to, Subject = subject, Body = body, Html = html, Image = img)
yag.send(To = to, Image = img)
```

Furthermore, if you do not want to be explicit, you can do the following:

```python
yag.send(to, subject, body)
yag.send(to, subject, body, img)
```

And lastly, it is also possible to send to a group of people by providing a list of email strings rather than a single string:

```python
yag.send([to, to2, to3], subject, body)
```

Actually, all arguments can be missing or lists. Pretty much the table summarizes:

Type/Amount   |None|String|Flat iterable (set/list/etc)
---|---|---|---
To|To = Self|Value|join (";")
Subject|Nothing|Value|join (" ")
Body|Nothing|Value|join (" ")
Attach|Nothing|Value|Separated

Furthermore, attachments will be smartly guessed. (Soon, To be continued)

Attachment By|Filename|URL|String
---|---|---|---
Html|Yes|Yes|Yes
Image|Yes|Yes|No

### Roadmap (and priorities)

- ~~Added possibility of Image~~
- ~~Attachment counter~~
- ~~Optional SMTP arguments should go with magic to my Connect~~
- ~~CC/BCC (high)~~
- ~~Custom names (high)~~
- ~~Allow send to return a preview rather than to actually send~~
- Perhaps change the casing of the arguments... (needs thought)
- Choose inline or not somehow (needs thought)
- Just attachments, being smart guessed (high, complex)
- Attachments in a list so they actually define the order (medium)
- Provide automatic fallback for html etc (low)
- Extra other types (low)
- Mail counter (low)
- Logging count & mail capability (very low)

### Errors

- Make sure you have a keyring entry (see section [Add yagmail to your keyring](add-yagmail-to-your-keyring))

- [`smtplib.SMTPException: SMTP AUTH extension not supported by server`](http://stackoverflow.com/questions/10147455/trying-to-send-email-gmail-as-mail-provider-using-python)

- [`SMTPAuthenticationError: Application-specific password required`](https://support.google.com/accounts/answer/185833)

- **YagAddressError**: This means that the address was given in an invalid format. Note that `From` can either be a string, or a dictionary where the key is an `email`, and the value is an `alias` {'sample@gmail.com', 'Sam'}. In the case of 'To', it can either be a string (`email`), a list of emails (email addresses without aliases) or a dictionary where keys are the email addresses and the values indicate the aliases.

- Make sure you have a connection

- I only suppose it will work for gmail
