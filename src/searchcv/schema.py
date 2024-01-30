
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
    
    
class ResumePackage(str, Enum):
    basic = "basic"
    platinum = "platinum"

    def __str__(self):
        return f"{self.value}"
    
class ChooseResume(BaseModel):
    cv_id: int
    package: ResumePackage
       
    
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
    candidate_accepted_interview = "candidate_accepted_interview"
    candidate_rejected_interview = "candidate_rejected_interview"

    def __str__(self):
        return f"{self.value}"