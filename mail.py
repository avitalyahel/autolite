import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from verbosity import verbose

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    {head}
  </head>
  <body>
    {content}
  </body>
</html>
'''


class Email(object):

    def __init__(self,
                 smtp_server='smtp.gmail.com',
                 smtp_port=587,
                 smtp_username='',
                 smtp_password=''):

        self.smpt = smtplib.SMTP(smtp_server, smtp_port)
        self.smpt.starttls()
        self.username, self.password = smtp_username, smtp_password
        self.smpt.login(self.username, self.password)

    def send(self, content: str, recipients: list,
             subject: str = '', html_head: str = '', file_paths: list = [], email_from=''):
        assert content, 'missing content'
        assert recipients, 'missing recipients'

        content = content.replace('\n', '<br/>')

        if not email_from:
            email_from = self.username

        msg = MIMEMultipart('alternative')

        html_part = MIMEText(HTML_TEMPLATE.format(head=html_head, content=content), 'html')
        msg.attach(html_part)

        if file_paths:
            tmpmsg = msg
            msg = MIMEMultipart()
            msg.attach(tmpmsg)

            for filename in file_paths:
                f = open(os.path.expanduser(filename))
                attachment = MIMEText(f.read(), _subtype='octet-stream')
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachment)

        msg['Subject'] = subject
        msg['To'] = ', '.join(recipients)
        msg['From'] = email_from

        self.smpt.sendmail(email_from, list(recipients), msg.as_string())

        verbose(1, 'Mail sent to {}: "{}"'.format(recipients, subject))

    def __del__(self):
        if hasattr(self, 'smpt'):
            try:
                self.smpt.quit()

            except smtplib.SMTPServerDisconnected:
                pass


class FakeEmail(object):

    def send(self, content: str, recipients: list,
             subject: str = '', html_head: str = '', file_paths: list = [], email_from=''):

        print('from:', email_from)
        print('to:', recipients)
        print('subjec:', subject)
        print(content)


if __name__ == '__main__':
    username = 'avital.yahel'
    email = Email(
        smtp_username=username,
        smtp_password=input(username + '\'s password: '),
    )
    fnames = ['README.md']
    email.send(
        recipients=['avital.yahel@gmail.com'],
        subject='Demo: html content{}'.format(' with attachement' if fnames else ''),
        content='This is html content{}.'.format(', with attachements' if fnames else ''),
        attach_fnames=fnames,
    )
