import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'test-realty-service'
    URL_MONGODB = 'mongodb://localhost:27017/'
    DATABASE = 'realty-service'
    SMTP_SERVER = os.environ.get('SMPT_SERVER') or 'smtp.yandex.ru'
    SMTP_PORT = os.environ.get('SMTP_PORT') or 587
    EMAIL = os.environ.get('EMAIL') or 'bykov@appvelox.ru'
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or '9Fhc7RnZ1kMV'
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30


class ConfigCelery:
    broker_url = os.environ.get('BROKER_URL') or 'redis://localhost:6379'
    result_backend = os.environ.get('RESULT_BACKEND') or 'redis://localhost:6379'

    task_serializer = os.environ.get('TASK_SERIALIZER') or 'json'
    result_serializer = os.environ.get('RESULT_SERIALIZER') or 'json'
    accept_content = os.environ.get('ACCEPT_CONTENT') or ['json']
    timezone = os.environ.get('TIMEZONE') or 'Europe/Moscow'
    enable_utc = True
