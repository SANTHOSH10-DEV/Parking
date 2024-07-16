from sqlalchemy import  Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.database.base_class import Base
# from database.base_class import Base



class ApiTokens(Base):
    __tablename__ = "api_tokens"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    token=Column(String(100))
    validity=Column(TINYINT(1),comment="0-Expired, 1- Lifetime")
    expires_at=Column(DateTime)# expire time
    date=Column(DateTime)
    status=Column(TINYINT(1),comment="1-active, -1 inactive, 0- deleted")

    user=relationship("User",back_populates="api_tokens")



