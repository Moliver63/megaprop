import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'sua-chave-secreta'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///megaprop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False