from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel


# class CustomResponse(BaseModel):
#     message: str = None
#     data: Any = None
    
    
# class CollaborateJobStatus(str, Enum):
#     referred = "referred"
#     favorite = "favorite"
#     unreferred = "unreferred"

#     def __str__(self):
#         return f"{self.value}"