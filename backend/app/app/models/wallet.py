from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base_class import Base
# from database.base_class import Base
from sqlalchemy.dialects.mysql import TINYINT


class Wallet(Base):
    __tablename__ = 'wallet'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    balance = Column(Float, default=0.0)
    credit_amount = Column(Float,) 
    updated_at = Column(DateTime)
    status = Column(TINYINT,comment=" '1:Active', '-1:Inactive', '0:Delete' ")

    
    user = relationship("User", back_populates="wallet")
    
