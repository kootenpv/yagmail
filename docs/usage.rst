Usage
=====
This document aims to show how to use ``yagmail`` in your programs.
Most of what is shown here is also available to see in the
`README <https://github.com/kootenpv/yagmail>`_, some content may be
duplicated for completeness.


Start a Connection
------------------
As mentioned in :ref:`configuring_credentials`, there are multiple ways to initialize a connection by instantiating :class:`yagmail.Client`:

1. **With Username and Password / App-Password**:
   e.g. ``yagmail.Client('mygmailusername', 'mygmailpassword')``
   This is the most straightforward method. If you do not want to hardcode your password, you can load it from environment variables or prompt for it.

2. **With Username and Keyring (Optional)**:
   If you have registered a keyring entry for ``yagmail`` (e.g. using ``yagmail.register('mygmailusername', 'mygmailpassword')``), you can omit the password and yagmail will securely load it from your OS keyring:
   ``yagmail.Client('mygmailusername')``

3. **With Configuration File (Optional)**:
   If you have a ``.yagmail`` configuration file containing your GMail username in your home folder, you can instantiate the client without passing any arguments:
   ``yagmail.Client()``

4. **With OAuth2**:
   This is the safest method of authentication, as you can easily revoke tokens. Pass an ``oauth2_file`` credentials file path:
   ``yagmail.Client('user@gmail.com', oauth2_file='~/oauth2_creds.json')``


Closing and reusing the Connection
----------------------------------
By default, :class:`yagmail.Client` will clean up after itself
**in CPython**. This is an implementation detail of CPython and as such
may not work in other implementations such as PyPy (reported in
`issue #39 <https://github.com/kootenpv/yagmail/issues/39>`_). In those
cases, you can use :class:`yagmail.Client` with ``with`` instead.

For asynchronous use, you can use the async context manager of :class:`yagmail.AsyncClient`. Below is a complete, copy-pasteable example of sending an email asynchronously:

.. code-block:: python

    import asyncio
    import yagmail

    async def main():
        # Use AsyncClient as an async context manager
        async with yagmail.AsyncClient('mygmailusername', 'mygmailpassword') as yag:
            contents = [
                "This is the body of the async email.",
                "/local/path/to/song.mp3"
            ]
            await yag.send('to@someone.com', 'subject', contents)

    asyncio.run(main())

Alternatively, you can close and re-use the connection with
:meth:`yagmail.Client.close` and :meth:`yagmail.Client.login` (or
``aclose()`` and ``login()`` for :class:`yagmail.AsyncClient`).


Sending E-Mails
---------------
:meth:`yagmail.Client.send` (or :meth:`yagmail.AsyncClient.send`) is a fairly versatile method that allows
you to adjust more or less anything about your Mail.
First of all, all parameters are optional.
If you omit the recipient (specified with ``to``), you will send an
E-Mail to yourself.

Since the use of the (keyword) arguments are fairly obvious, they will simply be listed here:

- ``to``
- ``subject``
- ``contents``
- ``attachments``
- ``cc``
- ``bcc``
- ``preview_only``
- ``headers``

Some of these - namely ``to`` and ``contents`` - have some magic
associated with them which will be outlined in the following sections.


E-Mail recipients
-----------------
You can send an E-Mail to a single user by simply passing
a string with either a GMail username (``@gmail.com`` will be appended
automatically), or with a full E-Mail address:

.. code-block:: python

    yag.send(to='mike@gmail.com', contents="Hello, Mike!")

Alternatively, you can send E-Mails to a group of people by either passing
a list or a tuple of E-Mail addresses as ``to``:

.. code-block:: python

    yag.send(to=['to@someone.com', 'for@someone.com'], contents="Hello there!")

These E-Mail addresses were passed without any aliases.
If you wish to use aliases for the E-Mail addresses, provide a
dictionary mapped in the form ``{address: alias}``, for example:

.. code-block:: python

    recipients = {
        'aliased@mike.com': 'Mike',
        'aliased@fred.com': 'Fred'
    }
    yag.send(to=recipients, contents="Hello, Mike and Fred!")


Magical ``contents``
--------------------
The ``contents`` argument of :meth:`yagmail.Client.send` will be smartly guessed.
You can pass it a string with your contents or a list of elements which are either:

- If it is a **dictionary**, then it will be assumed that the key is the content and the value is an alias (currently, this only applies to images). For example:


.. code-block:: python

    contents = [
        "Hello Mike! Here is a picture I took last week:",
        {'path/to/my/image.png': 'PictureForMike'}
    ]

- If it is a **string**, then it will first check whether the content of the string can be **read as a file** locally, for example ``'path/to/my/image.png'``. These files require an extension for their content type to be inferred.

- If it could not be read locally, then it checks whether the string is valid HTML, such as ``<h1>This is a big title!</h1>``.

- If it was not valid HTML either, then it must be text, such as ``"Hello, Mike!"``.

If you want to **ensure that a string is treated as text** and should not be checked
for any other content as described above, you can use :class:`yagmail.raw`, a subclass
of :class:`str`.

If you intend to **inline an image instead of attaching it**, you can use
:class:`yagmail.inline`.


Attaching Files
---------------
There are multiple ways to attach files using the ``attachments`` parameter (in addition to the magical ``contents`` parameter):

1. **Pass a List of Paths**:
   You can pass a list of local file paths as a list of strings:

.. code-block:: python

    yag.send(
        to='to@someone.com',
        subject='File Attachments',
        contents='Here are the files you requested.',
        attachments=['path/to/attachment1.png', 'path/to/attachment2.pdf']
    )

2. **Pass an IO Stream**:
   You can pass an instance of :class:`io.IOBase` (such as a file object):

.. code-block:: python

    with open('path/to/attachment.pdf', 'rb') as f:
        yag.send(
            to='to@someone.com',
            subject='File Attachments',
            contents='Attached is the PDF.',
            attachments=f
        )

.. note::
    When passing an IO stream, ``yagmail`` will look for the ``.name`` attribute to determine the filename and detect the MIME-type. If your IO stream does not have a ``.name`` attribute, it is highly recommended to set it manually (e.g., ``f.name = 'document.pdf'``) to avoid attachments being named generic names like ``attachment1`` without an extension.


DKIM Support
------------
To send emails signed with a DKIM signature, you will first need to install the package with all optional dkim dependencies:

.. code-block:: bash

    pip install yagmail[dkim]

Then, configure and pass a :class:`yagmail.dkim.DKIM` configuration object to your client instance:

.. code-block:: python

    from yagmail import Client
    from yagmail.dkim import DKIM
    from pathlib import Path

    # Load private key bytes
    private_key = Path("privkey.pem").read_bytes()

    dkim_obj = DKIM(
        domain=b"example.com",
        selector=b"selector",
        private_key=private_key,
        include_headers=[b"To", b"From", b"Subject"] # Or pass None for defaults
    )

    yag = Client(dkim=dkim_obj)
    yag.send(to="to@someone.com", subject="DKIM Signed Email", contents="Hi!")


Stability & Concurrency
-----------------------

Auto-reconnect on Disconnect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both the synchronous ``Client`` and asynchronous ``AsyncClient`` feature automatic reconnection. If the SMTP server drops the connection (raising ``SMTPServerDisconnected``) during a send operation, ``yagmail`` will catch the exception, automatically log back in, and retry sending the email up to 3 times before giving up.

Concurrency & Thread-safety
~~~~~~~~~~~~~~~~~~~~~~~~~~~
In asynchronous scripts, you can share a single ``AsyncClient`` instance across concurrent tasks safely. The client implements internal asynchronous locks (``send_lock`` and ``login_lock``) to serialize access to the underlying socket connection, preventing race conditions or interleaved data blocks during simultaneous email transmissions.


Using yagmail from the command line
-----------------------------------
``yagmail`` includes a command-line application, simply called with ``yagmail``
after you installed it. To view a full reference on how to use this, run
``yagmail --help``.
