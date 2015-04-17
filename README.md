# yagmail -- Yet Another GMAIL client

The simple goal here is to make it as simple and painless as possible to send an email.

In the end, your code will look something like this:

```python
import yagmail
yag = yagmail.Mail('mygmailusername')
yag.send('to@someone.com', 'subject', 'body')
```

Note that it will read the password securely from your keyring (read below). If you don't want this, even though you know you want it, you can also initialize with:

```python
yag = yagmail.Mail('mygmailusername', 'mygmailpassword')
```

but honestly, do you want to have your password written in your script?

### Install

For Python 2.x and Python 3.x respectively:

```python
pip install yagmail
pip3 install yagmail
```

### Add yagmail to your keyring

[keyring quoted](https://pypi.python.org/pypi/keyring#what-is-python-keyring-lib): The Python `keyring` lib provides a easy way to access the system keyring service from python. It can be used in any application that needs safe password storage. 

You know you want it. Set it up by running once:

```python
yagmail.register('mygmailusername', 'mygmailpassword')
```

In fact, it is just a wrapper for `keyring.set_password('yagmail', 'mygmailusername', 'mygmailpassword')`.

### Start a connection

```python
yag = yagmail.Mail('mygmailusername')
```

Note that this connection is reusable.

### Usability 

Defining some variables:

```python
to = 'santa@someone.com'
to2 = 'easterbunny@someone.com
to3 = 'sky@pip-package.com'
subject = 'This is obviously the subject'
body = 'This is obviously the body'
html = '<a href="https://pypi.python.org/pypi/sky/">Click me!</a>'
```

Note that only `To` is required, the rest of the options are optional (`subject`, `body`, `html`)

```python
yag.send(To = to, Subject = subject, Body = body)
yag.send(To = to, Subject = subject, Body = body, Html = html)
yag.send(To = to, Html = html)
```

Furthermore, if you do not want to be explicit, you can do the following:

```python
yag.send(to, subject, body)
yag.send(to, subject, body, html)
```

And lastly, it is also possible to send to a group of people by providing a list of email strings rather than a single string:

```python
yag.send([to, to2, to3], subject, body)
yag.send([to, to2, to3], subject, body)
```

### Roadmap (and priorities)

- Add images/video/other types (medium)
- Logging capability (low)

### Errors

- Make sure you have a keyring entry (see section [Add yagmail to your keyring](add-yagmail-to-your-keyring))

- [`smtplib.SMTPException: SMTP AUTH extension not supported by server`](http://stackoverflow.com/questions/10147455/trying-to-send-email-gmail-as-mail-provider-using-python)

- Make sure you have a connection

- I only suppose it will work for gmail