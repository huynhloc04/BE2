from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import File, Form, UploadFile, Body
from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    admin = 'admin'
    super_admin = 'super_admin'
    recruiter = 'recruiter'
    collaborator = 'collaborator'

class SignUpResponse(BaseModel):
    user_id: int
    email: EmailStr
    fullname: Optional[str] = None
    role: Optional[Role] = None


class UserInfo(BaseModel):
    fullname: str
    email: EmailStr
    phone: str


class LoginForm(BaseModel):
    role: Role = 'admin'
    access_token: str
    refresh_token: Optional[str]
    token_type: Optional[str] = 'Bearer'
    token_key: Optional[str] = 'Authorization'


class AdminMember(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    role: Role = "admin"
    

class SignUp(BaseModel):
    fullname: str
    email: EmailStr
    phone: str
    password: str
    password_again: str
    role: Role

    @classmethod
    def as_form(cls, 
                fullname: str = Form(...),
                email: EmailStr = Body(...),
                phone: str = Form(...),
                password: str = Form(...),
                password_again: str = Form(...),
                role: Role = Form(...)):
        
        return cls(
                fullname=fullname,
                email=email,
                phone=phone,
                password=password,
                password_again=password_again,
                role=role)
    
    
class VerifyOTP(BaseModel):
    received_otp: str 
    user_id: int 

    @classmethod
    def as_form(cls, 
                received_otp: str = Form(...),
                user_id: int = Form(...)):
        
        return cls(
                received_otp=received_otp,
                user_id=user_id,
                )
        
        
class ChangePassword(BaseModel):
    old_password: str 
    new_password: str

    @classmethod
    def as_form(cls, 
                old_password: str = Form(...),
                new_password: str = Form(...)):
        
        return cls(
                old_password=old_password,
                new_password=new_password,
                )
        
        
class UserInfo(BaseModel):
    fullname: Optional[str] 
    email: Optional[str]
    phone: Optional[str]

    @classmethod
    def as_form(cls, 
                fullname: Optional[str] = Form(None),
                email: Optional[str] = Form(None),
                phone: Optional[str] = Form(None)):
        
        return cls(
            fullname=fullname,
            email=email,
            phone=phone)
        
        
class MemberBase(BaseModel):
    fullname: str 
    email: str
    password: str

    @classmethod
    def as_form(cls, 
                fullname: str = Form(...),
                email: str = Form(...),
                password: str = Form(...)):
        
        return cls(
            fullname=fullname,
            email=email,
            password=password)