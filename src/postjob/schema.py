from datetime import datetime
from typing import List, Optional
from enum import Enum
from fastapi import File, Form, UploadFile, Body, Query
from pydantic import BaseModel, EmailStr


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