from fastapi import HTTPException,Depends, APIRouter,Body, Form
from sqlalchemy import or_,func,case
from typing import Annotated
from schemas import *
from models import * 
from database.session import SessionLocal
from datetime import datetime
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from utils import user_name_verify,phone_number_validation, db_dependency,check
from core.security import get_password_hash

router=APIRouter()
def get_db(): 
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 1). new user
@router.post("/sign_up")
async def new_user(db: Session = Depends(get_db),
                          first_name:str = Form(...),
                          last_name:str = Form(None),
                          user_name:str = Form(...),
                          phone_number:str = Form(...),
                          email_id:str = Form(...),
                          password: str = Form(...)):
    
    if user_name_verify(user_name, db):
        raise HTTPException(status_code=400, detail="User name already exists")

    if not phone_number_validation(phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    already_exist_phone_number=db.query(User).filter(User.phone_number==phone_number).first()
    
    if already_exist_phone_number:
        return {"status" : 0 , "message" : "Phone number is aleady exist"}
    
    if not check(email_id):
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    already_exist_email_id=db.query(User).filter(User.email_id==email_id).first()
    if already_exist_email_id:
        return {"status" :0, "message" : "email ID is already exist."}
    hashed_pass = get_password_hash(password)
    
    db_customer = User(
        first_name=first_name,
        last_name=last_name,
        full_name=user_name,
        phone_number=phone_number,
        email_id=email_id,
        password=hashed_pass,
        status=1,
        user_type= 5,
        created_at=datetime.now()
    )
    
    db.add(db_customer)
    
    db.commit()
    
    db.refresh(db_customer)
    
    return {
        "full_name": db_customer.full_name,
        "phone_number": db_customer.phone_number,
        "email_id": db_customer.email_id
    }

# 2). list All User
@router.get('/list')
async def list_user(token : str,db:db_dependency,page_no:int=1,size:int=10):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session is expired'})

    user=db.query(User).filter(User.id==check_token.user_id,
                                   User.status==1,
                                   or_(User.user_type==1,User.user_type==2)).first()
    if not user:
        return {"status" : 0, "message": "Accessed only by 'SuperAdmin' or 'Admin'."}

    result=[]

    all_customer=db.query(User).all()

    if (len(all_customer)) % size == 0:
        total_page = int((len(all_customer))/size)
    else:
        total_page=((len(all_customer))//size+1)

    if total_page < page_no:
        return {"message" : f"Only {total_page} pages available" }

    line_no=(page_no-1)*size
    customers=db.query(User).offset(line_no).limit(size).all()
   
    page_details=( "Page_no:", page_no, "Total_page:", 
                  total_page,"Total_no_records:", len(all_customer))
    for user in customers:
        result.append(
            {
                "UserID" : user.id,
                "UserName" : user.full_name,
                "PhoneNumber" : user.phone_number,
                "UserEmailID" : user.email_id
            })
        
    if not result:
            return {"message" : "Result not found"}
    return result

# 3). update User
@router.put('/update')

async def update_user(db: db_dependency, token:str , 
                          first_name : str = Form(None),
                          last_name : str = Form(None),
                          user_name : str = Form(None),
                          phone_number : str = Form(None),
                          email_id : str = Form(None)):
    checkToken = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if checkToken.expires_at < datetime.now():
        checkToken.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if checkToken.status ==1:
        user=db.query(User).filter_by(id=checkToken.user_id).first()
        
        if not (first_name or last_name or user_name or phone_number or email_id):
            return {"status" : 0, "message" : "No data is updated"}

        if first_name:
            user.first_name=first_name

        if last_name:
            user.last_name=last_name

        if user_name:
            if user_name_verify(user_name,db):
                raise HTTPException(status_code=400, detail="User name already exist")
            user.full_name=user_name

        if phone_number:
            if not phone_number_validation(phone_number):
                raise HTTPException(status_code=400, detail="Invalid Phone number")
            user.phone_number=phone_number

        if email_id:

            if not check(email_id):
                raise HTTPException(status_code=400, detail="Invalid email address")
            user.email_id=email_id
        
        db.commit()
        # db.refresh(user)
        # return user
        return ({
            "UserID" : user.id,
            "FirstName" : user.first_name,
            "LastName" : user.last_name,
            "FullName" : user.full_name,
            "PhoneNumber" : user.phone_number,
            "email_id" : user.email_id
        })
    else:
        return {"status" : 0, "message" : "Invalide token id"}
# 4). Delete user    
@router.post("/delete_account")
async def deleteUser(token:str,user_name:str, db:db_dependency):
    
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    user=db.query(User).filter(User.id==check_token.user_id,
                                    User.full_name==user_name,
                                    User.status == 1).first()
    
    # if user.status ==0 :
    #     return {"message" : "Invalied "}

    user.status = 0
    
    db.commit()

    return {"message" : "UserID successfully deactivated."}


# 5). Add Staff
@router.post("/add_staff")
async def new_staff(db: db_dependency,token: str,
                first_name:str = Form(...),
                last_name:str = Form(None),
                user_name:str = Form(...),
                phone_number:str = Form(...),
                email_id:str = Form(...),
                password: str = Form(...),
                user_type:int = Form(...,description="1:SuperAdmin,2:Admin,3:Manager,4:Employee")):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

    if not check_token:
        return ({"status":0, "message": "Invalied token Id"})
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.status==1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
    else:
        return ({"status" : 0, "message" : "Token ID is not Activate"})   

    if user_name_verify(user_name, db):
        raise HTTPException(status_code=400, detail="User name already exists")

    if not phone_number_validation(phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    
    already_exist_phone_number=db.query(User).filter(User.phone_number==phone_number).first()
    
    if already_exist_phone_number:
        return {"status" : 0 , "message" : "Phone number is aleady exist"}
    
    if not check(email_id):
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    already_exist_email_id=db.query(User).filter(User.email_id==email_id).first()
    if already_exist_email_id:
        return {"status" :0, "message" : "email ID is already exist."}
    hashed_pass = get_password_hash(password)
    if user_type not in [1,2,3,4]:
        return {"status": 0, "message": "Invalied user type"}
    
    db_customer = User(
        first_name=first_name,
        last_name=last_name,
        full_name=user_name,
        phone_number=phone_number,
        email_id=email_id,
        password=hashed_pass,
        status=1,
        user_type = user_type,
        created_at=datetime.now()
    )
    
    db.add(db_customer)
    
    db.commit()
    
    db.refresh(db_customer)
    
    return {
        "full_name": db_customer.full_name,
        "phone_number": db_customer.phone_number,
        "email_id": db_customer.email_id
    }

# 6). Update staff_id
@router.post("/update_staff_id")
async def update_staff_id(db:db_dependency,token : str,
                          update_user_id : int = Form(...),
                          update_user_type : int = Form(...,description= "2:Admin, 3:Manager, 4:Employee")):

    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()


    if not check_token:
        return ({"status":0, "message": "Invalied token Id"})
    

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.status == 1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}

    else:
        return ({"status" : 0, "message" : "Token ID is not Activate"})   
  

    getUpdateUser = db.query(User).filter(User.id == update_user_id).first()
    
    
    if not getUpdateUser:
        return({"status":0, "msg": "Invalied Update user ID"})
    
    if getUpdateUser.status != 1 :
        return ({"status":0,"message":"Update user ID is not activate"})
    
    if update_user_type not in [2,3,4]:
        return ({"status":0,"message":'Invalied Update user type'})
    
    if getUpdateUser.user_type == update_user_type:
        return ({"status" :0, "msg":"User ID is already updated"})
    
    else:
        getUpdateUser.user_type = update_user_type
        db.commit()
        return ({"status":1,"message":"User type is successfully updated"})





# # usercount
# @router.get("/usercount")
# async def countuser(db: db_dependency):
#     numberofuser = db.query(func.count(User.id).label("ucount")).filter(User.status ==1).scalar()

#     return numberofuser

# # mailid
# @router.get("/email")
# async def mail(db:db_dependency):
#     useremail = db.query(Vehicletype).scalar()
#     result =useremail
#     print (useremail,"one")
#     for row in useremail:
#         result.append({"user_id":row.id,
#                     #    "email_id": row.email_id,
#                        })
        
#     return "one"

# @router.get("/user")
# def list_user(db:db_dependency):
#     getUser = db.query(User).filter(User.status == 1).all()
#     result = []
#     for singlerow in getUser:
#         result.append({'User Id': singlerow.id,
#                        "User Name" : singlerow.full_name})
    
#     uservehicle =[ ]
#     getVehcle = db.query(Vehicle).filter(Vehicle.status == 1).all()
#     for row in getVehcle:
#         uservehicle.append({"Vehicle Number" : row.vehicle_number,
#                             "User id" : row.user_id})


#     return result, uservehicle





# def sleep_function():
#     print("process started")
#     import time
#     time.sleep(10)
#     print ("process ended")
    
# def going():
    
#     print("process on going")

# @router.get("/sleepfunction")
# async def process():
#     sleep_function()
#     going()
   




# def sleep_function():
#     print("process started")
    
#     start()
#     import time
#     time.sleep(5)
#     print ("process ended")
    
# def start():
    
#     print("process on going")

# @router.get("/sleepfunction")
# async def process():
#     sleep_function()
      



# import asyncio

# async def sleep_function():
#     print("process started")
#     # import time
#     # time.sleep(10)
#     await asyncio.sleep(10)
#     print("process ended")

# async def start():
#     print("process on going")

# @router.get("/sleepfunction")
# async def process():
#     sleep_task = asyncio.create_task(sleep_function())
#     await asyncio.sleep(0.1)
#     await start()
#     await sleep_task






   

import asyncio




# def sleep_function():
#     print("process started")
#     import time
#     time.sleep(10)
#     print ("process ended")

#     time.sleep(5)
#     print("after 5 sec")
    
# def going():
    
#     print("process on going")

# @router.get("/sleepfunction")
# async def process():
   
#     loop = asyncio.get_event_loop()
    
#     sleep_task = loop.run_in_executor(None, sleep_function)
    
#     going()
    
#     await sleep_task

#     print("somethings")



# def sleep_function():
#     print("process started")
#     import time
#     time.sleep(10)
#     print ("process ended")

    
# def going():
    
#     print("process on going")

# @router.get("/sleepfunction")
# async def process():
#     loop = asyncio.get_event_loop()
#     event_fun = loop.run_in_executor(None, sleep_function)
   
#     going()
#     await event_fun




# # example for Delimit
# @router.get("/items/{item_ids}")
# async def read_items(item_ids: str):
#     # Split the path parameter by comma to get a list of items
#     items = item_ids.split(",")
#     return {"items": items}

# # example for Delimit
# from pydantic import BaseModel

# class Item(BaseModel):
#     name: str
#     tags: str
# @router.post("/items/")
# async def create_item(item: Item):
#     # Split the tags by comma to get a list of tags
#     tags = item.tags.split(",")
#     return {"name": item.name, "tags": tags}





# # # joins for example
# @router.get("/innerJoins")
# async def innerjoin(db:db_dependency):
#     getInnerJoins = db.query(User,Wallet
#                              ).join(Wallet,User.id ==Wallet.user_id
#                                     ).order_by(User.id).all() 
#     # print(getInnerJoins)
#     result =[]
#     for row,row2 in getInnerJoins:
#         # return row
#         result.append({"wallet_ID" : row.id,
#                        "User_ID": row.full_name,
#                        "walletID": row2.id,
#                        "amount_amount":row2.balance
#                     })
    
#     return result


# # joins for example
# @router.get("/innerJoinsInverse")
# async def inner_join_inverse(db:db_dependency):
    

#     getrightJoin = db.query(User,Branch
#                             ).outerjoin(Branch,User.id == Branch.manager_id
#                                    ).filter(Branch.manager_id == None,
#                                             )
    
#     getleftJoin = db.query(User,Branch
#                             ).outerjoin(User, Branch.manager_id == User.id
#                                    ).filter(User.id == None,
#                                             )
#     left_right = getrightJoin.union(getleftJoin).all()
#     result = []

#     for u,b in left_right:
#         result.append({"userid": u.id if u else None,
#                        "user_name": u.full_name if u else None,
#                        "branch Id": b.id if b else None,
#                        "branch name": b.name if b else None
#                     })

#     return result

# # joins for example
# @router.get("/LeftOuterJoin")
# async def left_outer_join(db:db_dependency):
#     # getInnerJoins =( 
#     #                 db.query(Branch)
#     #                 .outerjoin(User)
#     #                 .all() )
# # another type
#     getInnerJoins =( 
#                     db.query(Branch)
#                     .join(User, isouter= True)
#                     .all() )
#     result =[]
#     for ut in getInnerJoins:
#         result.append({"wallet_ID" : ut.id,
#                        "User_ID": ut.name,
#                        })
    
#     return result

# @router.get("/LeftOuterJoin")
# async def left_outer_join(db:db_dependency):
#     getInnerJoins =( 
#                     db.query(Branch,User)
#                     .outerjoin(User,Branch.manager_id == User.id)
#                     .all() )
# # another type
#     # getInnerJoins =( 
#     #                 db.query(Branch)
#     #                 .join(User, isouter= True)
#     #                 .all() )
#     result =[]
#     for Bh,ut in getInnerJoins:
#         result.append({"wallet_ID" : Bh.id,
#                        "User_ID": Bh.name,
#                        "Manager_id": ut.id if ut else None,
#                        "Manager_name": ut.full_name if ut else None
#                        })
    
#     return result


# @router.get("/InverseLeftOuterJoin")
# async def inverse_left_outer_join(db:db_dependency):
#     getInnerJoins =( 
#                     db.query(Branch)
#                     .outerjoin(User)
#                     .filter(User.id == None)
#                     .all() )
#     result =[]
#     for ut in getInnerJoins:
#         result.append({"wallet_ID" : ut.id,
#                        "User_ID": ut.name,
#                        })
    
#     return result



# @router.get("/fullJoin")
# async def full_join(db:db_dependency):
    
#     # joinData= (db.query(User,Branch).outerjoin(Branch)
#     #            .union_all(db.query(User,Branch).outerjoin(User)
#     #             # .filter(User.id == None)
#     #             ).all())

#     # for utable,bt, in joinData:
#     #     print(bt.id if bt else None)
#     #     print(bt.name if bt else None)
#     #     print(utable.id if utable else None)
#     #     print(utable.full_name if utable else None)

#     result =[]

#     left = db.query(User,Branch).outerjoin(Branch)
#     right = db.query(User,Branch).outerjoin(User)
                
#     full = left.union(right).all()
    
#     for utable,bt in full:
#         result.append({
#                         "Branchid": bt.id if bt else None,
#                        "Branch_name":bt.name if bt else None,
#                        "User_id ": utable.id if utable else None,
#                        "UserName" :utable.full_name if utable else None,
#                        })
    
#     return result


# @router.get("/fullJoin")
# async def full_join(db:db_dependency):

#     left_Join = db.query(User,Wallet).outerjoin(Wallet)
#     right_Join = db.query(User,Wallet).outerjoin(User)

#     left_and_right = left_Join.union(right_Join).all()

#     result = [] 
#     for user_table, wallet_table in left_and_right:
#         result.append({
#                         "userId": user_table.id if user_table else None,
#                         "user name": user_table.full_name if user_table else None,
#                         "WalletId": wallet_table.id if wallet_table else None,
#                         "wallet_Balance" : wallet_table.balance if wallet_table else None })
#     return result


# @router.get("/innerJoinInverse")
# async def sample_joins(db: db_dependency):
#     getrightJoin = db.query(User,Branch
#                             ).outerjoin(Branch,User.id == Branch.manager_id
#                                    ).filter(Branch.manager_id == None,
#                                             )
#     # result = []    
#     # for u,b in getrightJoin:
#     #     result.append({"userid": u.id if u else None,
#     #                    "user_name": u.full_name if u else None,
#     #                    "branch Id": b.id if b else None,
#     #                    "branch name": b.name if b else None
#     #                 })
#     getleftJoin = db.query(User,Branch
#                             ).outerjoin(User, Branch.manager_id == User.id
#                                    ).filter(User.id == None,
#                                             )
#     # result = []    
#     # for u,b in getleftJoin:
#     #     result.append({"userid": u.id if u else None,
#     #                    "user_name": u.full_name if u else None,
#     #                    "branch Id": b.id if b else None,
#     #                    "branch name": b.name if b else None
#     #                 })
    
#     left_right = getrightJoin.union(getleftJoin).all()
#     result = []

#     for u,b in left_right:
#         result.append({"userid": u.id if u else None,
#                        "user_name": u.full_name if u else None,
#                        "branch Id": b.id if b else None,
#                        "branch name": b.name if b else None
#                     })

#     return result



# @router.get("/leftouterjoinInverse")
# async def sample_joins(db: db_dependency):

#     getrightJoin = db.query(User
#                             ).outerjoin(Branch,User.id == Branch.manager_id
#                                    ).filter(Branch.manager_id == None,
#                                             ).all()
    #   result = []

#     for u in getrightJoin:
#         result.append({"user_id" : u.id,
#                        "user_name" : u.full_name})
#     return result    
    

# @router.get("/innerJoin")
# async def sample_joins(db: db_dependency):

#     getrightJoin = db.query(User,Branch
#                             ).outerjoin(Branch,User.id == Branch.manager_id
#                                    ).filter(Branch.manager_id == None,
#                                             )
    
#     getleftJoin = db.query(User,Branch
#                             ).outerjoin(User, Branch.manager_id == User.id
#                                    ).filter(Branch.manager_id == None,
#                                             )
#     left_right = getrightJoin.union(getleftJoin).all()
#     result = []

#     for u,b in left_right:
#         result.append({"userid": u.id if u else None,
#                        "user_name": u.full_name if u else None,
#                        "branch Id": b.id if b else None,
#                        "branch name": b.name if b else None
#                     })

#     return result


@router.get("/LeftOuterJoin")
async def left_outer_join(db:db_dependency):
    getInnerJoins =( 
                    db.query(Branch,
                        func.count(Parkingslotbooking.branch_id).label("parkingcount"))
                    .join(Branch, Parkingslotbooking.branch_id == Branch.id)
                    .group_by(Parkingslotbooking.branch_id)
                    # .filter(Parkingslotbooking.status == -1)
                    .all() )
# another type
    # getInnerJoins =( 
    #                 db.query(Branch)
    #                 .join(User, isouter= True)
    #                 .all() )
    result =[]
    for Bn,parkingcount in getInnerJoins:
        result.append({"Branch_id" : Bn.name,
                       "Parkingcount": parkingcount,
                    #    "Manager_id": ut.id if ut else None,
                    #    "Manager_name": ut.full_name if ut else None
                       })
    
    return result
