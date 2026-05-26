API Reference
=============
This page displays a full reference of `yagmail`\'s API.


Authentication
--------------

.. autofunction:: yagmail.register

Another way of authenticating is by passing an ``oauth2_file`` to
:class:`yagmail.Client` (or :class:`yagmail.AsyncClient`), which is among the safest methods of authentication.
Please see the `OAuth2 section <https://github.com/kootenpv/yagmail#oauth2>`_
of the `README <https://github.com/kootenpv/yagmail/blob/master/README.md>`_
for further details.

It is also possible to simply pass the password to :class:`yagmail.Client` / :class:`yagmail.AsyncClient`.
If no password is given, yagmail will prompt the user for a password and
then store the result in the keyring.


Mail Clients
------------

.. autoclass:: yagmail.Client
   :members:

.. autoclass:: yagmail.AsyncClient
   :members:


E-Mail Contents
---------------
.. autoclass:: yagmail.raw

.. autoclass:: yagmail.inline


Exceptions
----------
.. automodule:: yagmail.error
   :members:


Utilities
-----------------
.. autofunction:: yagmail.validate.validate_email_with_regex
