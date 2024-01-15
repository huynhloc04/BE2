import model
from fastapi import HTTPException
from sqlalchemy import select
import smtplib
import ssl
from config import db
from passlib.context import CryptContext
from email.message import EmailMessage
from auth import schema, security
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
from sqlmodel import Session


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRequestRepository:
    @staticmethod
    def get_user_by_email(db_session: Session, email: str):
        query = select(model.User).where(model.User.email == email)
        result = db_session.execute(query).scalars().first()
        return result

    @staticmethod
    def get_user_by_id(db_session: Session, user_id: int):
        query = select(model.User).where(model.User.id == user_id)
        result = db_session.execute(query).scalars().first()
        return result
    
    @staticmethod
    def add_user(db_session: Session, **kwargs):
        #   Add user information
        user_db = model.User(**kwargs)
        db_session.add(user_db)
        db.commit_rollback(db_session)
        return user_db    

    @staticmethod
    def OTP_GOOGLE(otp: str, input_email="example@gmail.com"):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "hiep200326@gmail.com"
        receiver_email = input_email
        password = "aghs ypya luzd seut"
        
        em=EmailMessage()
        em['From']=sender_email
        em['To']=input_email
        em['subject']="AUTHORIZED REGISTER"
        body="HERE IS YOUR OTP CODE "+ otp
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, em.as_string())

        print("Sent!")
        json_otp={"otp": otp}
        return json_otp
    
    @staticmethod
    def authenticate_user(
                    db_session: Session,
                    email: str, 
                    password: str):
        user = AuthRequestRepository.get_user_by_email(db_session, email)
        if not user:
            return False
        if not security.verify_password(password, user.password):
            return False
        return user
    
    @staticmethod
    def update_password(db_session: Session,
                        current_user, 
                        hashed_password):
        result = AuthRequestRepository.get_user_by_id(db_session, current_user.id)
        result.password = hashed_password,
        result.updated_at = datetime.now()
        db.commit_rollback(db_session)
        
        
    @staticmethod
    def add_admin(
                db_session: Session,
                data: schema.MemberBase):
        db_member = model.User(
                            fullname=data.fullname,
                            email=data.email,
                            password=data.password,
                            role='admin')
        db_session.add(db_member)
        db.commit_rollback(db_session)
        return db_member
        
    @staticmethod
    def list_admin(db_session: Session):
        query = select(model.User).where(model.User.role == "admin")
        results = db_session.execute(query).scalars().all()
        return results

    @staticmethod
    def remove_member(db_session: Session, member_id: int):    
        query = select(model.User).where(model.User.id == member_id)
        result = db_session.execute(query).scalars().first()
        if result:
            #   Delete tag
            db_session.delete(result)
            db.commit_rollback(db_session)
        return result
    
    

class OTPRepo:
    @staticmethod
    def check_otp(
            db_session: Session,
            user_id: int, 
            otp: str):
        query = select(model.User).where(
                                    model.User.id==user_id,
                                    model.User.otp_token == otp)
        result = db_session.execute(query).scalars().first()
        if result:
            return True
        return False
    
    @staticmethod
    def disable_otp(db_session: Session, data_form):
        result = AuthRequestRepository.get_user_by_id(db_session, data_form.user_id)
        result.otp_token = None
        db.commit_rollback(db_session)
        
    @staticmethod
    def check_token(db_session: Session, token: str):
        token = (db_session.execute(select(model.JWTModel).where(model.JWTModel.token == token))).scalar_one_or_none()
        if token:
            return True
        return False
    
    @staticmethod
    def add_to_blacklist(db_session: Session, token: str):
        result = model.JWTModel(token=token, created_at=datetime.now())
        db_session.add(result)
        db.commit_rollback(db_session)
        return {"detail": "Thêm vào Blacklist.",
                "data": result,
                "metadata": None, 
                "status_code": 201}
