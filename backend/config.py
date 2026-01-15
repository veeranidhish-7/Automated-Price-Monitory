import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///pricetracker.db')
    
    # JWT Secret
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production')
    
    # Email Configuration
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USER = os.getenv('EMAIL_USER', 'your-email@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
    
    # App Configuration
    MAX_PRODUCTS_PER_USER = 5
    PRICE_CHECK_INTERVAL = 3600  # 1 hour in seconds