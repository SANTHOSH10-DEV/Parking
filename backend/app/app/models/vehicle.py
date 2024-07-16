from sqlalchemy import Column, Integer, String,ForeignKey,DateTime
# from database.base_class import Base
from app.database.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT


class Vehicle(Base):
    __tablename__ = 'vehicle'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    vehicletype_id = Column(Integer, ForeignKey("vehicletype.id"))
    vehicle_number = Column(String(15), unique = True )
    brand_name = Column(String(40))
    model = Column(String(40))
    color = Column(String(40))
    created_at = Column(DateTime)
    status = Column(TINYINT,comment=" '1:Active', '-1:Inactive', '0:Delete' ")

    
    
    user = relationship("User", back_populates="vehicle")

    vehicletype = relationship("Vehicletype", back_populates = "vehicle" )

    parkingslotbooking = relationship("Parkingslotbooking", back_populates="vehicle")