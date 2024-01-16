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


class SignUp(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    password_again: str
    role: Role

    @classmethod
    def as_form(cls, 
                name: str = Form(...),
                email: EmailStr = Body(...),
                phone: str = Form(...),
                password: str = Form(...),
                password_again: str = Form(...),
                role: Role = Form(...)):
        
        return cls(
                name=name,
                email=email,
                phone=phone,
                password=password,
                password_again=password_again,
                role=role)