import os
import keyring
import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.encoders
import mimetypes
import lxml.html
import requests

class UserNotFoundInKeyring(Exception):
    pass

class YagConnectionClosed(Exception):
    pass

class YagAddressError(Exception):
    pass

class YagContentError(Exception):
    pass


class Connect():
    """ Connection is the class that contains the smtp"""
    def __init__(self, From = None, password = None, host = 'smtp.gmail.com', port = '587', 
                 starttls = True, set_debuglevel = 0, **kwargs): 
        if From is None: 
            From = self._findUserFromHome()
        self.From, self.FromName = self._makeAddrAliasFrom(From)
        self.isClosed = None 
        self.host = host
        self.port = port
        self.starttls = starttls
        self.debuglevel = set_debuglevel
        self.kwargs = kwargs
        self.login(password)
        self.cache = {} 
                
    def send(self, To = None, Subject = None, Contents = None, Cc = None, Bcc = None,
             previewOnly = False, useCache = False): 
        """ Use this to send an email with gmail""" 
        addresses = self._resolveAddresses(To, Cc, Bcc)        
        msg = self._prepareMsg(addresses, Subject, Contents, useCache)
        if previewOnly: 
            return addresses, msg.as_string() 
        else: 
            return self.smtp.sendmail(self.From, addresses['recipients'], msg.as_string())

    def close(self):
        self.isClosed = True
        self.smtp.quit()

    def login(self, password):
        self.smtp = smtplib.SMTP(self.host, self.port, **self.kwargs) 
        self.smtp.set_debuglevel(self.debuglevel)
        if self.starttls is not None:
            self.smtp.ehlo()
            if self.starttls == True:
                self.smtp.starttls()
            else:
                self.smtp.starttls(**self.starttls)     
            self.smtp.ehlo()
        if password is None:
            password = keyring.get_password('yagmail', self.From)
            if '@' not in self.From:
                self.From += '@gmail.com'
            if password is None: 
                password = keyring.get_password('yagmail', self.From) 
            if password is None: 
                exceptionMsg = 'Either yagmail is not listed in keyring, or the user + password is not defined.'
                raise UserNotFoundInKeyring(exceptionMsg)
        self.smtp.login(self.From, password)
        self.isClosed = False        
        
    def _resolveAddresses(self, To = None, Cc = None, Bcc = None): 
        addresses = {'recipients' : []} 
        if To is not None: 
            self._makeAddrAliasTarget(To, addresses, 'To') 
        elif Cc is not None and Bcc is not None: 
            self._makeAddrAliasTarget([self.From, self.FromName], addresses, 'To')
        else:
            addresses['recipients'].append(self.From)     
        if Cc is not None:
            self._makeAddrAliasTarget(Cc, addresses, 'Cc')                
        if Bcc is not None:
            self._makeAddrAliasTarget(Bcc, addresses, 'Bcc')    
        return addresses        
        
    def _prepareMsg(self, addresses, Subject = None, Contents = None, useCache = False):
        if self.isClosed:
            raise YagConnectionClosed('Login required again') 
        msg = MIMEMultipart() 
        self._addSubject(msg, Subject)
        msg['From'] = self.FromName
        if 'To' in addresses: 
            msg['To'] = addresses['To']
        else:
            msg['To'] = self.FromName    
        if 'Cc' in addresses:
            msg['Cc'] = addresses['Cc']
        if 'Bcc' in addresses:
            msg['Bcc'] = addresses['Bcc']
        if Contents is not None:    
            if isinstance(Contents, str):
                Contents = [Contents]
            for content in Contents:
                if useCache:
                    if content not in self.cache:
                        mimeObject = self._getMIMEObject(content)
                        self.cache[content] = mimeObject
                    msg.attach(self.cache[content])
                else:
                    msg.attach(self._getMIMEObject(content))
        return msg        
        
    def _findUserFromHome(self):
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()        

    def _makeAddrAliasFrom(self, x):
        if isinstance(x, str):
            return (x, x)
        if isinstance(x, dict): 
            if len(x) == 1:
                return (list(x.keys())[0], list(x.values())[0])
        raise YagAddressError

    def _makeAddrAliasTarget(self, x, addresses, which): 
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
        
    def _addSubject(self, msg, Subject):
        if not Subject:
            return
        if isinstance(Subject, list):
            Subject = ' '.join(Subject)
        msg['Subject'] = Subject
        
    def _getMIMEObject(self, attachString):
        guessed_type = (None, None)
        if os.path.isfile(attachString):
            try:
                with open(attachString) as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(attachString, 'rb') as f:
                    content = f.read()                 
        else:
            try:
                r = requests.get(attachString)
                # pylint: disable=protected-access
                # Used to obtain the raw content of requests object
                content = r._content 
                if 'content-type' in r.headers:
                    guessed_type = r.headers['content-type'].split('/')
            except (IOError, ValueError): 
                html_tree = lxml.html.fromstring(attachString)                
                if html_tree.find('.//*') is not None or html_tree.tag != 'p':
                    return MIMEText(attachString, 'html')
                else:
                    return MIMEText(attachString) 
                
        if guessed_type[0] is None:
            guessed_type = mimetypes.guess_type(attachString)
            if guessed_type[0] is not None: 
                guessed_type = guessed_type[0].split('/')
                
        if guessed_type is None:    
            raise YagContentError('Content-type cannot be inferred')    
        else:
            default_type, content_type = guessed_type
            contentName = os.path.basename(attachString)
            mimeObject = MIMEBase(default_type, content_type, name = contentName)
            mimeObject.set_payload(content)
            email.encoders.encode_base64(mimeObject)                
            return mimeObject
                    
    def __del__(self):
        self.close()
        
def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail"""
    keyring.set_password('yagmail', username, password)
