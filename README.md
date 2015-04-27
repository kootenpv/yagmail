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
yag.send(To = to, Subject = subject, Contents = body)
yag.send(To = to, Subject = subject, Contents = [body, html, img])
yag.send(Contents = [body, img])
```

Furthermore, if you do not want to be explicit, you can do the following:

```python
yag.send(to, subject, [body, img])
```

## Recipients

And lastly, it is also possible to send to a group of people by providing a list of email strings rather than a single string:

```python
yag.send(To = to) 
yag.send(To = [to, to2]) # List or tuples for emailadresses *without* aliases
yag.send(To = {to : 'Alias1'}) # Dictionary for emailaddress *with* aliases
yag.send(To = {to : 'Alias1', to2 : 'Alias2'}
```

**All arguments are optional when sending.**

Furthermore, the `Contents` argument will be smartly guessed. It can be passed a string (which will be turned into a list); or a list. For each object in the list:

- It will try to see if the string can be read as a file locally,
- if impossible, it will try to visit the string as a URL,
- if impossible, it will check if the string is valid html
- if not, it must be text.

Local files require to have an extension for their content type to be inferred. I will see if I can add `python-magic` package an optional dependency to not rely on extension.

### Roadmap (and priorities)

- ~~Added possibility of Image~~
- ~~Attachment counter~~
- ~~Optional SMTP arguments should go with \**kwargs to my Connect~~
- ~~CC/BCC (high)~~
- ~~Custom names (high)~~
- ~~Allow send to return a preview rather than to actually send~~
- ~~Just use attachments in "contents", being smart guessed (high, complex)~~
- ~~Attachments (contents) in a list so they actually define the order (medium)~~
- ~~Use lxml to see if it can parse the html (low)~~
- Choose inline or not somehow (high)
- Make `lxml` optional magic (high)
- Provide automatic fallback for complex content(medium)
- Allow caching of content (low)
- Extra other types (low)
- Mail counter (low)
- Logging count & mail capability (very low)
- Add the local images to the package (lowest)

### Errors

- Make sure you have a keyring entry (see section [Add yagmail to your keyring](add-yagmail-to-your-keyring))

- [`smtplib.SMTPException: SMTP AUTH extension not supported by server`](http://stackoverflow.com/questions/10147455/trying-to-send-email-gmail-as-mail-provider-using-python)

- [`SMTPAuthenticationError: Application-specific password required`](https://support.google.com/accounts/answer/185833)

- **YagAddressError**: This means that the address was given in an invalid format. Note that `From` can either be a string, or a dictionary where the key is an `email`, and the value is an `alias` {'sample@gmail.com', 'Sam'}. In the case of 'To', it can either be a string (`email`), a list of emails (email addresses without aliases) or a dictionary where keys are the email addresses and the values indicate the aliases.

- **YagContentError**: It means that from the filename/url it is not possible to infer the type. I plan to allow the use of python-magic which can infer many more types, not just based on the filename/url.   

- Make sure you have a connection

- I only suppose it will work for gmail
