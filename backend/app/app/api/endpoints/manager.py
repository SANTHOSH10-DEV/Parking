from fastapi import APIRouter, Form,HTTPException
from sqlalchemy import func, or_,case
from utils import db_dependency
from schemas import Payment
from models import * 
from datetime import datetime,date,time,timedelta
from utils import time_convert

router = APIRouter()


# #1). branch parking list
# @router.post("/ListParking")
# async def list_parking_details(db : db_dependency, token : str,page_no:int=1,size:int=10):
    
#     check_token = db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status == 1).first()

#     if not check_token:
#         return {"status" : 0, "message" : "Token ID is not Activate"}
    
#     if check_token.expires_at < datetime.now():
#         check_token.status = -1
#         db.commit()
#         return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
#      # if parking time is expire,it will update that status ``
#     GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
#     for single_row in GetParkingdata:
#         if single_row.parking_out_time < datetime.now():
#             single_row.status = -1
#             db.commit()

#     result=[]

#     branch_manager= db.query(Branch).filter(Branch.manager_id == check_token.user_id).first()

#     if not branch_manager:
#         return {"status" : 0, "message" : "Only access to permision for managers"}

#     all_data=db.query(Parkingslotbooking).filter(Parkingslotbooking.branch_id == branch_manager.id,
#                                                     Parkingslotbooking.status == 1).all()
#     if  not all_data:
#         return {"message" : "No one Vehicle is Parked now"}

#     if (len(all_data)) % size == 0:
#         total_page = int((len(all_data))/size)
#     else:
#         total_page=((len(all_data))//size+1)

#     if total_page < page_no:
#         return {"message" : f"Only {total_page} pages available" }

#     line_no=(page_no-1)*size

#     Pagenation=db.query(Parkingslotbooking).filter(Parkingslotbooking.branch_id == branch_manager.id,
#                                                     Parkingslotbooking.status == 1).offset(line_no).limit(size).all()


#     for onerow in Pagenation:
#         result.append({
#             #  "BranchID" : onerow.branch_id,
#              "BookingTime" : onerow.booking_time,
#              "ParkingInTime" : onerow.parking_in_time,
#              "ParkingOutTime" : onerow.parking_out_time,
#              "ParkingRent": onerow.fees},
#         )
#     return {"BranchID" : branch_manager.id,
#             # "UserID" : check_token.user_id,
#             "BookingDetails" : result}


# 2). parking list vehicle type count:(branch current status)
@router.post("/CurrentStatus")
async def branch_current_status(db : db_dependency, token : str):

    check_token = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if not check_token:
        return {"status" : 0, "message" : "Invalied token Id"}
    
    if check_token.status != 1:
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # to check user is SuperAdmin or Admin
    user=db.query(User).filter(User.id==check_token.user_id,
                                   User.status==1,
                                   User.user_type== 3).first()
    if not user:
        return {"status" : 0, "message": "Accessed only by 'Manager.' "}
    
    getBranch = db.query(Branch).filter(Branch.manager_id == check_token.user_id).first()

    bikeCount = db.query(func.count(Parkingslotbooking.id).label('bike_count')
                        ).join(Vehicle,Parkingslotbooking.vehicle_id == Vehicle.id
                            ).filter(Vehicle.vehicletype_id == 1,
                                     Parkingslotbooking.branch_id == getBranch.id,
                                     Parkingslotbooking.status == 1).scalar()
    
    carCount = db.query(func.count(Parkingslotbooking.id).label('car_count')
                        ).join(Vehicle,Parkingslotbooking.vehicle_id == Vehicle.id
                            ).filter(Vehicle.vehicletype_id == 2,
                                     Parkingslotbooking.branch_id == getBranch.id,
                                        Parkingslotbooking.status == 1).scalar()

    if bikeCount !=0 and carCount !=0:
        return ({'BranchID' :getBranch.id,
                    "Bike Parked count" : bikeCount,
                    "Car Parked_count" : carCount})
        
    elif carCount == 0 and bikeCount == 0:
        return {"message" : "No one Vehicle is cancled booking"}
        
    elif bikeCount == 0 and carCount != 0:
        return ({'BranchID' :getBranch.id,
                    "Car Parked_count" : carCount})
        
    elif carCount ==0 and bikeCount != 0:
        return ({'BranchID' :getBranch.id,
                    "Bike Parked count" : bikeCount})

#3). list cancled booking for branch
@router.post("/CanceledDetails")
async def canceled_booking_status(db : db_dependency, token : str,
                                  fromdate : date = Form(...), todate : date = Form(...) ):

    check_token = db.query(ApiTokens).filter(ApiTokens.token == token).first()

    if not check_token:
        return {"status" : 0, "message" : "Invalied token Id"}
    
    if check_token.status != 1:
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # to check user is SuperAdmin or Admin
    user=db.query(User).filter(User.id==check_token.user_id,
                                   User.status==1,
                                   User.user_type== 3).first()
    if not user:
        return {"status" : 0, "message": "Accessed only by 'Manager.' "}
    
    getBranch = db.query(Branch).filter(Branch.manager_id == User.id).first()

    getCanledBooking = db.query(Parkingslotbooking
                                ).filter(Parkingslotbooking.branch_id == getBranch.id)
    one_day=timedelta(days=1)
    f_date=fromdate
    # f_date=fromdate+one_day
    t_date=todate+one_day

    cancelBikeCount = db.query(func.count(Parkingslotbooking.id).label('bike_count')
                        ).join(Vehicle,Parkingslotbooking.vehicle_id == Vehicle.id
                            ).filter(Vehicle.vehicletype_id == 1,
                                     Parkingslotbooking.branch_id == getBranch.id,
                                     Parkingslotbooking.booking_time.between(f_date,t_date),
                                     Parkingslotbooking.status == 0).scalar()
    
    cancelCarCount = db.query(func.count(Parkingslotbooking.id).label('car_count')
                        ).join(Vehicle,Parkingslotbooking.vehicle_id == Vehicle.id
                            ).filter(Vehicle.vehicletype_id == 2,
                                     Parkingslotbooking.branch_id == getBranch.id,
                                     Parkingslotbooking.booking_time.between(f_date,t_date),
                                     Parkingslotbooking.status == 0).scalar()
    
    if cancelBikeCount !=0 and cancelCarCount !=0:
        return ({'BranchID' :getBranch.id,
                    "Bike Parked count" : cancelBikeCount,
                    "Car Parked_count" : cancelCarCount})
        
    elif cancelCarCount == 0 and cancelBikeCount == 0:
        return {"message" : "No one Vehicle is Parked now"}
        
    elif cancelBikeCount == 0:
        return ({'BranchID' :getBranch.id,
                    "Car Parked_count" : cancelCarCount})
        
    elif cancelCarCount ==0:
        return ({'BranchID' :getBranch.id,
                    "Bike Parked count" : cancelBikeCount})
    