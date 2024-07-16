from fastapi import APIRouter, Form
from utils import db_dependency
from datetime import datetime,date,timedelta
from models import * 
import xlsxwriter
from fpdf import FPDF
from sqlalchemy import func,or_,desc,case

router = APIRouter()

@router.post("/IncomeDetails")
async def income_report(db : db_dependency, token : str,
                        fromdate : date = Form(...,description="2023-1-1"), 
                        todate : date = Form(...,description="2023-12-30"),
                        export_type : int = Form(...,description="1:'xl format', 2:'pdf format' ")):

    check_token=db.query(ApiTokens).filter(ApiTokens.token==token).first()
    if not check_token:
        
        return {"message":"Token ID is not Activate"} 
    
    if check_token.status==1:

            db_user = db.query(User).filter(User.id==check_token.user_id,
                                        User.status==1,
                                         or_(User.user_type==1, User.user_type==2)).first()
            
            if not db_user:
                return {"status" : 0, "message" : "Accessed only by 'Super_Admin' or 'Admin' "}
            
    else:
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if check_token.expires_at < datetime.now():
        check_token.status = -1
        db.commit()
        return ({"status" :0, "message" : "Your session has expired. Please, Sign-in again"})

    if export_type == 1:

        # export file path
        workbook = xlsxwriter.Workbook("/home/ramya/Desktop/BranchIncome.xlsx")

        worksheet = workbook.add_worksheet()

        bold = workbook.add_format({"bold":1})
        dAte = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        cost_format = workbook.add_format({'num_format': '0.00'})

        headings = ['S.no ',
                    'Branch_ID',
                    "Branch Name",
                    "UserCount",
                    "Total amount",
                    "From date",
                    "To date"]
        
        # all_data = []
        
        one_day=timedelta(days=1)
        f_date=fromdate
        t_date=todate+one_day

        GetBranch= db.query(Parkingslotbooking.branch_id,Branch.name,
                            func.sum(Parkingslotbooking.fees).label("cost"),
                            func.count(Parkingslotbooking.id).label("usercount"),
                            ).join(Branch,Parkingslotbooking.branch_id == Branch.id
                                   ).filter(Parkingslotbooking.booking_time.between(f_date, t_date),
                                            Parkingslotbooking.status == -1,
                                            ).group_by(Parkingslotbooking.branch_id
                                                       ).order_by(desc("cost")).all()
        
        row = 0
        column = 0
        serial_number = 1

        worksheet.write_row("A1",headings,bold)
        row +=1

        for b_id, b_name, cost, usercount in GetBranch:
            worksheet.write(row,column,serial_number) 
            worksheet.write(row,column+1,b_id)
            worksheet.write(row,column+2,b_name)
            worksheet.write(row,column+3,usercount)
            worksheet.write(row,column+4,cost,cost_format)
            worksheet.write(row,column+5,fromdate,dAte)
            worksheet.write(row,column+6,todate,dAte)

            row += 1
            serial_number += 1

        workbook.close()
        return {"message" : "xlsx file is created"}
    
    elif export_type == 2:
        
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial","B",18)
                self.cell(0,15,"Branch-wise income",align = "C",border = 0)
                self.set_xy(0,30)

        pdf = PDF("portrait","mm","A4")
        pdf.set_font("Helvetica","B",10)

        pdf.add_page()

        # rectangle
        pdf.set_xy(5,5)
        pdf.rect(25,30,150,10)

        # heading column line
        pdf.line(50,30,50,40)
        pdf.line(75,30,75,40)
        pdf.line(100,30,100,40)
        pdf.line(125,30,125,40)
        pdf.line(150,30,150,40)
        pdf.line(175,30,175,40)


        headings = ['Branch_ID',
                    "Branch Name",
                    "Total amount",
                    "UserCount",
                    "From date",
                    "To date"]

        pdf.set_xy(25,32)

        for head_data in headings:
            pdf.cell(25,7,txt = head_data, align = "C",border=0)

        one_day=timedelta(days=1)
        f_date=fromdate
        # f_date=fromdate+one_day
        t_date=todate+one_day
        # GetBranch =[[2,3,4,5,6,7],['A',"C","D","E","F","G"],
        #             ["a",23,45,65,45,78]]
        GetBranch= db.query(Parkingslotbooking.branch_id,Branch.name,
                            func.sum(Parkingslotbooking.fees).label("cost"),
                            func.count(Parkingslotbooking.id).label("usercount"),
                            ).join(Branch,Parkingslotbooking.branch_id == Branch.id
                                   ).filter(Parkingslotbooking.booking_time.between(f_date, t_date),
                                            Parkingslotbooking.status == -1,
                                            ).group_by(Parkingslotbooking.branch_id
                                                       ).order_by(desc("cost")).all()

        a=25
        b=40
        pdf.set_xy(a,b)
        pdf.set_font("Arial",size=10)
        # pdf.cell(30,7,"5",1 )
        x=25
        y=10
        # serival_num = 1

        for row in GetBranch:
            for row_data in row:
                # row_data[0] = str(serival_num)
                pdf.cell(x,y,txt = str(row_data),align = "C",border = 1,ln=0)
            pdf.cell(x,y,txt = str(fromdate),align= "C",border=1,ln=0)
            pdf.cell(x,y,txt = str(todate),align="C",border=1)
            # serival_num += 1
            b += 10
            pdf.set_xy(a,b)

        pdf.output("/home/ramya/Desktop/demopark.pdf")
        return {"status" : 1, "message":"PDF file create"}
    else:
        return {"status": 0,"message":"Invalied export type"}