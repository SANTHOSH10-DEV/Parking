from pydantic import BaseModel
from enum import Enum


class Payment(str, Enum):
    phone_pay = "Phone_pay"
    google_pay = "Google_pay"
    paytm = " Paytm"
    cash = "Cash"
    wallet = "wallet"