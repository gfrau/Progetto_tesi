from sqlalchemy import Column, Integer, String, Boolean
from app.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="viewer")