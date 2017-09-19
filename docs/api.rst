API Reference
=============
This page displays a full reference of `yagmail`\'s API.


Authentication
--------------
The recommended way to use authenticate is through using
`keyring <https://pypi.python.org/pypi/keyring#what-is-python-keyring-lib>`_
through ``yagmail.register``:

.. autofunction:: yagmail.register

Another way of authenticating is by passing an ``oauth2_file`` to
:class:`yagmail.SMTP`, which is among the safest methods of authentication.
Please see the `OAuth2 section <https://github.com/kootenpv/yagmail#oauth2>`_
of the `README <https://github.com/kootenpv/yagmail/blob/master/README.md>`_
for further details.

It is also possible to simply pass the password to :class:`yagmail.SMTP`,
although this option is not recommended.

If no password is given, yagmail will prompt the user for a password and
then store the result in the keyring.


SMTP Client
-----------
.. autoclass:: yagmail.SMTP
   :members:


E-Mail Contents
---------------
.. autoclass:: yagmail.raw

.. autoclass:: yagmail.inline


Exceptions
----------
.. automodule:: yagmail.error
   :members:
