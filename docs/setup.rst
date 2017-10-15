Setup
=====
This page shows you how to install ``yagmail`` and
how to set it up to use your system keyring service.


Installing from PyPI
--------------------
The usual way of installing ``yagmail`` is through PyPI.
It is recommended to install it together with the ``keyring``
library, by running the following (for Python 2.x and 3.x respectively)::

    pip install yagmail[all]
    pip3 install yagmail[all]

If installing ``yagmail`` with ``keyring`` causes issues,
omit the ``[all]`` to install it without.


Installing from GitHub
----------------------
If you're not scared of things occasionally breaking, you can also
install directly from the GitHub `repository <https://github.com/kootenpv/yagmail>`_.
You can do this by running the following (for Python 2.x and 3.x respectively)::

    pip install -e git+https://github.com/kootenpv/yagmail#egg=yagmail[all]
    pip3 install -e git+https://github.com/kootenpv/yagmail#egg=yagmail[all]

Just like with the PyPI installation method, if installing with ``keyring``
causes issues, simply omit the ``[all]`` to install ``yagmail`` without it.

.. _configuring_credentials:

Configuring Credentials
-----------------------
While it's possible to put the username and password for your
E-Mail address into your script, ``yagmail`` enables you to omit both.
Quoting from ``keyring``\s `README <https://github.com/jaraco/keyring#what-is-python-keyring-lib>`_::

    What is Python keyring lib?

    The Python keyring lib provides a easy way to access the system
    keyring service from python. It can be used in any
    application that needs safe password storage.

If this sparked your interest, set up a Python interpreter and run
the following to register your GMail credentials with ``yagmail``:

.. code-block:: python

    import yagmail
    yagmail.register('mygmailusername', 'mygmailpassword')

(this is just a wrapper for ``keyring.set_password('yagmail', 'mygmailusername', 'mygmailpassword')``)
Now, instantiating :class:`yagmail.SMTP` is as easy as doing:

.. code-block:: python

    yag = yagmail.SMTP('mygmailusername')

If you want to also omit your username, you can create a ``.yagmail``
file in your home folder, containing just your username. Then, you can
instantiate the SMTP client without passing any arguments.


Using OAuth2
------------
Another fairly safe method for authenticating using OAuth2, since
you can revoke the rights of tokens. In order to use OAuth2, pass
the location of the credentials file to :class:`yagmail.SMTP`:

.. code-block:: python

    yag = yagmail.SMTP('user@gmail.com', oauth2_file='~/oauth2_creds.json')
    yag.send(subject="Great!")

If the file could not be found, then it will prompt for a
``google_client_id`` and ``google_client_secret``. You can obtain these
on `this OAauth2 Guide <http://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html>`_,
upon which the OAauth2 code of ``yagmail`` is heavily based.
After you have provided these, a link will be shown in the terminal that
you should follow to obtain a ``google_refresh_token``.
Paste this again, and you're set up!

If somebody obtains the file, they can send E-Mails, but nothing else.
As soon as you notice, you can simply disable the token.