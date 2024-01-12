
from datetime import datetime
from sqlalchemy import text, Column, TIMESTAMP
from sqlmodel import Field, SQLModel, Relationship, JSON
from typing import List, Optional, Set
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.dialects import postgresql
from enum import Enum
from sqlalchemy.types import Integer, String


class TableBase(SQLModel):
    """
    A base class for SQLModel tables.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=datetime.utcnow,
        )
    )


class Job_User_Join(TableBase, table=True):
    """
    A link between a blog JobDescription and User.
    """
    
    __tablename__ = "job_user_joins"
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        primary_key=True,
    )
    job_id: Optional[int] = Field(
        default=None,
        foreign_key="job_descriptions.id",
        primary_key=True,
    )
    is_favorite: bool = Field(default=False)


class User(TableBase, table=True):
    __tablename__ = 'users'
    
    fullname: str = Field(default=None)
    email: str = Field(unique=True, default=None)
    phone: str = Field(unique=True, default=None)
    role: str = Field(default='admin')
    point: int = Field(nullable=True, default=None)
    hashed_password: str = Field(nullable=True, default=None)
    avatar: str = Field(default=None)
    sex: str = Field(default=None)
    address: str = Field(default=None, sa_column=Column(TEXT))
    linkedin: str = Field(default=None, sa_column=Column(TEXT))
    refresh_token: str = Field(max_length=255, nullable=True)
    is_verify: Optional[bool] = Field(default=False)
    is_active: Optional[bool] = Field(default=False)
    is_verify_forgot_password: Optional[bool] = Field(default=False)
    jobs: List["JobDescription"] = Relationship(back_populates="users", 
                                                link_model=Job_User_Join)


class Company(TableBase, table=True):
    __tablename__ = 'companies'
    
    user_id: int = Field(default=None, foreign_key="users.id")
    company_name: str = Field(default=None)
    industry: str = Field(default=None)
    description: str = Field(default=None)
    tax_code: str = Field(default=None)
    phone: str = Field(default=None)
    email: str = Field(default=None)
    founded_year: int = Field(default=None)
    company_size: int = Field(default=None)
    address: str = Field(default=None, sa_column=Column(TEXT))
    city: str = Field(default=None)
    country: str = Field(default=None)
    logo: str = Field(default=None)
    cover_image: Optional[str] = Field(default=None)
    company_images: Optional[List[str]] = Field(default=None)
    company_video: Optional[str] = Field(default=None)
    linkedin: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    facebook: Optional[str] = Field(default=None)
    instagram: Optional[str] = Field(default=None)


class JobDescription(TableBase, table=True):
    __tablename__ = 'job_descriptions'

    company_id: int = Field(default=None, foreign_key="companies.id")
    job_title: str = Field(default=None)
    industry: str = Field(default=None)
    sex: Optional[str] = Field(default=None)
    job_type: str = Field(default=None)
    skills: List[str] = Field(default=None)
    recieved_job_time: datetime = Field(default=None)
    working_time: str = Field(default=None)
    description: str = Field(default=None)
    requirement: str = Field(default=None)
    benefits: str = Field(default=None)
    level: str = Field(default=None)          # (Cấp bậc đảm nhiệm)
    roles: List[str] = Field(default=None)    # (Vai trò đảm nhiệm: Tối đa 3 lựa chọn)
    yoe: int = Field(default=None)
    num_recruit: int = Field(default=None)
    #    Học vấn
    degree: str = Field(default=None)       # (Cử nhân, Thạc sĩ, Tiến sĩ, Kỹ sư)
    major: str = Field(default=None)
    ranking: str = Field(default=None)       # (Xuất sắc, Giỏi, Khá)
    language: str = Field(default=None)       # (English, Chinese, Korean, Japan, Vietnamese)
    language_level: str = Field(default=None)
    #    Lương thưởng
    min_salary: str = Field(default=None)     # (default: Thảo thuận)
    max_salary: str = Field(default=None)     # (default: Thảo thuận)
    #    Địa chỉ
    address: str = Field(default=None)
    city: str = Field(default=None)
    country: str = Field(default=None)
    #    Treo thưởng (Chỉ hiển thị khi là Headhunt)
    point: int = Field(default=None)
    guarantee: int = Field(default=None)
    jd_file: str = Field(default=None)
    #    Tình trạng Job
    job_status: str = Field(default="Chờ duyệt")     # JobStatus -[default: Chờ duyệt] (Chờ duyệt, Đang tuyển, Đã tuyeẻn, Tạm dừng)  
    #    Bản nháp
    is_draft: bool = Field(default=False)  
    users: List[User] = Relationship(back_populates="jobs", 
                                     link_model=Job_User_Join)
     

class Resume(TableBase, table=True):
    __tablename__ = 'resumes'

    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    user_id: int = Field(default=None, foreign_key="users.id")
    status: str = Field(default="decline")  #   Admin an "Duyet" => Send email to UV, UV an "Accept/Decline"
    name: str = Field(default=None)    #   Ten cong viec
    job_title: str = Field(default=None)
    wait_date: int = Field(default=0)
    email: str = Field(default=None)
    phone: str = Field(default=None)
    industry: str = Field(default=None)     #   Nganh nghe
    reason: str = Field(default=None, sa_column=Column(TEXT))     #   Ly do ung tuyen  
    expectation: str = Field(default=None, sa_column=Column(TEXT))     #   Nguyen vong  
    amount: int = Field(default=None)     #   So luong ung tuyen
    level: str = Field(default=None)     #   Cap do
    role: str = Field(default=None)     #   Vai tro
    salary_min: float = Field(default=None)     #   Cap do
    salary_max: float = Field(default=None)     #   Cap do
    current_salary: float = Field(default=None)     #   Cap do
    desired_work_loc: str = Field(default=None, sa_column=Column(TEXT))     #   Noi lam viec mong muon 
    skills: str = Field(default=None)     #   Ky nang
    spoken_lang: str = Field(default=None) 
    spoken_lang_level: str = Field(default=None) 
    yoe: int = Field(default=None)
    experience: str = Field(default=None, sa_column=Column(TEXT))    
    experience_level: str = Field(default=None)
    cv_link: str = Field(default=None)      #  Link CV


class JWTModel(TableBase, table=True): # BlacklistToken
    __tablename__ = "blacklisted_jwt"
    
    token: str = Field(unique=True, nullable=False)


class OTPModel(TableBase, table=True):
    __tablename__ = "otps"

    user_id: int = Field(foreign_key="users.id")
    otp: Optional[str] = Field(nullable=True)
















# from datetime import datetime
# from sqlalchemy import text, Column, TIMESTAMP
# from sqlmodel import Field, SQLModel, Relationship, JSON
# from typing import List, Optional, Set
# from sqlalchemy.dialects.postgresql import TEXT
# from sqlalchemy.dialects import postgresql
# from enum import Enum
# from sqlalchemy.types import Integer, String


# class TableBase(SQLModel):
#     """
#     A base class for SQLModel tables.
#     """
#     id: Optional[int] = Field(default=None, primary_key=True)
#     created_at: Optional[datetime] = Field(
#         sa_column=Column(
#             TIMESTAMP(timezone=True),
#             nullable=False,
#             server_default=text("CURRENT_TIMESTAMP"),
#         ),
#     )
#     updated_at: Optional[datetime] = Field(
#         sa_column=Column(
#             TIMESTAMP(timezone=True),
#             nullable=False,
#             server_default=text("CURRENT_TIMESTAMP"),
#             onupdate=datetime.utcnow,
#         )
#     )


# class JobUserJoin(TableBase, table=True):
#     """
#     A link between a blog JobDescription and User: Mark this Job is_favorite.
#     """
    
#     __tablename__ = "job_user_joins"
#     user_id: Optional[int] = Field(
#         default=None,
#         foreign_key="users.id",
#         primary_key=True,
#     )
#     job_id: Optional[int] = Field(
#         default=None,
#         foreign_key="job_descriptions.id",
#         primary_key=True,
#     )
#     is_favorite: bool = Field(default=False)


# class User(TableBase, table=True):
#     __tablename__ = 'users'
    
#     name: str = Field(default=None)
#     email: str = Field(unique=True, default=None)
#     phone: str = Field(unique=True, default=None)
#     role: str = Field(default='admin')
#     birthday: datetime = Field(default=None)
#     point: int = Field(nullable=True, default=None)
#     hashed_password: str = Field(nullable=True, default=None)
#     avatar: str = Field(default=None)
#     sex: str = Field(default=None)
#     country: str = Field(default=None)
#     city: str = Field(default=None)
#     address: str = Field(default=None)
#     identification_code: str = Field(unique=True, default=None)
#     refresh_token: str = Field(max_length=255, nullable=True)
#     is_verify: Optional[bool] = Field(default=False)
#     is_active: Optional[bool] = Field(default=False)
#     is_verify_forgot_password: Optional[bool] = Field(default=False)
#     jobs: List["JobDescription"] = Relationship(back_populates="users", link_model=JobUserJoin)


# class Company(TableBase, table=True):
#     __tablename__ = 'companies'
    
#     user_id: int = Field(default=None, foreign_key="users.id")
#     name: str = Field(default=None)
#     industry: str = Field(default=None)
#     description: str = Field(default=None, sa_column=Column(TEXT))
#     email: str = Field(default=None)
#     phone: str = Field(default=None)
#     founded_year: int = Field(default=None)
#     size: int = Field(default=None)
#     tax_code: str = Field(default=None)
#     country: str = Field(default=None)
#     city: str = Field(default=None)
#     address: str = Field(default=None, sa_column=Column(TEXT))
#     logo: str = Field(default=None)
#     cover_image: Optional[str] = Field(default=None)
#     company_images: Optional[List[str]] = Field(default=None)
#     company_video: Optional[str] = Field(default=None)
#     linkedin: Optional[str] = Field(default=None)
#     website: Optional[str] = Field(default=None)
#     facebook: Optional[str] = Field(default=None)
#     instagram: Optional[str] = Field(default=None)


# class JobDescription(TableBase, table=True):
#     __tablename__ = 'job_descriptions'

#     company_id: int = Field(default=None, foreign_key="companies.id")
#     job_title: str = Field(default=None)
#     industry: str = Field(default=None)
#     sex: Optional[str] = Field(default=None)
#     job_type: str = Field(default=None)
#     skills: List[str] = Field(default=None)
#     recieved_job_time: datetime = Field(default=None)
#     working_time: str = Field(default=None)
#     description: str = Field(default=None, sa_column=Column(TEXT))
#     requirement: str = Field(default=None)
#     benefits: str = Field(default=None)
#     levels: List[str] = Field(default=None)          # (Cấp bậc đảm nhiệm)
#     roles: List[str] = Field(default=None)    # (Vai trò đảm nhiệm: Tối đa 3 lựa chọn)
#     yoe: int = Field(default=None)
#     num_recruit: int = Field(default=None)
#     #    Học vấn
#     degree: str = Field(default=None)       # (Cử nhân, Thạc sĩ, Tiến sĩ, Kỹ sư)
#     major: str = Field(default=None)
#     gpa: float = Field(default=None)       # (Xuất sắc, Giỏi, Khá)
#     language: str = Field(default=None)       # (English, Chinese, Korean, Japan, Vietnamese)
#     language_certificate: str = Field(default=None)
#     language_certificate_level: str = Field(default=None)
#     #    Lương thưởng
#     min_salary: str = Field(default=None)     # (default: Thảo thuận)
#     max_salary: str = Field(default=None)     # (default: Thảo thuận)
#     currency: str = Field(default=None) 
#     #    Địa chỉ
#     address: str = Field(default=None)
#     city: str = Field(default=None)
#     country: str = Field(default=None)
#     #    Treo thưởng (Chỉ hiển thị khi là Headhunt)
#     point: int = Field(default=None)
#     guarantee: int = Field(default=None)
#     jd_file: str = Field(default=None)
#     #    Tình trạng Job
#     status: str = Field(default="Pending")  
#     #    Bản nháp
#     is_draft: bool = Field(default=True)  
#     is_admin_approved: bool = Field(default=False)  
#     admin_decline_reason: str = Field(default=None, sa_column=Column(TEXT))
#     company_decline_reason: str = Field(default=None, sa_column=Column(TEXT))
#     users: List[User] = Relationship(back_populates="jobs", link_model=JobUserJoin)
    

# class ResumeOld(TableBase, table=True):
#     __tablename__ = 'resume_olds'

#     job_id: int = Field(default=None, foreign_key="job_descriptions.id")
#     user_id: int = Field(default=None, foreign_key="users.id")
#     filename: str = Field(default=None)
    

# class ResumeNew(TableBase, table=True):
#     __tablename__ = 'resume_news'

#     job_id: int = Field(default=None, foreign_key="job_descriptions.id")
#     user_id: int = Field(default=None, foreign_key="users.id")
#     filename: str = Field(default=None)
     

# class ResumeVersion(TableBase, table=True):
#     __tablename__ = 'resume_versions'

#     cv_file: str = Field(default=None)      #  Link CV
#     name: str = Field(default=None)    #   Ten cong viec
#     current_job: str = Field(default=None)
#     current_job_industry: str = Field(default=None)
#     email: str = Field(default=None)
#     phone: str = Field(default=None)
#     address: str = Field(default=None)
#     city: str = Field(default=None)
#     country: str = Field(default=None)
#     description: str = Field(default=None, sa_column=Column(TEXT))
#     birthday: datetime = Field(default=None)
#     identification_code: str = Field(unique=True, default=None)
#     sex: str = Field(default=None)
#     linkedin: Optional[str] = Field(default=None)
#     website: Optional[str] = Field(default=None)
#     facebook: Optional[str] = Field(default=None)
#     instagram: Optional[str] = Field(default=None)
#     status: str = Field(default="pending")
#     package: str = Field(default=None)
#     is_ai_valuated: bool = Field(default=False)  
#     is_admin_valuated: bool = Field(default=False)  
#     warning_content: str = Field(default=None, sa_column=Column(TEXT))
#     is_ai_matching: bool = Field(default=False)  
#     is_admin_matching: bool = Field(default=False) 
#     matching_decline_reason: str = Field(default=None, sa_column=Column(TEXT))
#     point: int = Field(nullable=True, default=None)
    

# class Education(TableBase, table=True):
#     __tablename__ = 'educations'

#     resume_id: int = Field(default=None, foreign_key="resume_versions.id")
#     degree: str = Field(default=None) 
#     institute_name: str = Field(default=None) 
#     major: str = Field(default=None) 
#     gpa: float = Field(default=None) 
#     start_time: datetime = Field(default=None)
#     end_time: datetime = Field(default=None)
    

# class WorkExperience(TableBase, table=True):
#     __tablename__ = 'work_experiences'

#     resume_id: int = Field(default=None, foreign_key="resume_versions.id")
#     company_name: str = Field(default=None) 
#     logo: str = Field(default=None) 
#     job_title: str = Field(default=None) 
#     industry: str = Field(default=None) 
#     levels: List[str] = Field(default=None)          # (Cấp bậc đảm nhiệm)
#     roles: List[str] = Field(default=None)
#     start_time: datetime = Field(default=None)
#     end_time: datetime = Field(default=None)
    

# class Skill(TableBase, table=True):
#     __tablename__ = 'skills'

#     resume_id: int = Field(default=None, foreign_key="resume_versions.id")
#     name: str = Field(default=None) 
    

# class Project(TableBase, table=True):
#     __tablename__ = 'projects'

#     resume_id: int = Field(default=None, foreign_key="resume_versions.id")
#     project_name: str = Field(default=None) 
#     description: str = Field(default=None, sa_column=Column(TEXT))
#     start_time: datetime = Field(default=None)
#     end_time: datetime = Field(default=None)
    

# class Award(TableBase, table=True):
#     __tablename__ = 'awards'

#     resume_id: int = Field(default=None, foreign_key="resume_versions.id")
#     name: str = Field(default=None) 
#     time: datetime = Field(default=None)
#     description: str = Field(default=None, sa_column=Column(TEXT))


# class JWTModel(TableBase, table=True): # BlacklistToken
#     __tablename__ = "blacklisted_jwt"
    
#     token: str = Field(unique=True, nullable=False)


# class OTPModel(TableBase, table=True):
#     __tablename__ = "otps"

#     user_id: int = Field(foreign_key="users.id")
#     otp: Optional[str] = Field(nullable=True)