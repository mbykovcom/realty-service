import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bson import ObjectId
from celery import Celery
from celery.schedules import crontab

from config import Config, ConfigCelery
from utils.db import request_collection, user_collection

celery = Celery('celery_app')
celery.config_from_object(ConfigCelery)

celery.conf.beat_schedule = {
    "overdue_requests_processing": {
        "task": 'celery_app.warning_admin_long_time_consider_request',
        'schedule': crontab(minute=Config.CHECK_OVERDUE_REQUEST_PERIOD)
    },
    "overdue_requests_execution": {
        "task": 'celery_app.warning_employee_long_time_complete_request',
        'schedule': crontab(minute=Config.CHECK_OVERDUE_REQUEST_PERIOD)
    }
}


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
    except Exception as error:  # If an exception is raised when send email
        print(error)
        return False
    return True


@celery.task
def warning_admin_long_time_consider_request() -> bool:
    admin = user_collection.find_one({'role': 'admin'})
    try:
        requests = request_collection.find({'employee_id': ''})
        now = datetime.now()
        overdue_requests = [request for request in requests
                            if (now - request['date_receipt']) > timedelta(
                                hours=Config.CONSIDERATION_REQUEST_TIME)]
        if not overdue_requests:
            return False
        for request in overdue_requests:
            send_email.delay(admin['email'], 'Overdue request', "You're taking too long to process the request "
                                                                f"(> {Config.CONSIDERATION_REQUEST_TIME} hours): "
                                                                f"{request['title']} id = {request['_id']}")
    except Exception as error:
        print(error)
        return False
    return True


@celery.task
def warning_employee_long_time_complete_request() -> bool:
    try:
        requests = request_collection.find({'$and': [
            {'employee_id': {'$not': {'$eq': ''}}},
            {'status': {'$not': {'$eq': 'finished'}}}
        ]})
        now = datetime.now()
        overdue_requests = [request for request in requests
                            if (now - request['date_receipt']) > timedelta(
                                hours=Config.REQUEST_EXECUTION_TIME)]
        if not overdue_requests:
            return False
        for request in overdue_requests:
            employee_email = user_collection.find_one({'_id': ObjectId(request['employee_id'])})['email']
            send_email.delay(employee_email, 'Overdue request', "You take too long to complete the request "
                                                                f"(> {Config.REQUEST_EXECUTION_TIME} hours): "
                                                                f"{request['title']} id = {request['_id']}")
    except Exception as error:
        print(error)
        return False
    return True
