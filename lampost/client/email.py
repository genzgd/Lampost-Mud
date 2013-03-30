from smtplib import SMTPHeloError, SMTP, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError

from lampost.context.resource import provides, m_requires

m_requires('log', __name__)


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
        server = self._open_server()
        for user in users:
            if user.email:
                email_message = "\From: {}\nTo: {}\nSubject:{}\n\n{}".format(self.email_name, user.user_name, subject, text)
                self._send_message(server, user.email, email_message)
            else:
                log.warn("User {} has no email address".format(user.user_name), self)
        server.close()
        return "Email Sent"

    def _open_server(self):
        server = SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(self.email_address, self.email_password)
        return server

    def _send_message(self, server, addresses, message):
        try:
            return server.sendmail(self.email_address, addresses, message)
        except SMTPHeloError as exp:
            error("Helo error sending email", self, exp)
        except SMTPRecipientsRefused:
            warn("Failed to send email to {}".format(addresses), self)
        except SMTPSenderRefused:
            error("Sender refused for email", self)
        except SMTPDataError as exp:
            error("Unexpected Data error sending email", self, exp)