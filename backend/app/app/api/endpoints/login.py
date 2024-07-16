
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from models import *
from database.session import SessionLocal
from datetime import datetime,timedelta
from core.security import verify_password
from passlib.context import CryptContext
from core.security import get_password_hash

import random
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()
dt = str(int(datetime.utcnow().timestamp()))

def get_db(): 
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def verify_password(plain_password: str, password: str):
#     return pwd_context.verify(plain_password, password)

def get_user_token(db: Session, *, token: str) :# Keyword argument like (*, token:str)
    get_token=db.query(ApiTokens).filter(ApiTokens.token== token ,
                                            ApiTokens.status==1).first()

    if get_token: 
        return db.query(User).filter(User.id == get_token.user_id,
                                         User.status == 1).first()            
    else:
        return None
    
#1) Login
@router.post("/login")
async def login(db: Session = Depends(get_db),
                full_Name: str = Form(...),
                password: str = Form(...)):
    user=db.query(User).filter(User.full_name==full_Name,User.status == 1).first()
   
    if not user:
        return {"status": 0,"msg": "Your account not found.Please check the details you entered."}
    
    if not verify_password(password,user.password):
        return {"status": 0,"msg": "Your account Password is incorrect. Please entered correct Password."}
   
    key = ''
    char1 = '0123456789abcdefghijklmnopqrstuvwxyz'
    char2 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    characters = char1 + char2 # SALT_KEY
    for i in range(0, 20):
        key += characters[random.randint(0, len(characters) - 1)]
            # delToken = db.query(ApiTokens).\
            # filter(ApiTokens.user_id == user.id).update({'status': 0})
    
    already_login=db.query(ApiTokens
                           ).filter(ApiTokens.user_id==user.id,
                                    ApiTokens.status==1).update({'status':-1})
    
    # set token expire 
    expire_time=datetime.now()+ timedelta(minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    addToken = ApiTokens(user_id = user.id,
                            token = key,
                            date = datetime.now(),
                            validity = 1,
                            status = 1,
                            expires_at=expire_time
                            )
    db.add(addToken)
    db.commit()
    return {'status':1,
            'token': key,
            'msg': 'Successfully login.',
            'userId': user.id,
            'userName': user.full_name}

#2) Check Token
@router.post("/check_token")
async def checkToken(*,db: Session = Depends(get_db),
                      token: str = Form(...)):
    
    checkToken = db.query(ApiTokens).filter(ApiTokens.token == token,
                                           ApiTokens.status == 1).first()
    if checkToken:
        return {"status": 1,"msg": "Success."}
    else:
        return {"status": 0,"msg": "Failed."}
    
#3) Logout
@router.post("/logout")
async def logout(db: Session = Depends(get_db),
                 token: str = Form(...)):

    user = get_user_token(db = db,token = token)
    if user:
        check_token = db.query(ApiTokens
                               ).filter(ApiTokens.token == token,
                                        ApiTokens.status == 1
                                        ).update({"status":-1})
        db.commit()
        return ({"status": 1,"msg": "Success."}) 
    else:
        return ({"status":0,"msg":"Invalid user."})
    
#4) Forgot Password
@router.post("/forgot_password")
async def forgot_password(db: Session = Depends(get_db),
                            user_name: str = Form(...),
                            phone_number: str = Form(...),
                            email_id: str = Form(...),
                            new_password: str = Form(...),
                            confirm_password: str = Form(...)):

    CheckUserName=db.query(User).filter(User.full_name==user_name).first()

    if CheckUserName:
        CheckPhoneNumber=db.query(User).filter(User.full_name==user_name,
                                                   User.phone_number==phone_number).first()
        
        if CheckUserName:
            CheckMailID=db.query(User).filter(User.full_name==user_name,
                                                  User.phone_number==phone_number,
                                                  User.email_id==email_id).first()
            if CheckMailID:
                if new_password==confirm_password:
                    hashed_password=get_password_hash(confirm_password)
                    ChangePassword=db.query(User).filter(User.full_name==user_name,
                                                  User.phone_number==phone_number,
                                                  User.email_id==email_id
                                                  ).update({"password" : hashed_password})
                    db.commit()
                    return ({"Status": 1, "message": "Password update successfully",
                             "User Name" : user_name})
                else:
                    return {"status" : 0, "msg" : "New password and Confirm password doesn't match"}
            else:
                return {"status" : 0, "msg" : "Invalied email ID"}

        else:
            return {"status" : 0, "msg" : "Invalied Phone number"}    
    else:
        return {"status": 0, "msg" : "Invalied user name" }
    