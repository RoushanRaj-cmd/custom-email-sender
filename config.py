import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///emails.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ESP and OAuth configurations
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Email throttling settings
    MAX_EMAILS_PER_HOUR = 500  # Adjust based on your provider limits
    MAX_BATCH_SIZE = 50        # Maximum emails to send in one batch
    
    # Email provider settings
    EMAIL_PROVIDER_RATE_LIMIT = 100  # Emails per minute allowed by provider
