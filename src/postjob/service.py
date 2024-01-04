import model
from fastapi import HTTPException, Request
from sqlalchemy import select
import smtplib
import ssl
from config import db
from passlib.context import CryptContext
from email.message import EmailMessage
from postjob import schema
from datetime import timedelta, datetime
from pydantic import BaseModel, EmailStr
from sqlmodel import Session
from postjob import schema


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
    def check_token(db_session: Session, token: str):
        token = (db_session.execute(select(model.JWTModel).where(model.JWTModel.token == token))).scalar_one_or_none()
        if token:
            return True
        return False



def add_company(request: Request,
                db_session: Session,
                data: schema.CompanyBase,
                current_user):
    db_company = model.Company(
                            user_id=current_user.id,
                            name=data.company_name, 
                            industry=data.industry, 
                            description=data.description, 
                            tax_code=data.tax_code, 
                            phone=data.phone, 
                            email=data.email, 
                            founded_year=data.founded_year, 
                            company_size=data.company_size, 
                            address=data.address, 
                            city=data.city, 
                            country=data.country, 
                            logo=str(request.base_url) + data.logo.filename if data.logo else None,
                            cover_image=str(request.base_url) + data.cover_image.filename if data.cover_image else None, 
                            # company_images=[str(request.base_url) + company_img.filename for company_img in data.company_images] if data.company_images else None,
                            company_video=str(request.base_url) + data.company_video.filename if data.company_video else None,
                            linkedin=data.linkedin,
                            website=data.website,
                            facebook=data.facebook,
                            instagram=data.instagram)
    db_session.add(db_company)
    db.commit_rollback(db_session)
    return db_company