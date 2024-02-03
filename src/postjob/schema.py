
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile, Query
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
    
    

class AdminReviewMatching(BaseModel):
    cv_id: int
    resume_status: CandidateMailReply 
    decline_reason: Optional[str]
    
    
class ResumePackage(str, Enum):
    basic = "basic"
    platinum = "platinum"

    def __str__(self):
        return f"{self.value}"
    
class ChooseResume(BaseModel):
    cv_id: int
    package: ResumePackage
    
    
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
    
    
class JobStatus(str, Enum):
    pending = "pending"
    browsing = "browsing"
    recruiting = "recruiting"
    paused = "paused"

    def __str__(self):
        return f"{self.value}"

    
class CandidateStatus(str, Enum):
    all = "all"
    pending = "pending"
    approved = "approved"
    declined = "declined"

    def __str__(self):
        return f"{self.value}"

class InterviewForm(BaseModel):
    cv_id: int
    interview_form: InterviewEnum


class RecruitRejectResume(BaseModel):
    cv_id: int
    decline_reason: Optional[str]


class ResumeIndex(BaseModel):
    cv_id: int
    
    
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
    
        
class JobEducation(BaseModel):
    degree: Optional[str]
    major: Optional[str]
    gpa: Optional[str]
    
class LanguageCertificate(BaseModel):
    certificate_language: Optional[str]
    certificate_name: Optional[str]
    certificate_point_level: Optional[str]
    
class OtherCertificate(BaseModel):
    certificate_name: Optional[str]
    certificate_level: Optional[str]

class FillJob(BaseModel):
    jd_file: UploadFile
    job_title: str
    industries: List[str]
    gender: GenderChoice
    job_type: str
    skills: List[str]
    received_job_time: datetime
    working_time: str
    descriptions: List[str]
    requirements: List[str]
    benefits: List[str]
    levels: List[str]
    roles: List[str]
    yoe: int
    num_recruit: int
    education: Optional[List[str]]
    language_certificates: Optional[List[str]]
    other_certificates: Optional[List[str]]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    min_salary: Optional[float]
    max_salary: Optional[float]
    currency: Optional[str]

    @classmethod
    def as_form(cls, 
                jd_file: UploadFile = File(...),
                job_title: str = Form(...),
                industries: List[str] = Form(...),
                gender: GenderChoice = Form(...),
                job_type: str = Form(...),
                skills: List[str] = Form(...),
                received_job_time: datetime = Form(...),
                working_time: str = Form(...),
                descriptions: List[str] = Form(...),
                requirements: List[str] = Form(...),
                benefits: List[str] = Form(...),
                levels: List[str] = Form(...),
                roles: List[str] = Form(...),
                yoe: int = Form(...),
                num_recruit: int = Form(...),
                education: Optional[List[str]] = Form(None),
                language_certificates: Optional[List[str]] = Form(None),
                other_certificates: Optional[List[str]] = Form(None),
                address: Optional[str] = Form(None),
                city: Optional[str] = Form(None),
                country: Optional[str] = Form(None),
                min_salary: Optional[float] = Form(None),
                max_salary: Optional[float] = Form(None),
                currency: Optional[str] = Form(None),
        ):
        return cls(
            jd_file=jd_file,
            job_title=job_title,
            industries=industries,
            gender=gender,
            job_type=job_type,
            skills=skills,
            received_job_time=received_job_time,
            working_time=working_time,
            descriptions=descriptions,
            requirements=requirements,
            benefits=benefits,
            levels=levels,
            roles=roles,
            yoe=yoe,
            num_recruit=num_recruit,
            education=education,
            language_certificates=language_certificates,
            other_certificates=other_certificates,
            address=address,
            city=city,
            country=country,
            min_salary=min_salary,
            max_salary=max_salary,
            currency=currency,
        )
    

class JobUpdate(BaseModel):
    job_id: int
    job_title: Optional[str]
    industries: Optional[List[Industry]]
    gender: Optional[GenderChoice]
    job_type: Optional[str]
    skills: Optional[List[str]]
    #   Education
    education: Union[List[JobEducation], None]
    #   LanguageCertificate    
    language_certificates: Optional[List[LanguageCertificate]]
    #   OtherCertificates
    other_certificates: Optional[List[OtherCertificate]]
    #   Location
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    received_job_time: Optional[datetime]
    working_time: Optional[str]
    descriptions: Optional[List[str]]
    requirements: Optional[List[str]]
    benefits: Optional[List[str]]
    levels: Optional[List[Level]]
    roles: Optional[List[str]]
    yoe: Optional[int]
    num_recruit: Optional[int]
    min_salary: Optional[float]
    max_salary: Optional[float]
    currency: Optional[str]
    #   Chỉ xuất hiện bên trang Admin, và lúc NTD xem lại JD đã up (Admin check và gửi lại cho NTD)
    admin_decline_reason: Optional[str]

    
# ===========================================================
#                           Resumes
# ===========================================================

class ResumeEducation(BaseModel):
    degree: Optional[str]
    institute_name: Optional[str]
    major: Optional[str]
    gpa: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]

class ResumeExperience(BaseModel):
    company_name: Optional[str]
    job_tile: Optional[str]
    working_industry: Optional[Industry]
    levels: Optional[Level]
    roles: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]

class ResumeAward(BaseModel):
    name: Optional[str]
    time: Optional[str]
    description: Optional[str]

class ResumeProject(BaseModel):
    project_name: Optional[str]
    descriptions: Optional[List[str]]
    start_time: Optional[str]
    end_time: Optional[str]


class FillResume(BaseModel):
    job_id: int
    avatar: UploadFile
    cv_file: UploadFile
    name: str
    industry: Industry
    level: Level
    current_job: str      
    phone: str
    email: str
    address: str
    city: str
    country: str        
    objectives: List[str]
    birthday: datetime  # => age    
    gender: str
    descriptions: Optional[str]
    identification_code: str    
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
                job_id: int = Form(...),
                avatar: UploadFile = File(...),
                cv_file: UploadFile = File(...),
                name: str = Form(...),
                industry: Industry = Form(...),
                level: Level = Form(...),
                current_job: str = Form(...),
                phone: str = Form(...),
                email: str = Form(...),
                address: str = Form(...),
                descriptions: Optional[str] = Form(...),
                city: str = Form(...),
                country: str = Form(...),
                objectives: List[str] = Form(...),
                birthday: datetime = Form(...),
                gender: str = Form(...),
                identification_code: str = Form(...),
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
                job_id=job_id,
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
    

class RecruitPauseJob(BaseModel):
    job_id: int
    is_active: bool
    

class AdminReviewJob(BaseModel):
    job_id: int
    is_approved: bool
    decline_reason: Optional[str]
    

class AdminPauseJob(BaseModel):
    job_id: int
    is_active: bool


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


class RecruitListJob(BaseModel):
    page_index: int
    limit: int 
    is_draft: bool


class CollabListResume(BaseModel):
    page_index: int
    limit: int 
    is_draft: bool

class CollabListJob(BaseModel):
    page_index: int
    limit: int
    job_status: CollaborateJobStatus

class AdminListJob(BaseModel):
    page_index: int
    limit: int
    job_status: JobStatus

class AdminListCandidate(BaseModel):
    page_index: int
    limit: int
    candidate_status: CandidateStatus


class UpdateResumeDraft(BaseModel):
    cv_id: int
    is_draft: bool 

