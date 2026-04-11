import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                     = os.environ.get('SECRET_KEY') or 'cropsense-secret-2024'
    SQLALCHEMY_DATABASE_URI        = os.environ.get('DATABASE_URL') or 'sqlite:///farming.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER                  = 'uploads'
    MAX_CONTENT_LENGTH             = 16 * 1024 * 1024
    WEATHER_API_KEY                = os.environ.get('WEATHER_API_KEY')
    GEMINI_API_KEY                 = os.environ.get('GEMINI_API_KEY')
    _groq_env = os.environ.get('GROQ_API_KEY')
    GROQ_API_KEY = (_groq_env if _groq_env and len(_groq_env) > 10 else None)
    
    # Twilio SMS Config
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN  = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
