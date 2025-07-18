from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PostTask(Base):
    __tablename__ = "post_tasks"
    
    task_id = Column(String, primary_key=True)
    account_id = Column(String, nullable=False)
    video_path = Column(String, nullable=False)
    caption = Column(Text)
    hashtags = Column(String)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default='pending')  # pending, completed, failed
    media_id = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow) 