yagmail - Yet another GMAIL / SMTP client
=========================================
`yagmail` is a GMAIL/SMTP client that aims to
make it as simple as possible to send emails.

Sending an Email is as simple:

.. code-block:: python

    import yagmail
    yag = yagmail.SMTP()
    contents = [
        "This is the body, and here is just text http://somedomain/image.png",
        "You can find an audio file attached.", '/local/path/to/song.mp3'
    ]
    yag.send('to@someone.com', 'subject', contents)

    # Alternatively, with a simple one-liner:
    yagmail.SMTP('mygmailusername').send('to@someone.com', 'subject', contents)

Note that yagmail will read the password securely from
your keyring, see the section on
`Username and Password in the repository's README
<https://github.com/kootenpv/yagmail#username-and-password>`_
for further details. If you do not want this, you can
initialize ``yagmail.SMTP`` like this:

.. code-block:: python

    yag = yagmail.SMTP('mygmailusername', 'mygmailpassword')

but honestly, do you want to have your
password written in your script?

For further documentation and examples,
please go to https://github.com/kootenpv/yagmail.

The full documentation is available at
http://yagmail.readthedocs.io/en/latest/.
