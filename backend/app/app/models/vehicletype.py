from sqlalchemy import Column, Integer, String,Float,ForeignKey,DateTime
# from database.base_class import Base
from app.database.base_class import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT


class Vehicletype(Base):

    __tablename__ = 'vehicletype'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30))
    amount_per_hour = Column(Float)
    date = Column(DateTime)
    status = Column(TINYINT,comment=" '1:Active', '-1:Inactive', '0:Delete' ")
     
    
    vehicle = relationship("Vehicle", back_populates = "vehicletype" )

    