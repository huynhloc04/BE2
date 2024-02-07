
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile, Query
from pydantic import BaseModel

    
class CollaborateJobStatus(str, Enum):
    referred = "referred"
    favorite = "favorite"
    unreferred = "unreferred"

    def __str__(self):
        return f"{self.value}"


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
        
    
class BatchFilter(BaseModel):
    cv_lst: List[int]
    job_id: int
        
    
class ListGoodMatch(BaseModel):
    job_id: int
    limit: int
    page_index: int
        
    
class ResumeIndex(BaseModel):
    cv_id: int
    
    
class CandidateState(str, Enum):
    all = "all"
    new_candidate = "new_candidate"
    choosen_candidate = "choosen_candidate"
    inappro_candidate = "inappro_candidate"

    def __str__(self):
        return f"{self.value}"
    
class RecruitListCandidate(BaseModel):
    page_index: int
    limit: int
    state: CandidateState
    
    
class ChoosePlatinum(BaseModel):
    cv_id: int
    #   Schedule
    date: datetime
    location: str
    start_time: datetime
    end_time: datetime
    note: Optional[str]
       
    
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


class UploadResume(BaseModel):
    industry: Industry
    cv_file: UploadFile

    @classmethod
    def as_form(cls, 
                industry: Industry = Form(...),
                cv_file: UploadFile = File(...)):
        
        return cls(
                industry=industry,
                cv_file=cv_file,
            )
    

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
    accepted_interview = "accepted_interview"
    rejected_interview = "rejected_interview"

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
    
class LanguageCertificate(BaseModel):
    certificate_language: Optional[str]
    certificate_name: Optional[str]
    certificate_point_level: Optional[str]    
    
class UpdateResumeValuation(BaseModel):
    cv_id: Optional[int]
    level: Optional[Level]
    current_salary: Optional[float]
    degrees: Optional[List[str]]
    language_certificates: Optional[List[LanguageCertificate]]


class CollabListResume(BaseModel):
    page_index: int
    limit: int 
    is_draft: bool


class UpdateResume(BaseModel):
    cv_id: int
    avatar: Optional[UploadFile]
    cv_file: Optional[UploadFile]
    name: Optional[str]
    industry: Optional[Industry]
    level: Optional[Level]
    current_job: Optional[str]      
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]        
    objectives: Optional[List[str]]
    birthday: Optional[datetime]  # => age    
    gender: Optional[str]
    descriptions: Optional[str]
    identification_code: Optional[str]    
    linkedin: Optional[str]
    website: Optional[str]
    facebook: Optional[str]
    instagram: Optional[str]  
    education: Optional[List[str]]
    work_experiences: Optional[List[str]]
    skills: Optional[List[str]]
    awards: Optional[List[str]]
    projects: Optional[List[str]]
    language_certificates: Optional[List[str]]
    other_certificates: Optional[List[str]]

    @classmethod
    def as_form(cls, 
                cv_id: int = Form(None),
                avatar: Optional[UploadFile] = File(None),
                cv_file: Optional[UploadFile] = File(None),
                name: Optional[str] = Form(None),
                industry: Optional[Industry] = Form(None),
                level: Optional[Level] = Form(None),
                current_job: Optional[str] = Form(None),
                phone: Optional[str] = Form(None),
                email: Optional[str] = Form(None),
                address: Optional[str] = Form(None),
                descriptions: Optional[str] = Form(None),
                city: Optional[str] = Form(None),
                country: Optional[str] = Form(None),
                objectives: List[str] = Form(None),
                birthday: Optional[datetime] = Form(None),
                gender: Optional[str] = Form(None),
                identification_code: Optional[str] = Form(None),
                linkedin: Optional[str] = Form(None),
                website: Optional[str] = Form(None),
                facebook: Optional[str] = Form(None),
                instagram: Optional[str] = Form(None),
                skills: Optional[List[str]] = Form(None),
                education: Optional[List[str]] = Form(None),
                work_experiences: Optional[List[str]] = Form(None),
                awards: Optional[List[str]] = Form(None),
                projects: Optional[List[str]] = Form(None),
                language_certificates: Optional[List[str]] = Form(None),
                other_certificates: Optional[List[str]] = Form(None)):
        
        return cls(
                cv_id=cv_id,
                avatar=avatar,
                cv_file=cv_file,
                name=name,
                industry=industry,
                descriptions=descriptions,
                level=level,
                current_job=current_job,
                phone=phone,
                email=email,
                address=address,
                city=city,
                country=country,
                objectives=objectives,
                birthday=birthday,
                gender=gender,
                identification_code=identification_code,
                linkedin=linkedin,
                website=website,
                facebook=facebook,
                instagram=instagram,
                education=education,
                work_experiences=work_experiences,
                skills=skills,
                awards=awards,
                projects=projects,
                language_certificates=language_certificates,
                other_certificates=other_certificates)
        
        
class RecruitRejectCandidate(BaseModel):
    cv_id: int
    decline_reason: Optional[str]
    
    
class InterviewStatus(str, Enum):
    accept = "accept"
    reject = "reject"

    def __str__(self):
        return f"{self.value}"
    
class IsAcceptInterview(BaseModel):
    cv_id: int
    status: InterviewStatus

    
class CandidateStatus(str, Enum):
    all = "all"
    pending = "pending"
    approved = "approved"
    declined = "declined"

    def __str__(self):
        return f"{self.value}"

class AdminListCandidate(BaseModel):
    page_index: int
    limit: int
    candidate_status: CandidateStatus