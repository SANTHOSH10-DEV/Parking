from sqlalchemy import Column, Integer, String,ForeignKey,DateTime
from app.database.base_class import Base
# from database.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT


class User(Base):
    __tablename__='user'
    id=Column(Integer, primary_key=True)
    first_name=Column(String(30))
    last_name=Column(String(30))
    full_name=Column(String(45),unique=True)
    phone_number=Column(String(12),unique=True)
    email_id=Column(String(50))
    password=Column(String(100))
    user_type =Column(TINYINT,comment="1->SuperAdmin,2->Admin,3->Manager,4->Employee,5->customer")
    created_at=Column(DateTime)
    status=Column(TINYINT,comment=" '1:Active', '-1:Inactive', '0:Delete' ")

    
    api_tokens = relationship("ApiTokens", back_populates="user")

    vehicle = relationship("Vehicle", back_populates="user")

    branch = relationship("Branch", back_populates="user")

    parkingslotbooking = relationship("Parkingslotbooking", back_populates="user")

    wallet = relationship("Wallet", back_populates = "user")
