from fastapi import APIRouter, Form,UploadFile,File,HTTPException
from models import * 
from datetime import datetime
from core.config import settings
from utils import db_dependency,phone_number_validation

from sqlalchemy import func,or_
import tempfile

router = APIRouter()

@router.post("/import_new_branch")
async def import_new_branch(db : db_dependency,
                             token:str = Form(...),
                             uploaded_file:UploadFile=File(...,description="xlsx")):
    
    check_token=db.query(ApiTokens).filter(ApiTokens.token==token).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.status != 1:
        return {"status" : 0,
                "message" : "Sorry! your login session expired. please login again."}

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

    # check user type is admin or superadmin
    db_user = db.query(User).filter(User.id==check_token.user_id,
                                    User.status==1,
                                    or_(User.user_type==1, User.user_type==2)).first()
    
    if not db_user:
        return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}

    # UPLOAD FILE CODE(below on this line):

    allLeadData = []
    # file format checking code
    file_extension = uploaded_file.filename.split(".")[1]
    if not file_extension in ["xlsx"]:
        return {"status":0,"msg":"Invalid File Format"}
    
    # upload file read
    readDetails = await uploaded_file.read()    
    

    base_dir = settings.BASE_UPLOAD_FOLDER+"/"

    file_path = f"{base_dir}/{uploaded_file.filename}"
    # write upload data in new file
    f= open(file_path,"wb")
    f.write(readDetails)


    import pandas as pd

    excel_data = pd.read_excel(file_path)

    data = pd.DataFrame(excel_data)
    data = data.where(pd.notnull(data),None)

    leadCol =data.columns.to_list()

    headers = ["name","phone_number",
               "address","manager_id",
               "maximum_no_bike",
               "maximum_no_car",]
    
    for index,row in data.iterrows():
        index += 1

        name = str(row["name"]) if not pd.isna(row["name"]) else None
        phone_number = str(row["phone_number"]) if not pd.isna(row["phone_number"]) else None
        address = str(row["address"]) if not pd.isna(row["address"]) else None
        manager_id = str(row["manager_id"]) if not pd.isna(row["manager_id"]) else None
        maximum_no_bike = str(row["maximum_no_bike"]) if not pd.isna(row["maximum_no_bike"]) else None
        maximum_no_car = str(row["maximum_no_car"]) if not pd.isna(row["maximum_no_car"]) else None


        # imported file data use to create new_branches 
        already_exist = db.query(Branch).filter(Branch.name == name,
                                                Branch.status == 1).first()

        if already_exist:
            return {"status" : 0, "message" : f"Branch name '{name}' is already exist"}
        
        if not phone_number_validation(phone_number):
            raise HTTPException(status_code=400, detail="Invalid phone number")
        
        already_exist_phone_number=db.query(Branch).filter(Branch.phone_number == phone_number,
                                                            Branch.status == 1).first()

        if already_exist_phone_number:
            return {"status" : 0 , "message" : f"Phone number '{phone_number}' is aleady exist"}
        
        if manager_id:
            chechManager = db.query(User).filter(User.id == manager_id,
                                                    User.user_type == 3,
                                                    User.status == 1).first()  
            if not chechManager:
                return {"message" : f"Invalied managaer ID : {manager_id}"}
        
        allLeadData.append({"name": name,
                            "phone_number" : phone_number,
                            "address" : address,
                            "manager_id" : manager_id,
                            "maximum_no_bike" : maximum_no_bike,
                            "maximum_no_car" : maximum_no_car,
                            })
    for row in allLeadData:
        branchData = Branch(name = row["name"],
                            phone_number = row["phone_number"],
                            address = row["address"],
                            manager_id = row["manager_id"],
                            maximum_no_bike = row["maximum_no_bike"],
                            maximum_no_car = row["maximum_no_car"],
                            updated_date = None,
                            created_at = datetime.now(),
                            status = 1)
        db.add(branchData)
        db.commit()
    return {"status" : 1, "message" : "Imported branches successfully created"}
