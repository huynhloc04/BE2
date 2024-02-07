import os
from fastapi import Request 
from datetime import datetime, time
from sqlalchemy import text, Column, TIMESTAMP
from sqlmodel import Field, SQLModel, Relationship, JSON
from typing import List, Optional, Set, Dict
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


class User(TableBase, table=True):
    __tablename__ = 'users'

    fullname: str = Field(default=None)
    email: str = Field(default=None)
    phone: str = Field(default=None)
    role: str = Field(default=None)
    point: float = Field(default=0)
    warranty_point: float = Field(default=0)    #   Only Collaborator
    avatar: str = Field(default=None)
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


class JobDescription(TableBase, table=True):
    __tablename__ = 'job_descriptions'

    user_id: int = Field(default=None, foreign_key="users.id")
    company_id: int = Field(default=None, foreign_key="companies.id")
    status: str = Field(default=None)
    job_service: str = Field(default=None)
    job_title: str = Field(default=None)
    industries: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    gender: Optional[str] = Field(default=None)
    job_type: str = Field(default=None)
    skills: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    received_job_time: datetime = Field(default=None)
    working_time: str = Field(default=None)
    descriptions: str = Field(default=None, sa_column=Column(TEXT))
    requirements: str = Field(default=None, sa_column=Column(TEXT))
    benefits: str = Field(default=None, sa_column=Column(TEXT))
    levels: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    roles: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    yoe: str = Field(default=None)
    num_recruit: int = Field(default=None)
    min_salary: float = Field(default=None)
    max_salary: float = Field(default=None)
    currency: str = Field(default=None)
    address: str = Field(default=None)
    city: str = Field(default=None)
    country: str = Field(default=None)
    headhunt_point: int = Field(default=None)
    correspone_price: float = Field(default=None)
    warranty_time: int = Field(default=None)
    jd_file: str = Field(default=None)
    status: str = Field(default="pending")
    is_draft: bool = Field(default=False)
    is_active: bool = Field(default=True)
    is_admin_approved: bool = Field(default=False)      # Admin filtered Job
    admin_decline_reason: str = Field(default=None, sa_column=Column(TEXT))


class Bank(TableBase, table=True):
    __tablename__ = 'banks'    
    user_id: int = Field(default=None, foreign_key="users.id")
    bank_name: str = Field(default=None)
    branch_name: str = Field(default=None)
    account_owner: str = Field(default=None)
    account_number: str = Field(default=None)


class Company(TableBase, table=True):
    __tablename__ = 'companies'    
    user_id: int = Field(default=None, foreign_key="users.id")
    company_name: str = Field(default=None)
    industry: str = Field(default=None)
    phone: str = Field(default=None)
    email: str = Field(default=None)
    description: str = Field(default=None, sa_column=Column(TEXT))
    founded_year: int = Field(default=None)
    company_size: str = Field(default=None)
    tax_code: str = Field(default=None)    
    address: str = Field(default=None, sa_column=Column(TEXT))
    city: str = Field(default=None)
    country: str = Field(default=None)    
    logo: str = Field(default=None)
    cover_image: Optional[str] = Field(default=None)
    company_images: Optional[List[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    company_video: Optional[str] = Field(default=None)
    linkedin: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    facebook: Optional[str] = Field(default=None)
    instagram: Optional[str] = Field(default=None)
    
class JobEducation(TableBase, table=True):
    __tablename__ = 'job_educations'    
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    degree: str = Field(default=None)
    major: str = Field(default=None)
    gpa: float = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    
class LanguageJobCertificate(TableBase, table=True):
    __tablename__ = 'language_job_certificates'    
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    certificate_language: str = Field(default=None)
    certificate_name: str = Field(default=None)
    certificate_point_level: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    
class OtherJobCertificate(TableBase, table=True):
    __tablename__ = 'other_job_certificates'    
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    certificate_name: str = Field(default=None)
    certificate_point_level: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)


class Resume(TableBase, table=True):
    __tablename__ = 'resumes'    
    user_id: int = Field(default=None, foreign_key="users.id")
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    is_active: bool = Field(default=True)


class ValuationInfo(TableBase, table=True):
    __tablename__ = 'valuation_infos'
    cv_id: int = Field(default=None, foreign_key="resumes.id")
    hard_item: str = Field(default=None)
    hard_point: float = Field(default=None)
    degrees: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    degree_point: float = Field(default=None)
    certificates: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    certificates_point: float = Field(default=None)
    total_point: float = Field(default=None)


class ResumeVersion(TableBase, table=True):
    __tablename__ = 'resume_versions'

    cv_id: int = Field(default=None, foreign_key="resumes.id")
    filename: str = Field(default=None)
    is_lastest: bool = Field(default=True)
    cv_file: str = Field(default=None)
    name: str = Field(default=None)
    avatar: str = Field(default=os.path.join(str(Request.base_url), 'static/resume/avatar/default_avatar.png')) 
    level: str = Field(default=None) 
    gender: str = Field(default=None)
    industry: str = Field(default=None)
    current_job: str = Field(default=None)
    skills: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    email: str = Field(default=None)
    phone: str = Field(default=None)  
    address: str = Field(default=None, sa_column=Column(TEXT))
    city: str = Field(default=None)
    country: str = Field(default=None)  
    descriptions: List[str] = Field(default=None, sa_column=Column(TEXT))
    birthday: datetime = Field(default=None)
    identification_code: str = Field(default=None, unique=True)
    linkedin: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    facebook: Optional[str] = Field(default=None)
    instagram: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    objectives: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    is_draft: bool = Field(default=False)
    is_ai_matched: bool = Field(default=False)
    matching_decline_reason: str = Field(default=None, sa_column=Column(TEXT))
    interview_decline_reason: str = Field(default=None, sa_column=Column(TEXT))
    point_recieved_time: datetime = Field(default=None)
    point_draw_status: str = Field(default=None)


class ResumeEducation(TableBase, table=True):
    __tablename__ = 'resume_educations'
    cv_id: int = Field(default=None, foreign_key="resume_versions.id")
    degree: str = Field(default=None)
    institute_name: str = Field(default=None)
    major: str = Field(default=None)
    gpa: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)

class ResumeExperience(TableBase, table=True):
    __tablename__ = 'resume_experiences'
    cv_id: int = Field(default=None, foreign_key="resume_versions.id")
    company_name: str = Field(default=None)
    job_title: str = Field(default=None)
    working_industry: str = Field(default=None)
    levels: str = Field(default=None)
    roles: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)

class ResumeAward(TableBase, table=True):
    __tablename__ = 'resume_awards'
    cv_id: int = Field(default=None, foreign_key="resume_versions.id")
    name: str = Field(default=None)
    time: str = Field(default=None)
    description: str = Field(default=None, sa_column=Column(TEXT))


class ResumeProject(TableBase, table=True):
    __tablename__ = 'resume_projects'
    cv_id: int = Field(default=None, foreign_key="resume_versions.id")
    project_name: str = Field(default=None)
    descriptions: List[str] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    
    
class LanguageResumeCertificate(TableBase, table=True):
    __tablename__ = 'language_resume_certificates'    
    cv_id: int = Field(default=None, foreign_key="resumes.id")
    certificate_language: str = Field(default=None)
    certificate_name: str = Field(default=None)
    certificate_point_level: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    
    
class OtherResumeCertificate(TableBase, table=True):
    __tablename__ = 'other_resume_certificates'    
    cv_id: int = Field(default=None, foreign_key="resumes.id")
    certificate_name: str = Field(default=None)
    certificate_point_level: str = Field(default=None)
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)
    

class ResumeMatching(TableBase, table=True):
    __tablename__ = 'matching_results'      
    job_id: int = Field(default=None, foreign_key="job_descriptions.id")
    cv_id: int = Field(default=None, foreign_key="resumes.id")
    title_score: int = Field(default=None)
    title_explain: str = Field(default=None, sa_column=Column(TEXT))
    exper_score: int = Field(default=None)
    exper_explain: str = Field(default=None, sa_column=Column(TEXT))
    skill_score: int = Field(default=None)
    skill_explain: str = Field(default=None, sa_column=Column(TEXT))
    education_score: int = Field(default=None)
    education_explain: str = Field(default=None, sa_column=Column(TEXT))
    orientation_score: int = Field(default=None)
    orientation_explain: str = Field(default=None, sa_column=Column(TEXT))
    overall_score: int = Field(default=None)
    overall_explain: str = Field(default=None, sa_column=Column(TEXT))
    

class CollaboratorJobJoin(SQLModel, table=True):    
    __tablename__ = "collab_job_joins"
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
    

class RecruitResumeJoin(SQLModel, table=True):    
    __tablename__ = "recruit_resume_joins"
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        primary_key=True,
    )
    resume_id: Optional[int] = Field(
        default=None,
        foreign_key="resumes.id",
        primary_key=True,
    )
    package: str = Field(default=None)            #   Basic / Platinum
    is_rejected: bool = Field(default=False)      #   Recruiter rejects Resumes
    decline_reason: str = Field(default=None, sa_column=Column(TEXT))
    remain_warantty_time: int = Field(default=None)
    
    
class InterviewSchedule(SQLModel, table=True): 
    __tablename__ = "interview_schedules"
    #   Recruiter
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        primary_key=True,
    )
    #   Candidate
    candidate_id: Optional[int] = Field(
        default=None,
        foreign_key="resumes.id",
        primary_key=True,
    )
    collaborator_id: int = Field(default=None) 
    date: datetime = Field(default=None)
    location: str = Field(default=None, sa_column=Column(TEXT))
    start_time: time = Field(default=None)
    end_time: time = Field(default=None)
    note: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    
    
    
#   ==============================================================
#                           Payment
#   ==============================================================

class PointPackage(TableBase, table=True):
    __tablename__ = 'point_packages'    
    point: int = Field(default=None)
    price: float = Field(default=None)
    currency: str = Field(default=None)

    
class TransactionHistory(TableBase, table=True):    
    __tablename__ = "transaction_histories"
    user_id: int = Field(default=None, foreign_key="users.id")  #   Recruiter
    point: int =  Field(default=None)   #   package_name
    price: float = Field(default=0)
    quantity: int = Field(default=0)
    total_price: float = Field(default=0)
    transaction_form: str =  Field(default='banking')
    transaction_otp: str =  Field(default=None)

    
class DrawHistory(TableBase, table=True):    
    __tablename__ = "draw_histories"
    user_id: int = Field(default=None, foreign_key="users.id")  #   Collaborator
    point: int =  Field(default=None) 
    transaction_form: str =  Field(default='banking')
    draw_status: str = Field(default='pending')