import logging
import time
import os
import keyring
import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.encoders
import mimetypes
import requests

from .error import YagConnectionClosed
from .error import YagAddressError
from .error import YagInvalidEmailAddress

from .validate import validate_email_with_regex

from .log import getLogger

try:
    import lxml.html
except ImportError:
    pass 

class Connect():
    """ Connection is the class that contains the SMTP connection and allows messages to be send """

    def __init__(self, user = None, password = None, host = 'smtp.gmail.com', port = '587',
                 smtp_starttls = True, smtp_set_debuglevel = 0, **kwargs):
        self.log = getLogger()
        self.set_logging()
        if user is None:
            user = self._find_user_home_path()
        self.user, self.userName = self._make_addr_alias_user(user)
        self.isClosed = None
        self.host = host
        self.port = port
        self.starttls = smtp_starttls
        self.debuglevel = smtp_set_debuglevel
        self.kwargs = kwargs
        self.login(password)
        self.cache = {}
        self.unsent = [] 
        self.log.info('Connected to SMTP @ %s:%s as %s', self.host, self.port, self.user)
        self.num_mail_sent = 0

    def set_logging(self, log_level = logging.ERROR, file_path_name = None):
        """ 
        This function allows to change the logging backend, either output or file as backend 
        It also allows to set the logging level (whether to display only critical, error, info or debug.
        e.g.
        yag = yagmail.Connect()
        yag.setLogging(yagmail.logging.DEBUG)  # to see everything

        and 

        yagmail.setLogging(yagmail.logging.DEBUG, 'somelocalfile.log')

        lastly, a log_level of None will make sure there is no I/O.
        """
        self.log = getLogger(log_level, file_path_name)
        
    def send(self, to = None, subject = None, contents = None, attachments = None, cc = None, bcc = None,
             previewOnly=False, useCache=False, validate_email = True, throw_invalid_exception = False):
        """ Use this to send an email with gmail"""
        addresses = self._resolveAddresses(to, cc, bcc, validate_email, throw_invalid_exception)
        if not addresses['recipients']:
            return {}
        msg = self._prepare_message(addresses, subject, contents, attachments, useCache)
        if previewOnly:
            return addresses, msg.as_string()
        return self._attempt_send(addresses['recipients'], msg.as_string())

    def _attempt_send(self, recipients, msgString): 
        attempts = 0
        while attempts < 3:
            try:
                result = self.smtp.sendmail(self.user, recipients, msgString)
                self.log.info('Message sent to %s', recipients)
                self.num_mail_sent += 1
                return result
            except smtplib.SMTPServerDisconnected as e:
                self.log.error(e)
                attempts += 1
                time.sleep(attempts * 3)
        self.unsent.append((recipients, msgString))
        return False

    def send_unsent(self):
        """ 
        Emails that were not being able to send will be stored in self.unsent. 
        Use this function to attempt to send these again
        """
        for i in range(len(self.unsent)):
            recipients, msgString = self.unsent.pop(i)
            self._attempt_send(recipients, msgString)
        
    def close(self):
        """ Close the connection to the SMTP server """
        self.isClosed = True 
        self.smtp.quit()
        self.log.info('Closed SMTP @ %s:%s as %s', self.host, self.port, self.user)

    def login(self, password):
        """ 
        Login to the SMTP server using password. 
        This only needs to be manually run when the connection to the SMTP server was closed by the user.
        """
        self.smtp = smtplib.SMTP(self.host, self.port, **self.kwargs)
        self.smtp.set_debuglevel(self.debuglevel)
        if self.starttls is not None:
            self.smtp.ehlo()
            if self.starttls:
                self.smtp.starttls()
            else:
                self.smtp.starttls(**self.starttls)
            self.smtp.ehlo()
        if password is None:
            password = keyring.get_password('yagmail', self.user)
            if '@' not in self.user:
                self.user += '@gmail.com'
            if password is None:
                password = keyring.get_password('yagmail', self.user)
            if password is None:
                import getpass
                password = getpass.getpass('Password for <{}>: '.format(self.user))
                answer = ''
                # Python 2 fix
                try: 
                    input = raw_input 
                except NameError: 
                    pass
                while answer != 'y' and answer != 'n':
                    answer = input('Save username and password in keyring? [y/n]: ').strip()
                if answer == 'y':    
                    register(self.user, password)    
        self.smtp.login(self.user, password)
        self.isClosed = False

    def _resolveAddresses(self, to, cc, bcc, validate_email, throw_invalid_exception):
        """ Handle the targets addresses, adding aliases when defined """
        addresses = {'recipients': []}
        if to is not None:
            self._make_addr_alias_target(to, addresses, 'to')
        elif cc is not None and bcc is not None:
            self._make_addr_alias_target([self.user, self.userName], addresses, 'to')
        else:
            addresses['recipients'].append(self.user)
        if cc is not None:
            self._make_addr_alias_target(cc, addresses, 'cc')
        if bcc is not None:
            self._make_addr_alias_target(bcc, addresses, 'bcc')
        if validate_email:
            for email_addr in addresses['recipients']:
                try:
                    validate_email_with_regex(email_addr)
                except YagInvalidEmailAddress as e:
                    if throw_invalid_exception:
                        raise e
                    else:
                        self.log.error(e)
                        addresses['recipients'].remove(email_addr)
        return addresses

    def _prepare_message(self, addresses, subject, contents, attachments, useCache):
        """ Prepare a MIME message """
        if self.isClosed:
            raise YagConnectionClosed('Login required again')
        hasEmbeddedImage, contentObjects = self._prepare_contents(contents, useCache)
        msg = MIMEMultipart()
        msgAlternative = MIMEMultipart('alternative')
        msg.attach(msgAlternative)
        self._add_subject(msg, subject)
        self._add_recipients(msg, addresses)
        if hasEmbeddedImage:
            msg.preamble = "You need a MIME enabled mail reader to see this message."
        if contents is not None:    
            for contentObject, contentString in zip(contentObjects, contents):
                if contentObject['main_type'] == 'image':
                    if isinstance(contentString, dict):
                        for x in contentString:
                            hashed_ref = contentString[x]
                    else:
                        hashed_ref = str(abs(hash(os.path.basename(contentString))))
                    msgImgText = MIMEText('<img src="cid:{}" title="{}"/>'.format(hashed_ref, hashed_ref), 'html')
                    contentObject['mimeObject'].add_header('Content-ID', '<{}>'.format(hashed_ref)) 
                    msgAlternative.attach(msgImgText) 
                    email.encoders.encode_base64(contentObject['mimeObject']) 
                msg.attach(contentObject['mimeObject'])
        if attachments or attachments is None:
            pass
        # attachments = self._prepare_attachments(msg, attachments, useCache)
        return msg

    def _prepare_attachments(self, msg, attachments, useCache):
        pass

    def _prepare_contents(self, contents, useCache):
        mimeObjects = []
        hasEmbeddedImage = False
        if contents is not None:
            if isinstance(contents, str):
                contents = [contents]
            for content in contents:
                if useCache: 
                    if content not in self.cache:
                        contentObject = self._get_mime_object(content)
                        self.cache[content] = contentObject
                    contentObject = self.cache[content]
                else:
                    contentObject = self._get_mime_object(content)
                if contentObject['main_type'] == 'image': 
                    hasEmbeddedImage = True
                mimeObjects.append(contentObject)
        return hasEmbeddedImage, mimeObjects

    def _add_recipients(self, msg, addresses):
        msg['user'] = self.userName
        if 'To' in addresses:
            msg['To'] = addresses['To']
        else:
            msg['To'] = self.userName
        if 'cc' in addresses:
            msg['Cc'] = addresses['cc']
        if 'bcc' in addresses:
            msg['Bcc'] = addresses['bcc']

    @staticmethod        
    def _find_user_home_path():
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()

    @staticmethod        
    def _make_addr_alias_user(x):
        if isinstance(x, str):
            return (x, x)
        if isinstance(x, dict):
            if len(x) == 1:
                return (list(x.keys())[0], list(x.values())[0])
        raise YagAddressError

    @staticmethod
    def _make_addr_alias_target(x, addresses, which):
        if isinstance(x, str):
            addresses['recipients'].append(x)
            addresses['To'] = x
            return addresses
        if isinstance(x, list) or isinstance(x, tuple):
            if not all([isinstance(k, str) for k in x]):
                raise YagAddressError
            addresses['recipients'].extend(x)
            addresses[which] = '; '.join(x)
            return addresses
        if isinstance(x, dict):
            addresses['recipients'].extend(x.keys())
            addresses[which] = '; '.join(x.values())
            return addresses
        raise YagAddressError

    @staticmethod        
    def _add_subject(msg, Subject):
        if not Subject:
            return
        if isinstance(Subject, list):
            Subject = ' '.join(Subject)
        msg['Subject'] = Subject

    @staticmethod        
    def _get_mime_object(contentString):
        contentObject = {'mimeObject': None, 'encoding': None, 'main_type': None, 'sub_type': None} 
        if isinstance(contentString, dict):
            for x in contentString:
                contentString, contentName = x, contentString[x]
        else:
            contentName = os.path.basename(contentString)        
        if os.path.isfile(contentString):
            try:
                with open(contentString) as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(contentString, 'rb') as f:
                    content = f.read()
        else:
            try:
                r = requests.get(contentString)
                # pylint: disable=protected-access
                # Used to obtain the raw content of requests object
                content = r._content
                if 'content-type' in r.headers:
                    main_type, sub_type = r.headers['content-type'].split('/')
                    contentObject['main_type'] = main_type
                    contentObject['sub_type'] = sub_type
            except (IOError, ValueError, requests.exceptions.MissingSchema):
                contentObject['main_type'] = 'text'
                try:
                    html_tree = lxml.html.fromstring(contentString)
                    if html_tree.find('.//*') is not None or html_tree.tag != 'p':
                        contentObject['mimeObject'] = MIMEText(contentString, 'html')
                        contentObject['sub_type'] = 'html'
                    else:
                        contentObject['mimeObject'] = MIMEText(contentString)
                except NameError: 
                    contentObject['mimeObject'] = MIMEText(contentString) 
                if contentObject['sub_type'] is None:
                    contentObject['sub_type'] = 'plain'
                return contentObject

        if contentObject['main_type'] is None:
            content_type, content_encoding = mimetypes.guess_type(contentString)
            contentObject['encoding'] = content_encoding

            if content_type is not None:
                contentObject['main_type'], contentObject['sub_type'] = content_type.split('/')

        if contentObject['main_type'] is None or contentObject['encoding'] is not None:
            contentObject['main_type'] = 'application'
            contentObject['sub_type'] = 'octet-stream'

        mimeObject = MIMEBase(contentObject['main_type'], contentObject['sub_type'], name = contentName)
        mimeObject.set_payload(content) 
        contentObject['mimeObject'] = mimeObject
        return contentObject

    def feedback(self, message = "Awesome features! You made my day! How can I contribute? Winter is coming."):
        """ Most important function. Please send me feedback :-) """
        self.send('kootenpv@gmail.com', 'Yagmail feedback', message)
        
    def __del__(self): 
        """ When the object leaves scope / gets destroyed, it will neatly cleanup and log it"""
        self.close() 
        self.log.info('Deleted SMTP @ %s:%s as %s', self.host, self.port, self.user)


def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail"""
    keyring.set_password('yagmail', username, password)


def main():
    """ This is the function that is run from commandline with `yagmail` """ 
    import argparse
    parser = argparse.ArgumentParser(description='Send a (g)mail with yagmail.') 
    parser.add_argument('-to', '-t', help='Send an email to address "TO"', nargs='+') 
    parser.add_argument('-subject', '-s', help='Subject of email', nargs='+') 
    parser.add_argument('-contents', '-c', help='Contents to send', nargs='+') 
    parser.add_argument('-user', '-u', help='Username') 
    parser.add_argument('-password', '-p', help='Preferable to use keyring rather than password here') 
    args = parser.parse_args() 
    Connect(args.user, args.password).send(to = args.to, subject = args.subject, contents = args.contents)
