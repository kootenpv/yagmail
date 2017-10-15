Usage
=====
This document aims to show how to use ``yagmail`` in your programs.
Most of what is shown here is also available to see in the
`README <https://github.com/Volcyy/yagmail>`_, some content may be
duplicated for completeness.


Start a Connection
------------------
As mentioned in :ref:`configuring_credentials`, there
are three ways to initialize a connection by instantiating
:class:`yagmail.SMTP`:

1. **With Username and Password**:
e.g. ``yagmail.SMTP('mygmailusername', 'mygmailpassword')``
This method is not recommended, since you would be storing
the full credentials to your account in your script in plain text.
A better alternative is using ``keyring``, as described in the
following section:

2. **With Username and keyring**:
After registering a ``keyring`` entry for ``yagmail``, you can
instantiate the client by simply passing your username, e.g.
``yagmail.SMTP('mygmailusername')``.

3. **With keyring and .yagmail**:
As explained in the `Setup` documentation, you can also
omit the username if you have a ``.yagmail`` file in your
home folder, containing just your GMail username. This way,
you can initialize :class:`yagmail.SMTP` without any arguments.

4. **With OAuth2**:
This is probably the safest method of authentication, as you
can revoke the rights of tokens. To initialize with OAuth2
credentials (after obtaining these as shown in `Setup`),
simply pass an ``oauth2_file`` to :class:`yagmail.SMTP`,
for example ``yagmail.SMTP('user@gmail.com', oauth2_file='~/oauth2_creds.json')``.


Closing and reusing the Connection
----------------------------------
By default, :class:`yagmail.SMTP` will clean up after itself
**in CPython**. This is an implementation detail of CPython and as such
may not work in other implementations such as PyPy (reported in
`issue #39 <https://github.com/kootenpv/yagmail/issues/39>`_). In those
cases, you can use :class:`yagmail.SMTP` with ``with`` instead.

Alternatively, you can close and re-use the connection with
:meth:`yagmail.SMTP.close` and :meth:`yagmail.SMTP.login` (or
:meth:`yagmail.SMTP.oauth2_file` if you are using OAuth2).


Sending E-Mails
---------------
:meth:`yagmail.SMTP.send` is a fairly versatile method that allows
you to adjust more or less anything about your Mail.
First of all, all parameters for :meth:`yagmail.SMTP.send` are optional.
If you omit the recipient (specified with ``to``), you will send an
E-Mail to yourself.

Since the use of the (keyword) arguments of :meth:`yagmail.SMTP.send`
are fairly obvious, they will simply be listed here:

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
The ``contents`` argument of :meth:`yagmail.SMTP.send` will be smartly guessed.
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


Using yagmail from the command line
-----------------------------------
``yagmail`` includes a command-line application, simply called with ``yagmail``
after you installed it. To view a full reference on how to use this, run
``yagmail --help``.
