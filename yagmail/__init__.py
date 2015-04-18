import keyring
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen        

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError
    
class UserNotFoundInKeyring(Exception):
    pass

class YagConnectionClosed(Exception):
    pass

class Connect():
    """ Connection is the class that contains the server"""
    def __init__(self, From, password = None): 
        if not From: 
            From = self._findUserFromHome()
        self.From = From 
        self.isClosed = None
        self.login(password)

    def _findUserFromHome(self):
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()
        
    def send(self, To = None, Subject = None, Body = None, Html = None, Image = None): 
        """ Use this to send an email with gmail"""
        if self.isClosed:
            raise YagConnectionClosed('Login required again') 
        if To is None:
            To = self.From
        msg = MIMEMultipart() 
        self._addSubject(msg, Subject)
        msg['From'] = self.From
        msg['To'] = ";".join(To) if isinstance(To, list) else To
        self._addBody(msg, Body)
        self._addHtml(msg, Html)
        self._addImage(msg, Image)
        if isinstance(To, str):
            To = [To] 
        return self.server.sendmail(self.From, To, msg.as_string())

    def close(self):
        self.isClosed = True
        self.server.quit()

    def login(self, password):
        self.server = smtplib.SMTP('smtp.gmail.com:587')
        self.server.starttls() 
        if password is None:
            password = keyring.get_password('yagmail', self.From)
            if '@' not in self.From:
                self.From += '@gmail.com'
            if password is None: 
                password = keyring.get_password('yagmail', self.From) 
            if password is None: 
                exceptionMsg = 'Either yagmail is not listed in keyring, or the user + password is not defined.'
                raise UserNotFoundInKeyring(exceptionMsg)
        self.server.login(self.From, password)
        self.isClosed = False
        
    def _addSubject(self, msg, Subject):
        if not Subject:
            return
        if isinstance(Subject, list):
            Subject = ' '.join(Subject)
        msg['Subject'] = Subject
        
    def _addBody(self, msg, Body):
        if not Body:
            return
        if isinstance(Body, list):
            Body = " ".join(Body)
        msg.attach(MIMEText(Body)) 

    def _addHtml(self, msg, Html):
        if not Html:
            return
        if isinstance(Html, str):
            Html = [Html]
        for html in Html:    
            msg.attach(self._readHtml(html)) 
            
    def _addImage(self, msg, Image):
        if not Image:
            return
        if isinstance(Image, str):
            Image = [Image]
        for img in Image:
            msg.attach(self._readImage(img))

    def _readHtml(self, html):
        content = self._loadContent(html)
        return MIMEText(content, 'html')
        
    def _readImage(self, img):
        content = self._loadContent(img)
        imgName = os.path.basename(img)
        if len(imgName) > 50:
            imgName = 'long_img_name_{}'.format(hash(img))
        return MIMEImage(content, name = imgName)

    def _loadContent(self, inp):
        try:
            with open(inp) as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(inp, 'rb') as f:
                content = f.read()            
        except FileNotFoundError: 
            try:
                content = urlopen(inp).read()
            except:
                content = inp
        return content            
        
    def __del__(self):
        self.close()

    def test(self):
        tos = [self.From, self.From]    
        subjects = ['subj', 'subj1']
        bodys = ['body', 'body1']
        htmls = ['/Users/pascal/GDrive/yagmail/yagmail/example.html', '<h2>Text</h2>']
        imgs = ['/Users/pascal/Documents/Capture.PNG', 'http://tinyurl.com/lpphnuy']
        self.send(tos, subjects, bodys, htmls, imgs)
        

def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail"""
    keyring.set_password('yagmail', username, password)
