
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile, Query
from pydantic import BaseModel

    
class Industry(str, Enum):
    education = "Education", 
    construction = "Construction", 
    design = "Design", 
    corporate_services = "Corporate Services", 
    retail = "Retail", 
    energy_mining = "Energy & Mining", 
    manufacturing = "Manufacturing", 
    finance = "Finance", 
    recreation_travel = "Recreation & Travel", 
    arts = "Arts", 
    health_care = "Health Care", 
    hardware_networking = "Hardware & Networking", 
    software_itservices = "Software & IT Services", 
    real_estate = "Real Estate", 
    legal = "Legal", 
    agriculture = "Agriculture", 
    media_communications = "Media & Communications", 
    transportation_logistics = "Transportation & Logistics", 
    entertainment = "Entertainment", 
    wellness_fitness = "Wellness & Fitness", 
    public_safety = "Public Safety", 
    public_administration = "Public Administration"

    def __str__(self):
        return f"{self.value}"


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None


class CompanyInfo(BaseModel):
    company_name: str
    logo: str
    description: str
    industry: Industry
    phone: str
    email: str
    founded_year: int
    company_size: str
    tax_code: str
    address: str
    city: str
    country: str
    company_video: Optional[str]
    company_images: Optional[List[str]]
    cover_image: Optional[str]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]


class CompanyBase(BaseModel):
    company_name: str
    industry: Industry
    description: str
    phone: str
    email: str
    founded_year: int
    company_size: str
    tax_code: str
    address: str
    city: str
    country: str
    logo: UploadFile
    cover_image: Optional[UploadFile]
    company_video: Optional[UploadFile]
    logo: Optional[UploadFile]
    company_images: Optional[List[UploadFile]]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]

    @classmethod
    def as_form(cls, 
                company_name: str = Form(...),
                industry: Industry = Form(...),
                description: str = Form(...),
                phone: str = Form(...),
                email: str = Form(...),
                founded_year: int = Form(...),
                company_size: str = Form(...),
                tax_code: str = Form(...),
                address: str = Form(...),
                city: str = Form(...),
                country: str = Form(...),
                logo: UploadFile = File(...),
                cover_image: Optional[UploadFile] = None,
                company_video: Optional[UploadFile] = None,
                company_images: Optional[List[UploadFile]] = None,
                linkedin: Optional[str] = Form(None),
                website: Optional[str] = Form(None),
                facebook: Optional[str] = Form(None),
                instagram: Optional[str] = Form(None)):
        
        return cls(
            company_name=company_name,
            industry=industry,
            description=description,
            phone=phone,
            email=email,
            founded_year=founded_year,
            company_size=company_size,
            tax_code=tax_code,
            address=address,
            city=city,
            country=country,
            logo=logo,
            cover_image=cover_image,
            company_video=company_video,
            company_images=company_images,
            linkedin=linkedin,
            website=website,
            facebook=facebook,
            instagram=instagram
        )


class CompanyUpdate(BaseModel):
    company_name: Optional[str]
    industry: Optional[Industry]
    description: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    founded_year: Optional[int]
    company_size: Optional[str]
    tax_code: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    logo: Optional[UploadFile]
    cover_image: Optional[UploadFile]
    company_video: Optional[UploadFile]
    logo: Optional[UploadFile]
    company_images: Optional[List[UploadFile]]
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]

    @classmethod
    def as_form(cls, 
                company_name: Optional[str] = None,
                industry: Optional[Industry] = None,
                description: Optional[str] = None,
                phone: Optional[str] = None,
                email: Optional[str] = None,
                founded_year: Optional[int] = None,
                company_size: Optional[str] = None,
                tax_code: Optional[str] = None,
                address: Optional[str] = None,
                city: Optional[str] = None,
                country: Optional[str] = None,
                logo: Optional[UploadFile] = None,
                cover_image: Optional[UploadFile] = None,
                company_video: Optional[UploadFile] = None,
                company_images: Optional[List[UploadFile]] = None,
                linkedin: Optional[str] = None,
                website: Optional[str] = None,
                facebook: Optional[str] = None,
                instagram: Optional[str] = None):
        
        return cls(
            company_name=company_name,
            industry=industry,
            description=description,
            phone=phone,
            email=email,
            founded_year=founded_year,
            company_size=company_size,
            tax_code=tax_code,
            address=address,
            city=city,
            country=country,
            logo=logo,
            cover_image=cover_image,
            company_video=company_video,
            company_images=company_images,
            linkedin=linkedin,
            website=website,
            facebook=facebook,
            instagram=instagram
        )

class BankBase(BaseModel):
    user_id: int
    bank_name: str
    branch_name: Optional[str]
    account_owner: str
    account_number: str