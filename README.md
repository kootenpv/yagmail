# yagmail -- Yet Another GMAIL client

The simple goal here is to make it as simple and painless as possible to send an email.

In the end, your code will look like this:

```python
import yagmail
yag = yagmail.Mail('gmailusername')
yag.send('to@someone.com', 'subject', 'body')
```

### Start a connection

```python
yag = yagmail.Mail('kootenpv')
```

Note that this connection is reusable.

### Usability 

Defining some variables:

```python
to = 'to@someone.com'
to2 = 'another@someone.com
subject = 'This is obviously the subject'
body = 'This is obviously the body'
html = '<a href="https://pypi.python.org/pypi/yagmail/">Click me!</a>'
```

Note that only `To` is required, the rest of the options are optional (`subject`, `body`, `html`)

```python
yag.send(To = to, Subject = subject, Body = body)
yag.send(To = to, Subject = subject, Body = body, Html = html)
yag.send(To = to, Html = html)
```

Furthermore, if you want do not want to be explicit, you can do the following:

```python
yag.send(to, subject, body)
yag.send(to, subject, body, html)
```

And lastly, it is also possible to send to a group of people by providing a list of email strings rather than a single string:

```python
yag.send([to, to2], subject, body)
yag.send([to, to2], subject, body)
```

### Errors

- Make sure you have a keyring entry. This is how you can do it for example (only required once):

```python
import keyring
keyring.set_password('yagmail', 'mygmailusername', 'mypassword')
```

- Make sure you have a connection

- I only suppose it will work for gmail