from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    access_token = Column(Text, nullable=False)  # Зашифрованный
    instagram_account_id = Column(String, nullable=False)
    proxy_url = Column(String)
    daily_limit = Column(Integer, default=5)
    current_daily_posts = Column(Integer, default=0)
    status = Column(String, default='active')  # active, limited, banned, error
    last_post_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow) 