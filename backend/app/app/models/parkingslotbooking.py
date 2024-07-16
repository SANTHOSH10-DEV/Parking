from sqlalchemy import Column, Integer, String,ForeignKey,DateTime,DECIMAL
from app.database.base_class import Base
# from database.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT



class Parkingslotbooking(Base):
    __tablename__ = "parkingslotbooking"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey("user.id"))
    branch_id = Column(Integer, ForeignKey("branch.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"))
    parking_in_time = Column(DateTime)
    parking_out_time = Column(DateTime)
    fees = Column(DECIMAL(10,2))
    payment_type = Column(String(40))
    booking_time = Column(DateTime)
    status = Column(TINYINT,comment=" '1:Active', '-1:Inactive', '0:Delete' ")
    
    
    user = relationship("User", back_populates="parkingslotbooking")

    branch = relationship("Branch", back_populates="parkingslotbooking")
    
    vehicle = relationship("Vehicle", back_populates="parkingslotbooking")
 