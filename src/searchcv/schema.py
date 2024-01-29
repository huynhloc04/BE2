
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