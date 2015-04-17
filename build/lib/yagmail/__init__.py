import keyring
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class UserNotFoundInKeyring(Exception):
    pass

class Mail():
    """ Mail is the class that contains the server"""
    def __init__(self, From, password = None): 
        self.From = From
        self.server = smtplib.SMTP('smtp.gmail.com:587')
        self.server.starttls() 
        if password is None:
            pw = keyring.get_password('yagmail', From)
            if pw is None:
                pw = keyring.get_password('yagmail', From + '@gmail.com') 
            if pw is None: 
                exceptionMsg = 'Either yagmail is not listed in keyring, or the user + pw is not defined.'
                raise UserNotFoundInKeyring(exceptionMsg)
        self.server.login(From, pw)

    def send(self, To, Subject = '', Body = None, Html = None): 
        """ Use this to send an email with gmail"""
        msg = MIMEMultipart() 
        msg['Subject'] = Subject
        msg['From'] = self.From.replace('@gmail.com', '') + '@gmail.com'
        msg['To'] = To        
        if Body is not None:
            msg.attach(MIMEText(Body)) 
        if Html is not None:
            msg.attach(MIMEText(Html, 'html'))            
        if isinstance(To, str):
            To = [To]
        return self.server.sendmail(self.From, To, msg.as_string())

    def __del__(self):
        self.server.quit()

def register(username, password):
    """ Use this to add a new gmail account to your OS' keyring so it can be used in yagmail"""
    keyring.set_password('yagmail', username, password)
