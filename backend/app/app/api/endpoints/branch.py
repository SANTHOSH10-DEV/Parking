from fastapi import HTTPException,Depends, APIRouter,Body, Form
from utils import db_dependency,phone_number_validation
from models import * 
from datetime import datetime, timedelta, date
from sqlalchemy import or_,func

router=APIRouter()

#1). Add new Branch
@router.post("/new_branch")
async def new_branch(db:db_dependency, token : str,
                     name : str = Form(...),
                     phone_number : str = Form(...),
                     address : str = Form(...),
                     manager_id : int = Form(None),
                     maximum_number_of_bike : int = Form(...),
                     maximum_number_of_car : int = Form(...)):

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
        
        already_exist = db.query(Branch).filter(Branch.name == name,Branch.status == 1).first()

        if already_exist:
            return {"status" : 0, "message" : "This Branch name is already exist"}
        
        if not phone_number_validation(phone_number):
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        already_exist_phone_number=db.query(Branch).filter(Branch.phone_number == phone_number,
                                                           Branch.status == 1).first()
    
        if already_exist_phone_number:
            return {"status" : 0 , "message" : "Phone number is aleady exist"}
        
        if manager_id:
            chechManager = db.query(User).filter(User.id == manager_id,
                                                 User.user_type == 3,
                                                 User.status == 1).first()  
            if not chechManager:
                return {"message" : "Invalied managaer ID"}
            
            db_branch = Branch(name = name, 
                            phone_number = phone_number,
                            address = address,
                            manager_id = manager_id,
                            maximum_no_bike = maximum_number_of_bike,
                            maximum_no_car = maximum_number_of_car,
                            created_at = datetime.now(),
                            status=1)
            db.add(db_branch)
            db.commit()

            return ({
                "status" : 1, "message" : "Branch successfully created",
                "branch_Id" : db_branch.id,
                "Branch Name" : db_branch.name 
                })
    
        db_branch = Branch(name = name, 
                        phone_number = phone_number,
                        address = address,
                        manager_id = manager_id,
                        maximum_no_bike = maximum_number_of_bike,
                        maximum_no_car = maximum_number_of_car,
                        updated_date = None,
                        created_at = datetime.now(),
                        status=1)
        db.add(db_branch)
        db.commit()

        return ({
                "status" : 1, "message" : "Branch successfully created",
                "branch_Id" : db_branch.id,
                "Branch Name" : db_branch.name 
                })
    return {"message":"Token ID is not Activate"} 

#2). LIST Braches
@router.post("/ListBranch")
async def list_branch(db : db_dependency, token : str,size : int = 10, page_no : int = 1 ):
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token,
                                             ApiTokens.status == 1).first()

    if not check_token:
        return {"message":"Token ID is not Activate"} 


    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.status==1:
        # db_user = db.query(User).filter(User.id==check_token.user_id,
        #                               User.status==1,
        #                               or_(User.user_type==1, User.user_type==2)).first()
        
        # if not db_user:
        #     return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
        
        all_branch=db.query(Branch).all()
            
        if (len(all_branch)) % size == 0:
            total_page = int((len(all_branch))/size)
        else:
            total_page=((len(all_branch))//size+1)

        if total_page < page_no:
            return {"message" : f"Only {total_page} pages available" }

        line_no=(page_no-1)*size
        db_branch=db.query(Branch).filter(Branch.status == 1).offset(line_no).limit(size).all()

        result=[]
        for Single_branch in db_branch:
            result.append({"BranchID":Single_branch.id,
                           "Branch Name" : Single_branch.name,
                           "Phone_number": Single_branch.phone_number,
                           "Address" : Single_branch.address
                           })
        if not result:
            return {"message" : "Result not found"}
        
        return result
    
#3). update Branch details
@router.post("/update_branch")
async def update_branch(db:db_dependency,token : str,
                        branch_id : int,
                        name : str = Form(None),
                        phone_number : str = Form(None),
                        address : str = Form(None),
                        manager_id : int = Form(None),
                        maximum_number_of_bike : int = Form(None),
                        maximum_number_of_car : int = Form(None)):

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
        
        already_exist = db.query(Branch).filter(Branch.id==branch_id).first()

        if not already_exist:
            return {"status" : 0, "message" : "This Branch_id is not found"}
        
        if name:
            new_name_vld= db.query(Branch).filter(Branch.name == name).first()
            if new_name_vld:
                return {"message" : "Branch name is Already exist"}
            already_exist.name = name

        if phone_number:
            if not phone_number_validation(phone_number):
                raise HTTPException(status_code=400, detail="Invalid phone number")
   
            already_exist_phone_number=db.query(Branch).filter(Branch.phone_number==phone_number).first()
            if already_exist_phone_number:
                return {"status" : 0 , "message" : "Phone number is aleady exist"}

            already_exist.phone_number = phone_number

        if manager_id:
            chechManager = db.query(User).filter(User.id == manager_id,
                                                 User.user_type == 3,
                                                 User.status == 1).first()  
            if not chechManager:
                return {"message" : "Invalied managaer ID"}      
            already_exist.manager_id = manager_id      

        if address:
            already_exist.address = address
        
        if maximum_number_of_bike:
            already_exist.maximum_no_bike = maximum_number_of_bike

        if maximum_number_of_car :
            already_exist.maximum_no_car = maximum_number_of_car 

        if not (name or phone_number or address or manager_id or maximum_number_of_bike or maximum_number_of_car):
            return {"message" : "No data is updated"}
        
        already_exist.updated_date = datetime.now()

        db.commit()
 
        return ({
            "status" : 1, "message" : "Branch details successfully updated",
            "branch_Id" : already_exist.id, "Branch Name" : already_exist.name,
            "Phone Number" : already_exist.phone_number, "Address" : already_exist.address,
            "Maximum number of bike parking" : already_exist.maximum_no_bike,
            "maximum number of car parking " : already_exist.maximum_no_car,
        })
    return {"message":"Token ID is not Activate"} 

#4). Delete brach Id
@router.post('/delete_branch')
async def delete_branch(token : str, db : db_dependency,
                        branch_id : int = Form(...),):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token,ApiTokens.status==1).first()

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status": 0, "message" : 'Your session has expired. Please, Sign-in again Your ID'})

    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.status ==1:
        getBranch=db.query(Branch).filter(Branch.id==branch_id,
                                       Branch.status == 1).first()
        
        if not getBranch:
            return {"message" : "Invalied branch id"}
        
        getBranch.status = 0
        
        db.commit()

        return {"message" : f"Branch_ID {branch_id}  successfully deleted."}

#5). particular branch income
@router.post("/BranchIncome")
async def branch_income(db : db_dependency, token : str,
                        # branch_id : int = Form(...),
                        fromdate : date = Form(...),
                        todate : date = Form(...)):
    
    check_token = db.query(ApiTokens).filter(ApiTokens.token==token).first()

    if not check_token:
        return {"status":0,"message": "Invalied token ID"}
    
    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    # if parking time is expire,it will update that status 
    GetParkingdata = db.query(Parkingslotbooking).filter(Parkingslotbooking.status == 1).all()
    for single_row in GetParkingdata:
        single_row.parking_out_time < datetime.now()
        single_row.status = -1
        db.commit()

    if check_token.status==1:
    
        db_user = db.query(User).filter(User.id==check_token.user_id,
                                      User.status==1,
                                    #   or_(User.user_type==1, 
                                    #       User.user_type==2,
                                          User.user_type==3).first()
        
        if not db_user:
            return {"status" : 0, "message" : "Accessed only by 'Managers' "}
        
        # to check same branch manager or other branch manager:
        if db_user.user_type==3:
            getBranch = db.query(Branch).filter(Branch.manager_id == check_token.user_id).first()
            
            one_day=timedelta(days=1)
            f_date=fromdate
            # f_date=fromdate+one_day
            t_date=todate+one_day
            if not f_date < t_date:
                return {"message": "Invalied from_date or to_date"}
            
            getDetails = db.query(func.sum(Parkingslotbooking.fees).label('amount')
                                  ).filter(Parkingslotbooking.branch_id == getBranch.id,
                                           Parkingslotbooking.booking_time.between(f_date, t_date),
                                           Parkingslotbooking.status == -1,
                                           ).group_by(Parkingslotbooking.branch_id).first()
            if not getDetails:
                return{"message": "result not found"}
            
            return {"Branch ID" : getBranch.id,
                    "Branch Name" : getBranch.name,
                    "Total Amount" : getDetails.amount}
    
    return {"status":0, "message":"Your session has expired. Please, Sign-in again"}
    
# 6). Each branch capacity
@router.post("/AllBranchCapacity")
async def list_all_branch_capacity(db : db_dependency, token : str):

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
                                   or_(User.user_type==1,User.user_type==2)).first()
    if not user:
        return {"status" : 0, "message": "Accessed only by 'SuperAdmin' or 'Admin'."}

    result =[]
    getBranches = db.query(Branch).all()

    for singlebranch in getBranches:
        result.append({"BranchID" : singlebranch.id,
                       "Bike parking count" : singlebranch.maximum_no_bike,
                       "Car parking count" : singlebranch.maximum_no_car})
        
    if not result:
        return {"message" : "Result not found"}

    return result
