from datetime import datetime
from sqlalchemy import text, Column, TIMESTAMP
from sqlmodel import Field, SQLModel, Relationship, JSON
from typing import List, Optional, Set
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.dialects import postgresql
from enum import Enum
from sqlalchemy.types import Integer, STRINGTYPE


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


class User(TableBase, table=True):
    __tablename__ = 'users'

    fullname: str = Field(default=None)
    email: str = Field(default=None)
    phone: str = Field(default=None)
    # identification_code: str = Field(default=None, unique=True)
    role: str = Field(default=None)
    # birthday: str = Field(default=None)
    point: float = Field(default=0)
    avatar: str = Field(default=None)
    # sex: str = Field(default=None)
    country: str = Field(default=None)
    city: str = Field(default=None)
    address: str = Field(default=None, sa_column=Column(TEXT))
    password: str = Field(default=None)
    last_signed_in: datetime = Field(default=None)
    refresh_token: str = Field(max_length=255, nullable=True)
    otp_token: str = Field(default=None)
    is_verify: Optional[bool] = Field(default=False)
    is_active: Optional[bool] = Field(default=False)
    is_verify_forgot_password: Optional[bool] = Field(default=False)


class JWTModel(TableBase, table=True): # BlacklistToken
    __tablename__ = "blacklisted_jwt"
    
    token: str = Field(unique=True, nullable=False)


class Company(TableBase, table=True):
    __tablename__ = 'companies'
    
    user_id: int = Field(default=None, foreign_key="users.id")
    company_name: str = Field(default=None)
    industry: str = Field(default=None)
    phone: str = Field(default=None)
    email: str = Field(default=None)
    description: str = Field(default=None, sa_column=Column(TEXT))
    founded_year: int = Field(default=None)
    company_size: int = Field(default=None)
    tax_code: str = Field(default=None)    
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


class Industry(TableBase, table=True):
    __tablename__ = 'industries'
    
    industry_name: str = Field(default=None)


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


class ResumeOld(TableBase, table=True):
    __tablename__ = 'resume_olds'
    
    industry_id: int = Field(default=None, foreign_key="industries.id")
    user_id: int = Field(default=None, foreign_key="users.id")


class ResumeNew(TableBase, table=True):
    __tablename__ = 'resume_news'
    
    industry_id: int = Field(default=None, foreign_key="industries.id")
    user_id: int = Field(default=None, foreign_key="users.id")
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")


class ResumeVersion(TableBase, table=True):
    __tablename__ = 'resume_versions'

    old_id: int = Field(default=None, foreign_key="resume_olds.id")
    new_id: int = Field(default=None, foreign_key="resume_news.id")
    filename: str = Field(default=None)
    is_lastest: bool = Field(default=False)
    cv_pdf: str = Field(default=None)
    candidate_name: str = Field(default=None) 
    sex: str = Field(default=None)
    current_job: str = Field(default=None)
    current_job_industry: str = Field(default=None)
    email: str = Field(default=None)
    phone: str = Field(default=None)  
    address: str = Field(default=None, sa_column=Column(TEXT))
    city: str = Field(default=None)
    country: str = Field(default=None)  
    description: str = Field(default=None, sa_column=Column(TEXT))
    birthday: str = Field(default=None)
    identification_code: str = Field(default=None, unique=True)
    linkedin: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    facebook: Optional[str] = Field(default=None)
    instagram: Optional[str] = Field(default=None)
    resume_status: bool = Field(default="pending")
    package: str = Field(default=None)
    point: float = Field(default=0.0)
    is_valuate: bool = Field(default=False)
    is_ai_matching: bool = Field(default=False)
    is_admin_matching: bool = Field(default=False)
    matching_decline_reason: str = Field(default=None, sa_column=Column(TEXT))