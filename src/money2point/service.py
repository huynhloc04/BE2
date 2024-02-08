import model
import os, re
import json
import random
from datetime import datetime
from typing import Dict, Any, List
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
    def purchase_point(request: Request, data_form: schema.PurchasePoint, db_session: Session, current_user):
        id_codes = db_session.execute(select(model.TransactionHistory.transaction_otp)).all()
        while True:
            payment_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if payment_otp not in id_codes:
                transaction_db = model.TransactionHistory(user_id=current_user.id, transaction_otp=payment_otp)
                db_session.add(transaction_db)
                db.commit_rollback(db_session)
                #   Save data as temporarily
                data = {
                    "id_code": payment_otp,
                    "package_id": data_form.package_id,
                    "quantity": data_form.quantity,
                    "total_price": data_form.total_price,
                    "transaction_form": data_form.transaction_form
                }
                #   Get current user and save transaction information for that user
                with open(os.path.join(PAYMENT_DIR, f'{payment_otp}.json'), 'w') as file:
                    json.dump(data, file)
                return {
                    "id_code": payment_otp,
                    "bank_name": "Ngân hàng TMCP Tiên Phong - Chi nhánh TP Hồ Chí Minh.",
                    "transaction": "Phòng giao dịch Nguyễn Oanh.",
                    "account_owner": "CÔNG TY CP CỘNG ĐỒNG SHARECV VIỆT NAM.",
                    "account_number": "02061973979",
                    "qr_code": os.path.join(str(request.base_url), 'static/payment/sharecv_qr.png')
                }
        

    @staticmethod
    def recruiter_make_transaction(transaction: List[Dict[str, Any]], db_session: Session):
        #   Get OTP from transaction form
        otp = re.findall(r'\b\d+\b', transaction[0]['description'])[0]
        #   Get transaction from DB
        transaction = db_session.execute(select(model.TransactionHistory).where(model.TransactionHistory.transaction_otp == otp)).scalars().first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction doesn't exist!")
        #   Read saved transaction data
        with open(os.path.join(PAYMENT_DIR, f'{otp}.json'), 'r') as file:
            data = json.load(file)
        point_package = db_session.execute(select(model.PointPackage).where(model.PointPackage.id == data['package_id'])).scalars().first()
        #   Get user from user_id => Update point
        user = db_session.execute(select(model.User).where(model.User.id == transaction.user_id)).scalars().first()
        user.point += data['quantity'] * point_package.point
        #   Add to purchase history
        transaction.point=point_package.point,
        transaction.price=point_package.price,
        transaction.quantity=data['quantity'],
        transaction.total_price=data['total_price'],
        transaction.transaction_form=data['transaction_form']
        db.commit_rollback(db_session)
        #   Remove saved transaction data
        os.remove(os.path.join(PAYMENT_DIR, f'{otp}.json'))
        

    @staticmethod
    def recruiter_make_transaction(transaction: List[Dict[str, Any]], db_session: Session):
        #   Get OTP from transaction form
        otp = re.findall(r'\b\d+\b', transaction[0]['description'])[0]
        #   Get transaction from DB
        transaction = db_session.execute(select(model.TransactionHistory).where(model.TransactionHistory.transaction_otp == otp)).scalars().first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction doesn't exist!")
        #   Read saved transaction data
        with open(os.path.join(PAYMENT_DIR, f'{otp}.json'), 'r') as file:
            data = json.load(file)
        point_package = db_session.execute(select(model.PointPackage).where(model.PointPackage.id == data['package_id'])).scalars().first()
        #   Get user from user_id => Update point
        user = db_session.execute(select(model.User).where(model.User.id == transaction.user_id)).scalars().first()
        user.point += data['quantity'] * point_package.point
        #   Add to purchase history
        transaction.point=point_package.point,
        transaction.price=point_package.price,
        transaction.quantity=data['quantity'],
        transaction.total_price=data['total_price'],
        transaction.transaction_form=data['transaction_form']
        db.commit_rollback(db_session)
        #   Remove saved transaction data
        os.remove(os.path.join(PAYMENT_DIR, f'{otp}.json'))