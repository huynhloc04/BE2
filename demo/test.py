from enum import Enum

class PermissionType(str, Enum):
    """
    Enum for the different types of default
    permissions that can be applied to a model.
    """
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    def __str__(self):
        return f"{self.value}"
    
print(PermissionType.CREATE.value)





class RecruitResumeJoin(SQLModel, table=True):
    
    __tablename__ = "recruit_resume_join"
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        primary_key=True,
    )
    cv_id: Optional[int] = Field(
        default=None,
        foreign_key="resumes.id",
        primary_key=True,
    )
    package: str = Field(default=None)          
    is_rejected: bool = Field(default=False) 
    

class Resume(TableBase, table=True):
    __tablename__ = 'resumes'    
    user_id: int = Field(default=None, foreign_key="users.id")
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")       
    
    
class ResumeVersion(TableBase, table=True):
    __tablename__ = 'resume_versions'

    cv_id: int = Field(default=None, foreign_key="resumes.id")
    filename: str = Field(default=None)
    is_lastest: bool = Field(default=True)
    cv_file: str = Field(default=None)
    name: str = Field(default=None) 
    
    
Write SQLModel queryy to get "filename", "name" from "ResumeVersion" table that 
    
    
