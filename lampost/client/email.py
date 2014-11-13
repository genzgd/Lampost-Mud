from smtplib import SMTPHeloError, SMTP, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError
from threading import Thread

from lampost.context.resource import provides, requires, m_requires

m_requires(__name__, 'log')


@provides('email_sender')
class EmailSender():
    def __init__(self):
        try:
            info_file = open('data/email_info')
        except IOError:
            warn("No email info available", self)
            self.available = False
            return
        email_info = info_file.readlines()
        self.email_name = email_info[0].strip
        self.email_address = email_info[1].strip()
        self.email_password = email_info[2].strip()
        info_file.close()
        self.available = True

    def send_targeted_email(self, subject, text, users):
        if not self.available:
            return "Email not available"
        wrappers = []
        for user in users:
            if user.email:
                wrappers.append(EmailWrapper(user.email, "\From: {}\nTo: {}\nSubject:{}\n\n{}".format(self.email_name, user.user_name, subject, text)))
            else:
                log.warn("User {} has no email address".format(user.user_name), self)
        MessageSender(wrappers).start()
        return "Email Sent"


@requires('email_sender')
class MessageSender(Thread):

    def __init__(self, wrappers):
        super().__init__()
        self.wrappers = wrappers

    def run(self):
        self._open_server()
        for wrapper in self.wrappers:
            self._send_message(wrapper.addresses, wrapper.message)
        self.server.close()

    def _send_message(self, addresses, message):
        try:
            self.server.sendmail(self.email_sender.email_address, addresses, message)
        except SMTPHeloError as exp:
            error("Helo error sending email", self, exp)
        except SMTPRecipientsRefused:
            warn("Failed to send email to {}".format(addresses), self)
        except SMTPSenderRefused:
            error("Sender refused for email", self)
        except SMTPDataError as exp:
            error("Unexpected Data error sending email", self, exp)

    def _open_server(self):
        self.server = SMTP("smtp.gmail.com", 587)
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.email_sender.email_address, self.email_sender.email_password)


class EmailWrapper():
    def __init__(self, addresses, message):
        self.addresses = addresses
        self.message = message
