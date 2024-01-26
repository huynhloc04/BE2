from datetime import datetime
from typing import List, Any, Optional
from enum import Enum
from fastapi import File, Form, UploadFile, Body
from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    admin = 'admin'
    super_admin = 'super_admin'
    recruiter = 'recruiter'
    collaborator = 'collaborator'

    def __str__(self):
        return f"{self.value}"


class LoginForm(BaseModel):
    role: Role = 'admin'
    access_token: str
    refresh_token: Optional[str]
    token_type: Optional[str] = 'Bearer'
    token_key: Optional[str] = 'Authorization'

    def __str__(self):
        return f"{self.value}"
    

class SignUpResponse(BaseModel):
    user_id: int
    email: EmailStr
    fullname: Optional[str] = None
    role: Optional[Role] = None


class UserInfo(BaseModel):
    fullname: str
    email: EmailStr
    phone: str


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
    
    
class VerifyOTP(BaseModel):
    received_otp: str 
    user_id: int 
        
        
class ChangePassword(BaseModel):
    old_password: str 
    new_password: str
    
class ForgotPassword(BaseModel):
    old_password: str
    new_password: str
        
        
class UserInfo(BaseModel):
    fullname: Optional[str] 
    email: Optional[str]
    phone: Optional[str]
        
        
class MemberBase(BaseModel):
    fullname: str 
    email: str
    password: str


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None