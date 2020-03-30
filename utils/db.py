from pymongo import MongoClient

from config import Config

client_mongo = MongoClient(Config.URL_MONGODB)
db = client_mongo[Config.DATABASE]
user_collection = db['user']
request_collection = db['request']