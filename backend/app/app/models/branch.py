from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
# from database.base_class import Base
from app.database.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT

class Branch(Base):
    __tablename__ = "branch"
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    phone_number = Column(String(12))
    address = Column(String(50))
    manager_id = Column(Integer, ForeignKey("user.id"),default = None )
    maximum_no_bike = Column(Integer)
    maximum_no_car = Column(Integer)
    updated_date = Column(DateTime,default = None)
    created_at = Column(DateTime)
    status = Column(TINYINT, comment=" '1:Active', '-1:Inactive', '0:Delete' ")

    
    user = relationship("User", back_populates="branch")

    parkingslotbooking = relationship("Parkingslotbooking", back_populates="branch")
