from fastapi import FastAPI
from pymongo import MongoClient
from celery import Celery

from Config import Config, ConfigCelery

app = FastAPI(title="Realty-Service",
              description="This is a training project, with auto docs for the API",
              version="0.1",)

celery = Celery('app', include=['app.model.services'])
celery.config_from_object(ConfigCelery)
client_mongo = MongoClient(Config.URL_MONGODB)
db = client_mongo[Config.DATABASE]
user_collection = db['user']
request_collection = db['request']

from app.controller import routes

