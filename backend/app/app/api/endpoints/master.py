from fastapi import APIRouter, Form
from utils import db_dependency
from models import * 
from schemas import VehicleType
from sqlalchemy import or_
from datetime import datetime

router = APIRouter()

# 1). Add new vehicletype
@router.post("/new_vehicletype")
async def new_vehicle_type(db : db_dependency, 
                           token : str,
                           name : str = Form(...),
                           amount_per_hour : float = Form(...)):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

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
        
        already_exist = db.query(Vehicletype).filter(Vehicletype.name==name, 
                                                Vehicletype.amount_per_hour==amount_per_hour).first()

        if already_exist:
            return {"status" : 0, "message" : "This Branch name is already exist"}
        
        db_vehicletype = Vehicletype(name = name,
                                     amount_per_hour = amount_per_hour,
                                     status = 1,
                                     date = datetime.now())
        db.add(db_vehicletype)
        db.commit()

        return ({
            "status" : 1 ,
            "message" : "VehicleType is successfully create",
            "VehicleType_id" : db_vehicletype.id,
            "VehicleType_name" : db_vehicletype.name
        })
    
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })

# 2). LIST vehicle_type
@router.post("/ListVehicleType")
async def list_vehicle_type(db : db_dependency, 
                            token : str, 
                            size : int = 5, 
                            page_no : int = 1 ):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

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
        
        all_vehicletype=db.query(Vehicletype).all()
            
        if (len(all_vehicletype)) % size == 0:
            total_page = int((len(all_vehicletype))/size)
        else:
            total_page=((len(all_vehicletype))//size+1)

        if total_page < page_no:
            return {"message" : f"Only {total_page} pages available" }

        line_no=(page_no-1)*size
        db_vehicletype=db.query(Vehicletype).offset(line_no).limit(size).all()

        result=[]
        for Single in db_vehicletype:
            result.append({"VehicleTypeID":Single.id,
                           "VehicleType Name" : Single.name,
                           "AmountPerHour" : Single.amount_per_hour,
                           })
        if not result:
            return {"message" : "Result not found"}
        
        return result
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })


#3). update vehicletype details
@router.post("/update_vehicletype")
async def update_vehicletype(db:db_dependency,token : str,
                             vehicle_type : VehicleType ,
                             name : str = Form(None),
                             amount_per_hour : float = Form(None)
                             ):

    check_token = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if vehicle_type:
        if vehicle_type.value == "Bike":
            vehicletype_id = 1
        elif vehicle_type.value == "Car":
            vehicletype_id = 2

    if check_token.status==1:

        db_user = db.query(User).filter(User.id == check_token.user_id,
                                      User.status == 1,
                                      or_(User.user_type == 1, 
                                          User.user_type == 2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        db_vehicletype = db.query(Vehicletype).filter(Vehicletype.id==vehicletype_id).first()

        if not db_vehicletype:
            return {"status" : 0, "message" : "This VehicleType_id is not found"}
        
        if name:
            db_vehicletype.name = name

        if amount_per_hour:
            db_vehicletype.amount_per_hour = amount_per_hour

        if not (name or amount_per_hour):
            return {"message" : "No data is updated"}    
        db.commit()
 
        return ({
            "status" : 1, "message" : "Vehicle type details successfully updated",
            "Vehicle type_Id" : db_vehicletype.id, "Vehicle type Name" : db_vehicletype.name,
            "Amount per Hours" : db_vehicletype.amount_per_hour
        })
    return {"message":"Token ID is not Activate"} 

#4). Delete Vehicle type Id
@router.post('/delete_vehicle_type')
async def delete_vehicle_type(token : str, db : db_dependency,
                        vehicletype_id : int = Form(...),
                        vehicletype_name : str = Form(...) ):
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if check_token.status==1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
    user=db.query(Vehicletype).filter(Vehicletype.id==vehicletype_id,
                                       Vehicletype.name==vehicletype_name,
                                       Vehicletype.status == 1).first()
        
    if user:
        user.status = 0
            
        db.commit()

        return {"message" : "UserID successfully deactivated."}

    return ({
        "status" : 0, "message" : "Invalied vehicle type details"
    })

#5). user to check number of bike and car register:
@router.post('/register vehicle')
async def list_all_vehicle(token : str, db : db_dependency):
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if check_token.status==1:
        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        result = []
        getvehicle = db.query(Vehicle).order_by(Vehicle.user_id).all() 

        for row in getvehicle:

            if row.vehicletype_id == 1:
                result.append({"userid": row.user_id,
                               "bike number" : row.vehicle_number})

            elif row.vehicletype_id == 2:
                result.append({"userid": row.user_id,
                               "car number" : row.vehicle_number})
                
        if not result:
            return {"message" : "Result not found"}
        
        return result
    