import os
import mongoengine
from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)
DB_URI = os.getenv("DB_CONNECTION")

MONGODB_SETTINGS = {"db": os.getenv("DATABASE"), "host":DB_URI}

def connect_to_mongo():
    mongoengine.connect(**MONGODB_SETTINGS)
    logger.info("Connected to MongoDB")