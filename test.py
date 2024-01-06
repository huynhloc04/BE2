from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from fastapi import File, Form, UploadFile, Union
from pydantic import BaseModel, EmailStr


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
    

class SexChoice(str, Enum):
    male = "male"
    female = "female"
    both = "both"
    

class CompanyInfo(BaseModel):
    company_name: str
    logo: str
    description: str
    # company_images: Optional[List[UploadFile]]
    industry: str
    phone: str
    email: str
    founded_year: int
    company_size: int
    tax_code: str
    address: str
    city: str
    country: str
    company_video: Optional[str]
    cover_image: Optional[str]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]

class CompanyBase(BaseModel):
    company_name: str
    industry: str
    description: str
    phone: str
    email: str
    founded_year: int
    company_size: int
    tax_code: str
    address: str
    city: str
    country: str
    logo: UploadFile
    cover_image: Optional[UploadFile]
    # company_images: Optional[List[UploadFile]]
    company_video: Optional[UploadFile]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]

    @classmethod
    def as_form(cls, 
                company_name: str = Form(...),
                industry: str = Form(...),
                description: str = Form(...),
                tax_code: str = Form(...),
                phone: str = Form(...),
                email: str = Form(...),
                founded_year: int = Form(...),
                company_size: int = Form(...),
                address: str = Form(...),
                city: str = Form(...),
                country: str = Form(...),
                logo: UploadFile = File(..., max_lenght=10485760),
                cover_image: Optional[UploadFile] = File(None, max_lenght=10485760),
                # company_images: Optional[List[UploadFile]] = File(None, max_lenght=10485760),
                company_video: Optional[UploadFile] = File(None, max_lenght=10485760),
                linkedin: Optional[str] = Form(None),
                website: Optional[str] = Form(None),
                facebook: Optional[str] = Form(None),
                instagram: Optional[str] = Form(None)):
        
        return cls(
            company_name=company_name,
            industry=industry,
            description=description,
            tax_code=tax_code,
            phone=phone,
            email=email,
            founded_year=founded_year,
            company_size=company_size,
            address=address,
            city=city,
            country=country,
            logo=logo,
            cover_image=cover_image,
            # company_images=company_images,
            company_video=company_video,
            linkedin=linkedin,
            website=website,
            facebook=facebook,
            instagram=instagram)
    


class CompanyUpdate(BaseModel):
    company_name: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    tax_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    founded_year: Optional[int]
    company_size: Optional[int]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    logo: Optional[UploadFile]
    cover_image: Optional[UploadFile]
    # company_images: Optional[List[UploadFile]]
    company_video: Optional[UploadFile]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]

    @classmethod
    def as_form(cls,
                company_name: Optional[str] = Form(None),
                industry: Optional[str] = Form(None),
                description: Optional[str] = Form(None),
                tax_code: Optional[str] = Form(None),
                phone: Optional[str] = Form(None),
                email: Optional[str] = Form(None),
                founded_year: Optional[int] = Form(None),
                company_size: Optional[int] = Form(None),
                address: Optional[str] = Form(None),
                city: Optional[str] = Form(None),
                country: Optional[str] = Form(None),
                logo: Optional[UploadFile] = File(None, max_lenght=10485760),
                cover_image: Optional[UploadFile] = File(None, max_lenght=10485760),
                # company_images: Optional[List[UploadFile]] = File(None, max_lenght=10485760),
                company_video: Optional[UploadFile] = File(None, max_lenght=10485760),
                linkedin: Optional[str] = Form(None),
                website: Optional[str] = Form(None),
                facebook: Optional[str] = Form(None),
                instagram: Optional[str] = Form(None)):
        
        return cls(
            company_name=company_name,
            industry=industry,
            description=description,
            tax_code=tax_code,
            phone=phone,
            email=email,
            founded_year=founded_year,
            company_size=company_size,
            address=address,
            city=city,
            country=country,
            logo=logo,
            cover_image=cover_image,
            # company_images=company_images,
            company_video=company_video,
            linkedin=linkedin,
            website=website,
            facebook=facebook,
            instagram=instagram)