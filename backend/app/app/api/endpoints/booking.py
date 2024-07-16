from fastapi import APIRouter, Form,HTTPException
from sqlalchemy import func, or_,case
from utils import db_dependency
from schemas import Payment,ListBranch
from models import * 
from datetime import datetime,date,time,timedelta
from utils import time_convert



router = APIRouter()

# 1). new parking :
@router.post("/vehiclebooking")
async def vehicle_booking(db : db_dependency, token : str,
                        #   branch : ListBranch = Form(...),
                          branch_id : int = Form(...),
                          vehicle_id : int = Form(...),
                        #   vehicle_type : str = Form(...),
                          parking_in_time : datetime = Form(...),
                          parking_exit_time : datetime = Form(...),
                          payment: Payment = Form(...)):
    
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,
                                           ApiTokens.status==1).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    if parking_in_time :
        if parking_in_time > datetime.now():
            if not parking_exit_time > parking_in_time:
                return {"status" : 0, "message" : "Invalide parking exit time"}
        elif not parking_in_time > datetime.now():
            return {"status" : 0, "message" : "Invalide parking in time"}
        
    # # if parking time is expire,it will update the status 
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()

    for single_row in GetParkingdata:
        if single_row.parking_out_time < datetime.now():
            single_row.status = -1
            db.commit()
 
    if branch:
        pass
        # To get branch_id 
        # getBranch = db.query(Branch).filter(Branch.name == branch.value,
        #                                     Branch.status ==1).first()
        # branch_id = getBranch.id
        
    #parking place is alvailable or not 
    db_vehicle = db.query(Vehicle).filter_by(id = vehicle_id, user_id = check_token.user_id).first()

    # to check current user's registered vehicle or not
    if not db_vehicle:
        return {"status" : 0, "message": "This vehicle id is register by another UserID"}

    db_vehicle_type = db.query(Vehicletype).filter_by(id = db_vehicle.vehicletype_id).first()

    GetBranchID = db.query(Branch).filter(Branch.id==branch_id,Branch.status==1).first()

    if not GetBranchID:
        return {"status" : "Invalied branch ID"}
    
    already_booked= db.query(Parkingslotbooking).filter(Parkingslotbooking.user_id==check_token.user_id,
                                                        Parkingslotbooking.vehicle_id ==  vehicle_id,
                                                        Parkingslotbooking.status ==1).first()

    if already_booked:

        if already_booked.parking_out_time < datetime.now():
            already_booked.status = -1
            db.commit()
            pass
    
        elif not already_booked.parking_out_time < parking_in_time:
            return {"status" : 0, "message" : "You alread booked in this time"}

    
    # #to check vehicle parking is available or not
    if db_vehicle_type.name == "bike" :
        # count = db.query(func.count(Parkingslotbooking.id)
    #                      ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
    #                             ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
    #                                    ).filter(Parkingslotbooking.branch_id == branch_id
    #                                             ).filter(Parkingslotbooking.status == 1
    #                                                      ).filter(Vehicletype.name == 'bike'
    #                                                               ).scalar()
        count = db.query(func.count(Parkingslotbooking.id)
                         ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
                                ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
                                       ).filter(Parkingslotbooking.branch_id == branch_id,
                                                Parkingslotbooking.status == 1,
                                                Vehicletype.name == 'bike',
                                                Parkingslotbooking.parking_in_time <= parking_in_time,
                                                Parkingslotbooking.parking_out_time >= parking_exit_time
                                                                  ).scalar()

        if GetBranchID.maximum_no_bike == count:

            return {"status" : 0, "message" : 'Parking area is not available'}

    # elif db_vehicle_type.name == "car" :
    #     count = db.query(func.count(Parkingslotbooking.id)
    #                      ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
    #                             ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
    #                                    ).filter(Parkingslotbooking.branch_id == branch_id
    #                                             ).filter(Parkingslotbooking.status == 1
    #                                                      ).filter(Vehicletype.name == 'car'
    #                                                               ).scalar()

    elif db_vehicle_type.name == "car" :
        count = db.query(func.count(Parkingslotbooking.id)
                         ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
                                ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
                                       ).filter(Parkingslotbooking.branch_id == branch_id,
                                                Parkingslotbooking.status == 1,
                                                Vehicletype.name == 'car',
                                                Parkingslotbooking.parking_in_time <= parking_in_time,
                                                Parkingslotbooking.parking_out_time >= parking_exit_time
                                                ).scalar()

        if GetBranchID.maximum_no_car == count:

            return {"status" : 0, "message" : 'Parking area is not available'}
    
    # calculate total parking hours
    total_hours = time_convert(parking_in_time,parking_exit_time)

    amount =  db_vehicle_type.amount_per_hour

    parking_rent = total_hours * amount


    # check the wallet amount for parking
    if payment.value == "wallet":
        
        db_wallet = db.query(Wallet).filter_by(user_id = check_token.user_id).first()  
        
        if not db_wallet:
            return {"status" : 0, "message" : "User don't have a wallet amount"}

        if db_wallet:

            if db_wallet.balance >= parking_rent:
                
                db_wallet.balance -= parking_rent
                db.commit()
            else:
                return {"status":0, "message" : "You don't have enough money in Yourt wallet"}

        parking = Parkingslotbooking(user_id = check_token.user_id,
                                    branch_id = branch_id,
                                    vehicle_id = vehicle_id,
                                    parking_in_time = parking_in_time,
                                    parking_out_time = parking_exit_time,
                                    fees = parking_rent,
                                    payment_type=payment,
                                    booking_time = datetime.now(),
                                    status = 1)

        db.add(parking)
        db.commit()
        return ({"status" : 1,
                "message" : "Parking successfully booking",
                "Parking ID" : parking.id,
                "cost of rent" : parking.fees,
                })
    parking = Parkingslotbooking(user_id = check_token.user_id,
                                branch_id = branch_id,
                                vehicle_id = vehicle_id,
                                parking_in_time = parking_in_time,
                                parking_out_time = parking_exit_time,
                                fees = parking_rent,
                                payment_type=payment,
                                booking_time = datetime.now(),
                                status = 1)

    db.add(parking)
    db.commit()
    return ({"status" : 1,
            "message" : "Parking successfully booking",
            "Parking ID" : parking.id,
            "cost of rent" : parking.fees
            })

# 2). cancel parking
@router.post("/CancelBooking")
async def cancel_booking(db : db_dependency, token : str,
                          park_booking_id : int = Form(...)):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token,
                                             ApiTokens.status == 1).first()

    if not check_token:
        return {"status" : 0, "message" : "Token ID is not Activate"}
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # # if parking time is expire,it will update that status 
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
    for single_row in GetParkingdata:
        if single_row.parking_out_time < datetime.now():
            single_row.status = -1
            db.commit()
    
    CheckBooking = db.query(Parkingslotbooking).filter(Parkingslotbooking.user_id == check_token.user_id,
                                                       Parkingslotbooking.id == park_booking_id,
                                                    #    Parkingslotbooking.branch_id == branch_id,
                                                    #  Parkingslotbooking.vehicle_id == vehicle_id,
                                                       Parkingslotbooking.status == 1).first()
    
    if not CheckBooking:

        return {"status" : 0, "message" : "Given date is invalied"}
    
    db_vehicle = db.query(Vehicle).filter_by(id = CheckBooking.vehicle_id).first()

    db_vehicle_type = db.query(Vehicletype).filter_by(id = db_vehicle.vehicletype_id).first()

    if CheckBooking.payment_type == "wallet" :

        if CheckBooking: 
            if CheckBooking.parking_in_time > datetime.now():
                CheckBooking.status = 0
                total_hours = time_convert(CheckBooking.parking_in_time,CheckBooking.parking_out_time)
                amount = db_vehicle_type.amount_per_hour
                parking_rent = total_hours * amount

                db_wallet = db.query(Wallet).filter_by(user_id = CheckBooking.user_id).first()  

                if db_wallet:

                    db_wallet.balance += parking_rent
                    db.commit()

                return {"status" : 1, "message" : "Vehicle Parking canceled succesffully "}

            else:
                return {"status" : 0, "message" : "before parking_in time only cancel is available"}

    if CheckBooking.parking_in_time > datetime.now():
        CheckBooking.status = 0
        # total_hours = time_convert(CheckBooking.parking_in_time,CheckBooking.parking_out_time)
        # amount = db_vehicle_type.amount_per_hour
        # parking_rent = total_hours * amount

        # db_wallet = db.query(Wallet).filter_by(user_id = CheckBooking.user_id).first()  

        # if db_wallet:

        #     db_wallet.balance += parking_rent
            # db.commit()
        db.commit()

        return {"status" : 1, "message" : "Vehicle Parking canceled succesffully "}

    else:
        return {"status" : 0, "message" : "before parking_in time only cancel is available"}

    # else:
    #     return {"status" : 0, "message" : "Given date is invalied"}

# 3). User Parking History
@router.post("/UserParkingHistory")
async def list_user_parking_history(db : db_dependency, 
                                    token : str,
                                    page_no:int=1,
                                    size:int=10):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token,
                                             ApiTokens.status == 1).first()

    if not check_token:
        return {"status" : 0, "message" : "Token ID is not Activate"}
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    result=[]

    all_data=db.query(Parkingslotbooking).filter(Parkingslotbooking.user_id == check_token.user_id,
                                                 Parkingslotbooking.status == -1).all()
    total_page = 0

    if (len(all_data)) % size == 0:
        total_page = int((len(all_data))/size)
    else:
        total_page=((len(all_data))//size+1)

    if total_page == 0:
        return {"message" : "result not found"}
    if total_page < page_no:
        return {"message" : f"Only {total_page} pages available" }

    line_no=(page_no-1)*size

    Pagenation=db.query(Parkingslotbooking
                        ).filter(Parkingslotbooking.user_id == check_token.user_id,
                                 Parkingslotbooking.status == -1).offset(line_no).limit(size).all()

    for onerow in Pagenation:
        result.append({
             "BranchID" : onerow.branch_id,
             "Booking ID" : onerow.id,
             "BookingTime" : onerow.booking_time,
             "ParkingInTime" : onerow.parking_in_time,
             "ParkingOutTime" : onerow.parking_out_time,
             "ParkingRent": onerow.fees},
        )

    current_booking_status = []
    current_booking=db.query(Parkingslotbooking
                        ).filter(Parkingslotbooking.user_id == check_token.user_id,
                                 Parkingslotbooking.status == 1).all()

    for onerow in current_booking:
        current_booking_status.append({
             "BranchID" : onerow.branch_id,
             "Booking ID" : onerow.id,
             "BookingTime" : onerow.booking_time,
             "ParkingInTime" : onerow.parking_in_time,
             "ParkingOutTime" : onerow.parking_out_time,
             "ParkingRent": onerow.fees},
        )
    if not current_booking_status:
        return {"UserID" : check_token.user_id,
            "BookedDetails" : result,}

    return {"UserID" : check_token.user_id,
            "BookedDetails" : result,
            "BookingDetails" : current_booking_status}
    
# 4). Parking Details 
@router.post('/ParkingDetails')
async def parking_details(token : str,db:db_dependency,
                          branch_id : int = Form(...),
                          page_no:int=1,size:int=10):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,
                                           ApiTokens.status==1).first()
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
    
    getBranch = db.query(Branch).filter(Branch.id == branch_id,
                                        Branch.status == 1).first()
    if not getBranch:
        return {"sttus" : "Invalied Branch Id"}
    
    result=[]

    all_parking=db.query(Parkingslotbooking).filter(Parkingslotbooking.branch_id == branch_id).all()
    total_page = 0
    if (len(all_parking)) % size == 0:
        total_page = int((len(all_parking))/size)
    else:
        total_page=((len(all_parking))//size+1)
    
    if total_page == 0:
        return {"message" : "No one vehicle is parked here"}

    if total_page < page_no:
        return {"message" : f"Only {total_page} pages available" }

    line_no=(page_no-1)*size
     
    pagination=db.query(Parkingslotbooking).filter(Parkingslotbooking.branch_id == branch_id).offset(line_no).limit(size).all()
    
    for row in pagination:
        result.append({
            "UserId" : row.user_id,
            "VehicleId" : row.vehicle_id,
            "Amount" : row.fees
        })
    return {"Branch Id" : branch_id,
            "BranchDetails": result}

# 5). Total parking availability in each branch :
@router.post("/CheckingParkingAvailablity")
async def availability_Checking(db : db_dependency, token : str,
                            #   branchName : ListBranch = Form(...),
                              branch_id : int = Form(...)):
    
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,
                                           ApiTokens.status==1).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # # if parking time is expire,it will update that status 
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
    for single_row in GetParkingdata:
        if single_row.parking_out_time < datetime.now():
            single_row.status = -1
            db.commit()

    getBranchID = db.query(Branch).filter(Branch.id == branch_id,
                                          Branch.status == 1).first()
    if not getBranchID:
        return {"status" : 0, "message" : "Invalied Branch Id "}
    # if branchName:
    #     if branchName.value == "Covai":
    #         branch_id = 1
    #     elif branchName.value == "Sathy":
    #         branch_id = 2
    if check_token.status==1:
        #checking SuperAdmin or admin:
        # db_user = db.query(User).filter(User.id==check_token.user_id,
        #                               User.status==1,
        #                               or_(User.user_type==1, User.user_type==2)).first()
        
        # if not db_user:
        #     return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        # bikeCount = db.query(func.count(Parkingslotbooking.id).label('bike_count')
        #                  ).join(Vehicle,Parkingslotbooking.vehicle_id == Vehicle.id
        #                         ).filter(Vehicle.vehicletype_id == 1,
        #                                  Parkingslotbooking.status == 1).first()

        # car_count = db.query(func.count(Parkingslotbooking.id)
        #                  ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
        #                         ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
        #                                ).filter(Parkingslotbooking.branch_id == branch_id,
        #                                         Parkingslotbooking.status == 1,
        #                                         Vehicletype.name == 'car').scalar()
        
        # bike_count = db.query(func.count(Parkingslotbooking.id)
        #                  ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
        #                         ).join(Vehicletype, Vehicle.vehicletype_id == Vehicletype.id
        #                                ).filter(Parkingslotbooking.branch_id == branch_id,
        #                                         Parkingslotbooking.status == 1,
        #                                         Vehicletype.name == 'bike').scalar()

        # get_branch=db.query(Branch).filter(Branch.id==branch_id,Branch.status==1).first()
    
        # available_bike=get_branch.maximum_no_bike - bike_count
        # available_car=get_branch.maximum_no_car - car_count

        car_bike_count = db.query(
                        func.count(case((Vehicle.vehicletype_id == 1, 1), else_=None)).label("bike_count"),
                        func.count(case((Vehicle.vehicletype_id == 2, 1), else_=None)).label("car_count"),
                        ).select_from(Parkingslotbooking
                                    ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
                                        ).filter(Parkingslotbooking.branch_id == branch_id,
                                                 Parkingslotbooking.status == 1).one()

        get_branch=db.query(Branch).filter(Branch.id==branch_id,Branch.status==1).first()
    
        available_bike=get_branch.maximum_no_bike - car_bike_count.bike_count
        available_car=get_branch.maximum_no_car - car_bike_count.car_count

        result = [{
            "BranchID": branch_id,
            "CarParkingAvailable": available_car,
            "BikeParkingAvailable": available_bike
        }]

        if not result:
            return {"message" : "Result not found"}

        return result

#6). check vehical booking:
@router.post("/CurrentStatus")
async def user_current_booking_status(db : db_dependency, token : str):

    check_token = db.query(ApiTokens).filter(ApiTokens.token==token,
                                             ApiTokens.status == 1).first()

    if not check_token:
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # if parking time is expire,it will update that status 
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
    for single_row in GetParkingdata:
        if single_row.parking_out_time < datetime.now():
            single_row.status = -1
            db.commit()
    
    result = []

    if check_token.status==1:

        getBooking = db.query(Parkingslotbooking).filter(Parkingslotbooking.user_id == check_token.user_id,
                                                      Parkingslotbooking.status==1).all()
        
        if not getBooking:
            return {"status" : 0, "message" : "Currently you are not booked any vehicle to park"}

        for row in getBooking:

            result.append({"Parking Branch" : row.branch_id,
                           "Park Booking Id" : row.id,
                           "vehicle number": row.vehicle.vehicle_number,
                           "Parking in time" : row.parking_in_time,
                           "parking out time" : row.parking_out_time,
                           })
    
    if not result:
            return {"message" : "Result not found"}
        
    return result

#7). user cancel list
@router.post("/UserListCancleBooking")
async def user_list_cancel_booking(token : str, db : db_dependency):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    result = []
    getBooking = db.query(Parkingslotbooking).filter(Parkingslotbooking.user_id == check_token.user_id,
                                                     Parkingslotbooking.status == 0).all()
    
    if not getBooking:
        return {"message" : "No cancellation history found"}
    for row in getBooking:
        result.append({"Branch Id" : row.branch_id,
                       "Canceled Booking Id" : row.id,
                      "Vehicle_number":row.vehicle.vehicle_number,
                      "booking Date": row.booking_time})
    
    if not result:
            return {"message" : "Result not found"}
    
    return result
