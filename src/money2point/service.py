import model
import os, re
import json
import random
import subprocess
from datetime import datetime
from typing import Dict, Any
from authentication import get_current_active_user_token
from fastapi import Request, HTTPException
from config import db
from dotenv import load_dotenv
from money2point import schema
from sqlmodel import Session, select
from config import PAYMENT_DIR

load_dotenv()

from_date = "2024-01-01"
page = 1
page_size = 20
sort = "DESC"
api_url = os.environ.get("API_URL")
api_key_or_token = os.environ.get("API_KEY_OR_TOKEN")

curl_command = [
        "curl",
        "--location",
        "--request",
        "GET",
        f"'{api_url}?fromDate={from_date}&page={page}&pageSize={page_size}&sort={sort}'",
        "--header",
        f"'Authorization: Apikey {api_key_or_token}'"
    ]
curl_command_str = " ".join(curl_command)


class General:   
    
    def format_time(data):
        my_datetime = datetime.fromisoformat(data)
        # Extracting date, month, and year
        day = my_datetime.day
        month = my_datetime.month
        year = my_datetime.year
        return f"{year}-{month}-{day}"

    def get_userjob_by_id(job_id: int, db_session: Session, current_user):
        job_query = select(model.JobDescription).where(
                                                    model.JobDescription.user_id == current_user.id,
                                                    model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result 
            
    def get_job_by_id(job_id: int, db_session: Session):
        job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
    
    def get_detail_resumeuser_by_id(cv_id: int, db_session: Session, current_user):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.user_id == current_user.id,
                   model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
            
    def get_detail_resume_by_id(cv_id: int, db_session: Session):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    

class MoneyPoint:

    @staticmethod
    def add_point_package(data: schema.PointPackage,
                          db_session: Session):
        package_db = model.PointPackage(
                                point=data.point,
                                price=data.price,
                                currency=data.currency
        )
        db_session.add(package_db)
        db.commit_rollback(db_session)


    @staticmethod
    def list_point_package(db_session: Session):
        package_db = db_session.execute(select(model.PointPackage)).scalars().all()
        return package_db

    @staticmethod
    def get_point_package(package_id: int,
                          db_session: Session):
        result = db_session.execute(select(model.PointPackage).where(model.PointPackage.id == package_id)).scalars().first()
        return result
                
    
    @staticmethod
    def purchase_point(request: Request, data_form: schema.PurchasePoint, db_session: Session, credentials):
        id_codes = db_session.execute(select(model.PaymentOTP.id_code)).all()
        while True:
            payment_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if payment_otp not in id_codes:
                payment_db = model.PaymentOTP(id_code=payment_otp)
                db_session.add(payment_db)
                db.commit_rollback(db_session)
                #   Save data as temporarily
                data = {
                    "id_code": payment_otp,
                    "auth_credentials": credentials.credentials,
                    "package_id": data_form.package_id,
                    "quantity": data_form.quantity,
                    "total_price": data_form.total_price,
                    "transaction_form": data_form.transaction_form
                }
                #   Get current user and save transaction information for that user
                _, customer = get_current_active_user_token(credentials.credentials, db_session)
                with open(os.path.join(PAYMENT_DIR, f'user_{customer.id}_transaction.json'), 'w') as file:
                    json.dump(data, file)
                return {
                    "id_code": payment_otp,
                    "bank_name": "Ngân hàng TMCP Tiên Phong - Chi nhánh TP Hồ Chí Minh.",
                    "transaction": "Phòng giao dịch Nguyễn Oanh.",
                    "account_owner": "CÔNG TY CP CỘNG ĐỒNG SHARECV VIỆT NAM.",
                    "account_number": "02061973979",
                    "qr_code": os.path.join(str(request.base_url), 'static/payment/sharecv_qr.png')
                }
                
    def get_current_time():
        current_time = datetime.now()
        # Extract year, month, and day
        year = current_time.year
        month = current_time.month
        day = current_time.day
        return f"{year}-{month}-{day}"
        
    #   Check to see if this consumer is the one who made the transaction   
    @staticmethod
    def check_customer(data: Dict[str, Any], id_code: str, total_price: float):
        for record in data["data"]["records"]:
            transaction_idcode = re.findall(r'\b\d+\b', record['description'])[0]
            transaction_time = General.format_time(record['when'])
            transaction_amount = float(abs(record['amount']))
            if transaction_idcode == id_code and  \
                transaction_time == MoneyPoint.get_current_time() and     \
                transaction_amount == float(total_price):
                return True
        

    @staticmethod
    def make_transaction(db_session: Session):
        result = subprocess.run(
                        curl_command_str,
                        shell=True,
                        capture_output=True,
                        text=True
        )     
        print("==============================================")
        print(curl_command_str)
        print("==============================================")
        #   Get current user: customer and update data
        _, customer = get_current_active_user_token(data['auth_credentials'], db_session)
        #   Read saved transaction data
        with open(os.path.join(PAYMENT_DIR, f'user_{customer.id}_transaction.json'), 'r') as file:
            data = json.load(file)
        #   Check wheather transaction exists
        if not MoneyPoint.check_customer(json.loads(result.stdout), data['id_code'], data['total_price']):
            raise HTTPException(status_code=404, detail="Transaction doesn't exist!")
        point_package = db_session.execute(select(model.PointPackage).where(model.PointPackage.id == data['package_id'])).scalars().first()
        customer.point += data['quantity'] * point_package.point
        #   Add to purchase history
        purchase_db = model.TransactionHistory(
                                        user_id=customer.id,
                                        point=point_package.point,
                                        price=point_package.price,
                                        quantity=data['quantity'],
                                        total_price=data['total_price'],
                                        transaction_form=data['transaction_form']
        ) 
        db_session.add(purchase_db)
        db.commit_rollback(db_session)
        #   Save transaction information
        with open(os.path.join(PAYMENT_DIR, 'transaction_info.json'), 'w') as file:
            json.dump(json.loads(result.stdout), file)
        #   Remove saved transaction data
        os.remove(os.path.join(PAYMENT_DIR, 'package_info.json'))
            

    @staticmethod
    def list_history_purchase(db_session: Session, current_user):
        query = select(model.TransactionHistory).where(model.TransactionHistory.user_id == current_user.id)
        results = db_session.execute(query).scalars().all()
        return [{
            "id": result.id,
            "point": result.point,
            "price": result.price,
            "quantity": result.quantity,
            "total_price": result.total_price,
            "transaction_form": result.transaction_form,
            "transaction_date": result.created_at,
        } for result in results]