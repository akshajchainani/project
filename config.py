import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AI21_API_KEY = os.getenv("AI21_API_KEY")
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME")