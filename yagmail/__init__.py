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

class UserNotFoundInKeyring(Exception):
    pass

class Mail():
    """ Mail is the class that contains the server"""
    def __init__(self, From, password = None): 
        if not From: 
            From = self._findUserFromHome()
        self.From = From
        self.server = smtplib.SMTP('smtp.gmail.com:587')
        self.server.starttls() 
        if password is None:
            password = keyring.get_password('yagmail', From)
            if password is None:
                password = keyring.get_password('yagmail', From + '@gmail.com') 
            if password is None: 
                exceptionMsg = 'Either yagmail is not listed in keyring, or the user + password is not defined.'
                raise UserNotFoundInKeyring(exceptionMsg)
        self.server.login(From, password)

    def _findUserFromHome(self):
        home = os.path.expanduser("~")
        with open(home + '/.yagmail') as f:
            return f.read().strip()
        
    def send(self, To, Subject = '', Body = None, Html = None, Image = None): 
        """ Use this to send an email with gmail"""
        msg = MIMEMultipart() 
        msg['Subject'] = Subject
        msg['From'] = self.From.replace('@gmail.com', '') + '@gmail.com'
        msg['To'] = To        
        self._addBody(msg, Body)
        self._addHtml(msg, Html)
        self._addImage(msg, Image)
        # Even die To uitzoeken nog
        if isinstance(To, str):
            To = [To]
        return self.server.sendmail(self.From, To, msg.as_string())

    def _addBody(self, msg, Body):
        if Body is None:
            return
        if isinstance(Body, list):
            Body = " ".join(Body)
        msg.attach(MIMEText(Body)) 

    def _addHtml(self, msg, Html):
        if Html is None:
            return
        if isinstance(Html, str):
            Html = [Html]
        for html in Html:    
            msg.attach(self._readHtml(html)) 
            
    def _addImage(self, msg, Image):
        if Image is None:
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
        except FileNotFoundError:     
            try:
                content = urlopen(inp).read()
            except:
                content = inp
        return content            
        
    def __del__(self):
        self.server.quit()

def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail"""
    keyring.set_password('yagmail', username, password)
