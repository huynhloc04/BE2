
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, EmailStr


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
    

class GenderChoice(str, Enum):
    male = "male"
    female = "female"
    both = "both"
    
    
class JobStatus(str, Enum):
	pending = "pending"
	browsing = "browsing"
	recruiting = "recruiting"
	paused = "paused"

class Level(str, Enum):     
	executive_senior_engineer_developer = "executive_senior_engineer_developer"
	leader_supervisor_seniorleader_seniorsupervisor_assistmanager = "leader_supervisor_seniorleader_seniorsupervisor_assistmanager"
	manager_seniormanager_assistantdirector = "manager_seniormanager_assistantdirector"
	vicedirector_deputydirector = "vicedirector_deputydirector"
	director = "director"
	head = "head"
	group = "group"
	coo_ceo_cfo_cpo = "coo_ceo_cfo_cpo"
	generalmanager_generaldirector = "generalmanager_generaldirector"
    

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
        
class JobEducation(BaseModel):
    degree: Union[str, None]
    major: Union[str, None]
    gpa: Union[str, None]
    
class LanguageCertificate(BaseModel):
    language: Union[str, None]
    language_certificate_name: Union[str, None]
    language_certificate_level: Union[str, None]
    
class OtherCertificate(BaseModel):
    certificate_name: Union[str, None]
    certificate_level: Union[str, None]

class JobUpdate(BaseModel):
    job_id: int
    job_title: Union[str, None]
    industries: Union[List[str], None]
    gender: Union[GenderChoice, None]
    job_type: Union[str, None]
    skills: Union[List[str], None]
    #   Education
    education: Union[List[JobEducation], None]
    #   LanguageCertificate    
    language_certificates: Union[List[LanguageCertificate], None]
    #   OtherCertificates
    other_certificates: Union[List[OtherCertificate], None]
    #   Location
    address: Union[str, None]
    city: Union[str, None]
    country: Union[str, None]
    received_job_time: Union[datetime, None]
    working_time: Union[str, None]
    description: Union[str, None]
    requirement: Union[str, None]
    benefits: Union[List[str], None]
    levels: Union[List[str], None]
    roles: Union[List[str], None]
    yoe: Union[int, None]
    num_recruit: Union[int, None]
    min_salary: Union[float, None]
    max_salary: Union[float, None]
    currency: Union[str, None]
    #   Chỉ xuất hiện bên trang Admin, và lúc NTD xem lại JD đã up (Admin check và gửi lại cho NTD)
    admin_decline_reason: Optional[str]


class AddCandidate(BaseModel):
    job_id: int
    level: Level
    cv_pdf: UploadFile

    @classmethod
    def as_form(cls,
                job_id: int = Form(...),
                level: Level = Form(...),
                cv_pdf: UploadFile = File(...)):
        
        return cls(
            job_id=job_id,
            level=level,
            cv_pdf=cv_pdf)
    

    
# ===========================================================
#                           Resumes
# ===========================================================

class ResumeEducation(BaseModel):
    degree: Union[str, None]
    institute_name: Union[str, None]
    major: Union[str, None]
    gpa: Union[str, None]
    start_time: Union[str, None]
    end_time: Union[str, None]

class ResumeExperience(BaseModel):
    company_name: Union[str, None]
    job_tile: Union[str, None]
    working_industry: Union[str, None]
    levels: Union[str, None]
    roles: Union[str, None]
    start_time: Union[str, None]
    end_time: Union[str, None]

class ResumeAward(BaseModel):
    name: Union[str, None]
    time: Union[str, None]
    description: Union[str, None]

class ResumeProject(BaseModel):
    project_name: Union[str, None]
    description: Union[str, None]
    start_time: Union[datetime, None]
    end_time: Union[datetime, None]
    
class ResumeLanguageCertificate(BaseModel):
    language: Union[str, None]
    language_certificate_name: Union[str, None]
    language_certificate_level: Union[str, None]
    
class OtherResumeCertificate(BaseModel):
    certificate_name: Union[str, None]
    certificate_level: Union[str, None]

class ResumeUpdate(BaseModel):
    cv_id: int
    name: Union[str, None]
    current_job: Union[str, None]
    gender: Union[str, None]
    birthday: Union[str, None]  # => age
    linkedin: Union[str, None]
    website: Union[str, None]
    facebook: Union[str, None]
    instagram: Union[str, None]        
    phone: Union[str, None]
    email: Union[str, None]
    address: Union[str, None]
    city: Union[str, None]
    country: Union[str, None]        
    objectives: Union[str, None]
    educations: Union[List[ResumeEducation], None]
    work_experiences: Union[List[ResumeExperience], None]
    skills: Union[List[str], None]
    awards: Union[List[ResumeAward], None]
    projects: Union[List[ResumeProject], None]
    #   LanguageCertificate    
    language_certificates: Union[List[ResumeLanguageCertificate], None]
    #   OtherCertificates
    other_certificates: Union[List[OtherResumeCertificate], None]