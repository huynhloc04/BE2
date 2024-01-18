
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
    
    
class CollaborateJobStatus(str, Enum):
    referred = "referred"
    favorite = "favorite"
    unreferred = "unreferred"

    def __str__(self):
        return f"{self.value}"
    
    
class InterviewEnum(str, Enum):
    directly = "Phỏng vân trực tiếp"
    phone = "Phỏng vân điện thoại"
    other = "Hình thức khác"

    def __str__(self):
        return f"{self.value}"
    

class CandidateMailReply(str, Enum):
    accept = "accept"
    decline = "decline"    

    def __str__(self):
        return f"{self.value}"
    
    
class Language(str, Enum):
    english = "English"
    japan = "Japan"
    korean = "Korean"
    chinese = "Chinese"  

    def __str__(self):
        return f"{self.value}"
    

class Level(str, Enum):     
    Executive = "Executive"
    Senior = "Senior"
    Engineer = "Engineer"
    Developer = "Developer"
    Leader = "Leader"
    Supervisor = "Supervisor"
    Senior_Leader = "Senior Leader"
    Senior_Supervisor = "Senior Supervisor"
    Assitant_Manager = "Assitant Manager"
    Manager = "Manager"
    Senior_Manager = "Senior Manager"
    Assitant_Director = "Assitant Director"
    Vice_Direcctor = "Vice Direcctor"
    Deputy_Direcctor = "Deputy Direcctor"
    Director = "Director"
    Head = "Head"
    Group = "Group"
    COO = "Chief Operating Officer"
    CEO = "Chief Executive Officer"
    CPO = "Chief Product Officer"
    CFO = "Chief Financial Officer"
    General_Manager = "General Manager"
    General_Director = "General Director"

    def __str__(self):
        return f"{self.value}"
    
class ValuationDegree(str, Enum):
    bachelor = "Bachelor"
    master = "Master"
    ph_d = "Ph.D"  

    def __str__(self):
        return f"{self.value}"
    

class GenderChoice(str, Enum):
    male = "male"
    female = "female"
    both = "both"

    def __str__(self):
        return f"{self.value}"
    

class ResumeStatus(str, Enum):
    pricing_approved = "pricing_approved"
    pricing_rejected = "pricing_rejected"
    ai_matching_approved = "ai_matching_approved"
    ai_matching_rejected = "ai_matching_rejected"
    waiting_candidate_accept = "waiting_candidate_accept"
    candidate_accepted = "candidate_accepted"
    candidate_declined = "candidate_declined"
    admin_matching_approved = "admin_matching_approved"
    admin_matching_rejected = "admin_matching_rejected"
    waiting_accept_interview = "waiting_accept_interview"
    candidate_accepted_interview = "candidate_accepted_interview"
    candidate_rejected_interview = "candidate_rejected_interview"

    def __str__(self):
        return f"{self.value}"
    

class AdminReviewMatching(str, Enum):
    admin_matching_approved = "admin_matching_approved"
    admin_matching_rejected = "admin_matching_rejected"

    def __str__(self):
        return f"{self.value}"
    
    
class ResumePackage(str, Enum):
    basic = "basic"
    platinum = "platinum"

    def __str__(self):
        return f"{self.value}"
    
    
class CandidateState(str, Enum):
    all = "TẤT CẢ"
    new_candidate = "ỨNG VIÊN MỚI"
    choosen_candidate = "ỨNG VIÊN ĐÃ CHỌN"
    inappro_candidate = "ỨNG VIÊN CHƯA PHÙ HỢP"

    def __str__(self):
        return f"{self.value}"
    
    
class JobStatus(str, Enum):
    pending = "pending"
    browsing = "browsing"
    recruiting = "recruiting"
    paused = "paused"

    def __str__(self):
        return f"{self.value}"
    

class InterviewForm(BaseModel):
    cv_id: int
    interview_form: InterviewEnum
    
class DirectlyInterviewMail(BaseModel):
    time: datetime
    location: str
    start_time: datetime
    end_time: datetime
    detail: str
    
class PhoneInterviewMail(BaseModel):
    time: datetime
    start_time: datetime
    end_time: datetime
    
class OtherInterviewMail(BaseModel):
    content: str
    

class CompanyInfo(BaseModel):
    company_name: str
    logo: str
    description: str
    industry: str
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
    industry: str
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
                industry: str = Form(...),
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
    industry: Optional[str]
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
                industry: Optional[str] = None,
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
    
        
class JobEducation(BaseModel):
    degree: Union[str, None]
    major: Union[str, None]
    gpa: Union[str, None]
    
class LanguageCertificate(BaseModel):
    certificate_language: Optional[str]
    certificate_name: Optional[str]
    certificate_point_level: Optional[str]
    
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

class ResumeUpdate(BaseModel):
    cv_id: int
    name: Union[str, None]
    level: str
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
    education: Union[List[ResumeEducation], None]
    work_experiences: Union[List[ResumeExperience], None]
    skills: Union[List[str], None]
    awards: Union[List[ResumeAward], None]
    projects: Union[List[ResumeProject], None]
    #   LanguageCertificate    
    language_certificates: Union[List[LanguageCertificate], None]
    #   OtherCertificates
    other_certificates: Union[List[OtherCertificate], None]


class AddCandidate(BaseModel):
    job_id: int
    cv_pdf: UploadFile

    @classmethod
    def as_form(cls, 
                job_id: str = Form(...),
                cv_pdf: UploadFile = File(...)):
        
        return cls(
                job_id=job_id,
                cv_pdf=cv_pdf,
                )
    

class UploadAvatar(BaseModel):
    cv_id: int
    avatar: UploadFile

    @classmethod
    def as_form(cls, 
                cv_id: str = Form(...),
                avatar: UploadFile = File(...)):
        
        return cls(
                cv_id=cv_id,
                avatar=avatar,
                )
    
    
class UpdateResumeValuation(BaseModel):
    cv_id: Optional[int]
    level: Optional[Level]
    current_salary: Optional[float]
    degrees: Optional[List[str]]
    language_certificates: Optional[List[LanguageCertificate]]
    
    
class ResumeValuateResult(BaseModel):
    hard_item: str
    hard_point: float
    degrees: List[str]
    degree_point: float
    certificates: List[LanguageCertificate]
    certificates_point: float
    total_point: float