from database.session import SessionLocal
from fastapi import Depends, HTTPException #,FastAPI, status,APIRouter,Query
from models import * 
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
from typing import Annotated
from sqlalchemy.orm import Session




def get_db(): 
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session, Depends(get_db)]


def check(email):
    try:
        v = validate_email(email)
        email = v["email"]
        return True
    except EmailNotValidError:
        return False


def user_name_verify(name:str,db:db_dependency) -> bool:
    db_users=db.query(User).filter(User.full_name==name,User.status == 1).first()
    if db_users:
        return True
    else:
        return False 

def phone_number_validation(number:str):
   
    num=number.replace(" ","")
    if num[0] in ['6','7','8','9'] and len(num)==10 and int(num)*0.5==int(num)/2:
        return True
    else:
        return False
   
    
def vehicle_number_validation(vehicle_number : str):
    value=vehicle_number.strip()# TN 36 DR 1236
    if len(value)==13:          # 0123456789101112
        for digit in range(0,len(value)-1):
            if digit in [0,1,6,7]:
                ascii_value=ord(value[digit])
                if ascii_value >= 65 and ascii_value <=90:
                    pass
                elif ascii_value >=97 and ascii_value <=122:
                    pass 
                else:
                    return False
            elif digit in [2,5,8]:
                if value[digit] == ' ':
                    pass
                else:
                    return False
            else:
                ascii_value=ord(value[digit])
                if ascii_value >= 48 and ascii_value <=57:
                    pass
                else:
                    print(value[digit])
                    return False
                
        return True
    else:
        return False

def time_convert(start_time, end_time):
    time_distance = end_time - start_time

    hours = time_distance.total_seconds() / 3600
    return hours