from pydantic import BaseModel
from enum import Enum

class VehicleType(str, Enum):
    bike = "Bike"
    car = "Car"
    