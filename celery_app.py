import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Celery

from config import Config, ConfigCelery

celery = Celery('celery_app')
celery.config_from_object(ConfigCelery)

@celery.task
def send_email(email, title, description) -> bool:
    """Send an email

    :param email: recipient's email address as name@email.com
    :param title: message subject
    :param description: the text of the letter
    :return: True if the email is sent, otherwise False
    """
    try:
        smtpObj = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        smtpObj.starttls()
        smtpObj.login(Config.EMAIL, Config.EMAIL_PASSWORD)
        message = MIMEMultipart("alternative")
        message["Subject"] = title
        message["From"] = Config.EMAIL
        message["To"] = email
        msg = f"""\
                {description}"""
        message.attach(MIMEText(msg, 'plain'))
        smtpObj.sendmail(Config.EMAIL, email, message.as_string())
    except Exception as error:      # If an exception is raised when send email
        print(error)
        return False
    return True
