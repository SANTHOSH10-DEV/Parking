from fastapi import APIRouter, Form
from utils import db_dependency
from models import * 
from sqlalchemy import func,or_,desc,case
from datetime import datetime,date,timedelta

router = APIRouter()

# 1). BranchID wise total amount:
@router.post("/BranchIncome")
async def branch_income(db : db_dependency, token : str,
                              fromdate : date = Form(...), todate : date = Form(...)):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
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

    if check_token.status==1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        

        one_day=timedelta(days=1)
        f_date=fromdate
        # f_date=fromdate+one_day
        t_date=todate+one_day

        if not f_date < t_date:
            return {"message" : "Invalied from_date or to_date."}

        result =[]
        GetBranch= db.query(Parkingslotbooking.branch_id,Branch.name,
                            func.sum(Parkingslotbooking.fees).label("cost"),
                            func.count(Parkingslotbooking.id).label("usercount"),
                            ).join(Branch,Parkingslotbooking.branch_id == Branch.id
                                   ).filter(Parkingslotbooking.booking_time.between(f_date, t_date),
                                            Parkingslotbooking.status == -1,
                                            ).group_by(Parkingslotbooking.branch_id
                                                       ).order_by(desc("cost")).all()
        
        for b_id, b_name, cost, usercount in GetBranch:
            result.append({"Branch_ID" : b_id,
                           "Branch Name" : b_name,
                           "UserCount" : usercount,
                           "Total amount" : cost,
                           "Form Date": f_date,
                           "To date": todate})
        if not result:
            return {"message" : "Result not found"}
            
        return result
    
# 2). BranchID wise most of user :
@router.post("/BranchCustomers")
async def user_count(db : db_dependency, token : str,
                              fromdate : date , todate : date ):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
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

    if check_token.status==1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        one_day=timedelta(days=1)
        f_date=fromdate
        # f_date=fromdate+one_day
        t_date=todate+one_day

        if not f_date < t_date:
            return {"message" : "Invalied from_date or to_date."}
        
        result =[]
        GetBranch = db.query(Parkingslotbooking.branch_id,func.count(Parkingslotbooking.branch_id).label("count")
                             ).filter(Parkingslotbooking.booking_time.between(f_date,t_date),
                                      Parkingslotbooking.status == -1,
                                      ).group_by(Parkingslotbooking.branch_id
                                        ).order_by(desc("count")).all()
        
        for branch_id, count in GetBranch:
            result.append({"BranchID" : branch_id,
                           "UserCount" : count})
        if not result:
            return {"message" : "Result not found"}
        
        return result
    
# 3). BranchID wise parking cancel :
@router.post("/CancelParking")
async def list_cancel_parking(db : db_dependency, token : str,
                              fromdate : date, todate : date ):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})
    
    # if parking time is expire,it will update that status ``
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
    for single_row in GetParkingdata:
        if single_row.parking_out_time < datetime.now():
            single_row.status = -1
            db.commit()

    if check_token.status==1:
        #checking SuperAdmin or admin:
        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        one_day=timedelta(days=1)
        f_date=fromdate
        # f_date=fromdate+one_day
        t_date=todate+one_day

        if not f_date < t_date:
            return {"message" : "Invalied from_date or to_date."}
        result =[]

        #to filter canceled booking in Branch wise:
        GetBranch = db.query(Parkingslotbooking.branch_id,func.count(Parkingslotbooking.branch_id).label("count")
                             ).filter(Parkingslotbooking.booking_time.between(f_date,t_date),
                                      Parkingslotbooking.status == 0,
                                      ).group_by(Parkingslotbooking.branch_id
                                        ).order_by(desc("count")).all()
        
        for branch_id, count in GetBranch:
            result.append({"Branch ID" : branch_id,
                           "Canceled booking Count" : count})
        if not result:
            return {"Status" : 0, "message": "Canceled Data not found"}
        
        return result

# 4). List current status for all branch
@router.post("/BranchStatus")
async def all_branch_current_status(db : db_dependency, token : str):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()
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

    if check_token.status==1:

        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                      or_(User.user_type==1, User.user_type==2)).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}

    result = []

    get_Branch = db.query(Parkingslotbooking.branch_id,
                          Branch.name,
                          func.sum(case((Vehicle.vehicletype_id == 2, 1), else_=0)).label("carcount"),
                          func.sum(case((Vehicle.vehicletype_id == 1, 1), else_=0)).label("bikecount")
                          ).join(Branch, Parkingslotbooking.branch_id == Branch.id
                          ).join(Vehicle, Parkingslotbooking.vehicle_id == Vehicle.id
                          ).filter(Parkingslotbooking.status == 1,
                                   Vehicle.vehicletype_id.in_([1, 2])
                                   ).group_by(Parkingslotbooking.branch_id,
                                            ).order_by(Parkingslotbooking.branch_id,
                                                        ).all()

    for branch_id, branch_name, carcount, bikecount in get_Branch:
        result.append({
            "Branch id": branch_id,
            "Branch Name": branch_name,
            "car parking": carcount,
            "bike parking": bikecount
        })

    if not result:
        return {"message" : "No one Vehicle is Parked now"}
    
    return result
