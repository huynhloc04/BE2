
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile, Query
from pydantic import BaseModel


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
    
class DrawMoney(BaseModel):
    draw_point: int
    
class ResumeIndex(BaseModel):
    cv_id: int
    
class JobIndex(BaseModel):
    job_id: int

    
class DrawStatus(str, Enum):
    pending = "pending"
    allowed = "allowed"
    drawed = "drawed"

    def __str__(self):
        return f"{self.value}"