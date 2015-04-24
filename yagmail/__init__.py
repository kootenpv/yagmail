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
    """ Connection is the class that contains the smtp"""
    def __init__(self, From, password = None, host = 'smtp.gmail.com', port = '587', 
                 starttls = True, set_debuglevel = 0, **kwargs): 
        if not From: 
            From = self._findUserFromHome()
        self.From = From 
        self.isClosed = None 
        self.host = host
        self.port = port
        self.attachmentCount = 0
        self.starttls = starttls
        self.debuglevel = set_debuglevel
        self.kwargs = kwargs
        self._login(password)
        
    def prepare(self, To = None, Subject = None, Body = None, Html = None, Image = None, Cc = None, Bcc = None):
        self.attachmentCount = 0
        if self.isClosed:
            raise YagConnectionClosed('Login required again') 
        if To is None:
            To = self.From
        msg = MIMEMultipart() 
        self._addSubject(msg, Subject)
        msg['From'] = self.From
        msg['To'] = ";".join(To) if isinstance(To, list) else To
        if Cc is not None:
            msg['Cc'] = ";".join(Cc) if isinstance(Cc, list) else Cc 
        if Bcc is not None:
            msg['Bcc'] = ";".join(Bcc) if isinstance(Bcc, list) else Bcc 
        self._addBody(msg, Body)
        self._addHtml(msg, Html)
        self._addImage(msg, Image) 
        return msg        
        
    def send(self, To = None, Subject = None, Body = None, Html = None, Image = None, Cc = None, Bcc = None): 
        """ Use this to send an email with gmail"""
        msg = self.prepare(To, Subject, Body, Html, Image, Cc, Bcc)
        if To is None:
            To = self.From
        return self.smtp.sendmail(self.From, To, msg.as_string())

    def preview(self, To = None, Subject = None, Body = None, Html = None, Image = None, Cc = None, Bcc = None): 
        """ Use this to send an email with gmail"""
        msg = self.prepare(To, Subject, Body, Html, Image, Cc, Bcc)
        if To is None:
            To = self.From
        return msg.as_string() 

    def close(self):
        self.isClosed = True
        self.smtp.quit()

    def _login(self, password):
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

    def _findUserFromHome(self):
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()        
        
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
        self.attachmentCount += 1        
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

