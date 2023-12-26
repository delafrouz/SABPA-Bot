import os

from pymongo import MongoClient


DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_URL = f'mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_NAME}.{DB_HOST}.mongodb.net/'

client = MongoClient(DB_URL)
mongo_db = client.Sabpa
