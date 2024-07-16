from fastapi import APIRouter, Form,HTTPException
from utils import db_dependency
from models import * 
from sqlalchemy import or_
from datetime import datetime
from utils import vehicle_number_validation



router = APIRouter()

# 1). new wallet:
@router.post("/new_wallet_id")
async def new_user_add_amount(db : db_dependency, token : str,
                     credit : float = Form(...),
                     ):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.status==1:

        already_exist = db.query(Wallet).filter(Wallet.user_id == check_token.user_id,
                                                Wallet.status == 1).first()
        if already_exist:
            return {"status" : 0, "message" : "Already You have a wallet_ID, So add amount in Your wallet id "}
        
        # if credit is not type(float):
        #     return {"status" : 0, "message" : "Invalide Credit amount"}
        
        db_wallet = Wallet(user_id = check_token.user_id,
                             balance = credit,
                             credit_amount = credit,
                             updated_at = datetime.now(),
                             status = 1)
        
        db.add(db_wallet)
        # db.refresh(db_wallet)
        db.commit()

        return ({
            "status" : 1 ,
            "message" : "Successfully credit amount",
            "Credit_amount" : credit,
            "Total amount" : db_wallet.balance,
        })
    
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })


#  2). Add amount in wallet:
@router.post("/update_add_wallet_amount")
async def credit_amount(db : db_dependency, token : str,
                     credit : float = Form(...),
                     ):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

    if not check_token:
        return ({"status":0, "message": "Invalied token Id"})
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.status==1:
        
        GetwalletId = db.query(Wallet).filter(Wallet.user_id == check_token.user_id,
                                              Wallet.status == 1).first()
        
        GetwalletId.balance = (GetwalletId.balance + credit)
        GetwalletId.credit_amount = credit ,
        GetwalletId.updated_at = datetime.now()
        
        db.add(GetwalletId)
        
        db.commit()

        return ({
            "status" : 1 ,
            "message" : "Successfully credit amount",
            "Credit_amount" : credit,
            "Total amount" : GetwalletId.balance,
        })
    
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })



