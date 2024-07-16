from fastapi import APIRouter, Form,HTTPException
from utils import db_dependency
from models import * 
from schemas import VehicleType
from sqlalchemy import or_
from datetime import datetime
from utils import vehicle_number_validation


router = APIRouter()

# 1). Add new vehicle
@router.post("/NewRegister")
async def register_new_vehicle(db : db_dependency, token : str,
                           vehicletype : VehicleType = Form(...),
                           vehicle_number : str = Form(...,description="TN 36 AA 0001"),
                           brand_name : str = Form(...),
                           vehicle_model :str = Form(...),
                           vehicle_color :str = Form(...)):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if not check_token:
        return {"status" : 0, "message" : "Invalied token Id"}
    
    if check_token.status != 1:
        return {"message":"Token ID is not Activate"} 
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    if check_token.status==1:

        if not vehicle_number_validation(vehicle_number):
            raise HTTPException(status_code=400, detail= "Indalied vehicle Number")
        
        if vehicletype:
            if vehicletype.value == "Bike":
                vehicle_type = 1
            elif vehicletype.value == "Car":
                vehicle_type = 2
        
        already_exist = db.query(Vehicle).filter(Vehicle.vehicletype_id == vehicle_type, 
                                                Vehicle.vehicle_number == vehicle_number,
                                                Vehicle.brand_name == brand_name,
                                                Vehicle.model == vehicle_model).first()

        if already_exist:
            return {"status" : 0, "message" : "This Vehicle Details is already exist"}
    
        db_vehicle = Vehicle(user_id = check_token.user_id,
                             vehicletype_id =  vehicle_type,
                             vehicle_number = vehicle_number,
                             brand_name = brand_name,
                             model = vehicle_model,
                             color = vehicle_color,
                             created_at = datetime.now(),
                             status = 1)
        
        db.add(db_vehicle)
        db.commit()

        return ({
            "status" : 1 ,
            "message" : "Vehicle Details is successfully create",
            "Vehicle_id" : db_vehicle.id,
            "User_ID" : db_vehicle.user_id,
            "Vehicle_number" : db_vehicle.vehicle_number,
        })
    
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })

# 2). List Vehicle
@router.get('/list')
async def list_vehicle(db:db_dependency,token : str,page_no : int = 1,size:int = 10):

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

    all_vehicle=db.query(Vehicle).all()

    if (len(all_vehicle)) % size == 0:
        total_page = int((len(all_vehicle))/size)
    else:
        total_page=((len(all_vehicle))//size+1)

    if total_page < page_no:
        return {"message" : f"Only {total_page} pages available" }

    line_no=(page_no-1)*size
    db_vehicle=db.query(Vehicle).offset(line_no).limit(size).all()
   
    # page_details=( "Page_no:", page_no, "Total_page:", 
    #               total_page,"Total_no_records:", len(all_customer))
    for vehicle_data in db_vehicle:
        result.append(
            {
                "UserID" : vehicle_data.user_id,
                "User Name" : vehicle_data.user.full_name,
                "Vehicle Number" :vehicle_data.vehicle_number ,
                "Vehicle Color" : vehicle_data.color
            })
    if not result:
        return {"message" : "Result not found"}
    
    return result

# 3). update vehicle details
@router.put('/update_details')

async def update_vehicle(db: db_dependency, token:str ,
                         vehicle_id : int,
                         vehicletype_id : int = Form(None),
                         vehicle_number : str = Form(None),
                         brand_name : str = Form(None),
                         vehicle_model : str = Form(None),
                         vehicle_color : str = Form(None)):
    checkToken = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if checkToken.expires_at < datetime.now():
        checkToken.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if checkToken.status ==1:
        GetVehicle=db.query(Vehicle).filter_by(id = vehicle_id,
                                               user_id = checkToken.user_id,
                                               ).first()

        if not GetVehicle:
            return {"message": "Invalied Vahicle id"}
        
        if not (vehicletype_id or vehicle_number or brand_name or vehicle_model or vehicle_color):
            return {"status" : 0, "message" : "Please, Enter your updated data"}

        if vehicletype_id:
            GetVehicle.vehicletype_id = vehicletype_id
        
        if vehicle_number:
            if not vehicle_number_validation(vehicle_number):
                raise HTTPException(status_code=400, detail= "Indalied vehicle Number")

            GetVehicle.vehicle_number = vehicle_number

        if brand_name:
            GetVehicle.brand_name = brand_name
        
        if vehicle_model:
            GetVehicle.model = vehicle_model

        if vehicle_color:
            GetVehicle.color =  vehicle_color
        
        if not (vehicle_number or vehicletype_id or brand_name or vehicle_color or vehicle_model):
            return {"message" : "No data is updated"}
        
        db.commit()
        db.refresh(GetVehicle)
        
        return ({
            "VehicleID" : GetVehicle.id,
            "UserID" : GetVehicle.user_id,
            "Vehicle Number" : GetVehicle.vehicle_number,
            "Vehicle Model" : GetVehicle.model
        })
    
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })

#4). Delete Vehicle Id
@router.post('/delete_vehicle')
async def delete_vehicle(token : str, db : db_dependency,
                         vehicle_id : int = Form(...),
                        #  user_id : int = Form(...),
                        #  vehicle_model : str = Form(...),
                        #  vehicle_number : str = Form(...),
                          ):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    

    if check_token.status ==1:
        db_vehicle=db.query(Vehicle).filter(Vehicle.id==vehicle_id,
                                       Vehicle.user_id==check_token.user_id,
                                    #    Vehicle.status == 0
                                    #    Vehicle.model == vehicle_model,
                                    #    Vehicle.vehicle_number == vehicle_number,
                                       ).first()
        
        if db_vehicle:
            if db_vehicle.status == 1:
                db_vehicle.status = 0
                db.commit()
                return {"message" : f"Vehicle_ID {db_vehicle.id} successfully deactivated."}        
            elif db_vehicle.status == 0 :
                return {"message" : f"Vehicle_id {db_vehicle.id} is already deleted"}
            
        return {"message" :"This is not Your registed Vehicle ID"}

        
    return ({
        "status" : 0, "message" : "Token ID is not Activate"
    })


#5). user check number of bike and car register:
@router.post('/ListMyVehiclies')
async def list_user_vehicle(token : str, db : db_dependency):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    # if check_token.status==1:
    #     db_user = db.query(User).filter(User.id==check_token.user_id,
    #                                   User.status==1,
    #                                   or_(User.user_type==1, User.user_type==2)).first()
        
    #     if not db_user:
    #         return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
    result = []
    getvehicle = db.query(Vehicle).filter(Vehicle.user_id == check_token.user_id).order_by(Vehicle.vehicletype_id).all() 

    if not getvehicle:
        return {"message" : "You not register any Vehicle"}

    for row in getvehicle:
        if row.vehicletype_id == 1:
            result.append({"vehicle ID" : row.id,
                           'Bike number' : row.vehicle_number,
                           "Brand" : row.brand_name,
                           "model" : row.model,})
        elif row.vehicletype_id == 2:
            result.append({"vehicle ID" : row.id,
                           "Car number": row.vehicle_number,
                           "Brand" : row.brand_name,
                           "model" : row.model,})

    return {"UserID" : check_token.user_id,
            "Vehicle Details" : result}
