import os
from config import db
from typing import List, Optional
from sqlmodel import Session
from fastapi import Query, UploadFile
from datetime import timedelta, datetime
from starlette.requests import Request
from postjob import schema, service
from enum import Enum
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import jwt


router = APIRouter(prefix="/postjob", tags=["Post Job"])
security_bearer = HTTPBearer()


def get_current_active_user(
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    #   Get access token
    token = credentials.credentials  
    if service.OTPRepo.check_token(db_session, token):
        raise HTTPException(status_code=401, detail="Authentication is required!")
    
    #   Decode
    payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=os.environ.get("ALGORITHM"))
    email = payload.get("sub")
        
    current_user = service.AuthRequestRepository.get_user_by_email(db_session, email)
    if not current_user:
        raise HTTPException(status_code=404, detail="Account doesn't exist!")
    
    return token, current_user


# ===========================================================
#                       Company register
# ===========================================================

@router.post("/collaborator/add-company-info",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_company_info(request: Request,
                     db_session: Session = Depends(db.get_session),
                     data_form: schema.CompanyBase = Depends(schema.CompanyBase.as_form),
                     credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.add_company(request, db_session, data_form, current_user)
    return schema.CustomResponse(
                    message="Add company information successfully",
                    data={
                        "company_id": info.id,
                        "company_name": info.company_name,
                        "company_size": info.company_size
                    }
    )


@router.get("/collaborator/get-company-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CompanyInfo)
def get_company_info(db_session: Session = Depends(db.get_session),
                     credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.get_company(db_session, current_user)
    if not info:
        raise HTTPException(status_code=404, detail="Company not found!")
    return schema.CompanyInfo(
                    company_name=info.company_name,
                    logo=info.logo,
                    description=info.description,
                    cover_image=info.cover_image,
                    # company_images=info.company_images#,
                    company_video=info.company_video,
                    industry=info.industry,
                    phone=info.phone,
                    email=info.email,
                    founded_year=info.founded_year,
                    company_size=info.company_size,
                    tax_code=info.tax_code,
                    address=info.address,
                    city=info.city,
                    country=info.country,
                    linkedin=info.linkedin,
                    website=info.website,
                    facebook=info.facebook,
                    instagram=info.instagram,
    )

@router.put("/collaborator/update-company-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_company_info(request: Request,
                     db_session: Session = Depends(db.get_session),
                     data_form: schema.CompanyUpdate = Depends(schema.CompanyUpdate.as_form),
                     credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.update_company(request, db_session, data_form, current_user)
    return schema.CustomResponse(
                    message="Update company information successfully",
                    data={
                        "company_id": info.id,
                        "company_name": info.company_name,
                        "company_size": info.company_size
                    }
    )

#   =================== Abundant API ===================
@router.post("/collaborator/add-industry",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_industry(
            industry_name: str,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.add_industry(industry_name, db_session, current_user)
    return schema.CustomResponse(
                    message="Add industries information successfully",
                    data={info.name}
    )


@router.get("/collaborator/list-industry",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_industry(db_session: Session = Depends(db.get_session)):

    info = service.Company.list_industry(db_session)
    return schema.CustomResponse(
                    message=None,
                    data=[industry for industry in info]
            )


# ===========================================================
#                       NTD post Job
# ===========================================================

@router.post("/collaborator/upload-jd",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(
        request: Request,
        uploaded_file: UploadFile,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    _ = service.Job.upload_jd(request,uploaded_file, db_session, current_user)
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data=None
    )


@router.put("/collaborator/upload-jd-again",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(
        request: Request,
        uploaded_file: UploadFile,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    _ = service.Job.upload_jd_again(request,uploaded_file, db_session, current_user)
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data=None
    )


@router.post("/collaborator/jd-parsing",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def jd_parsing(
        job_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    extracted_result, saved_path = service.Job.jd_parsing(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Extract JD successfully!",
                    data={
                        "extracted_result": extracted_result,
                        "json_saved_path": saved_path
                    }
    )


@router.put("/collaborator/fill-extracted-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def fill_parsed_job(data: schema.JobUpdate,
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Job.fill_job(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Fill-in job information successfully",
                    data=None
                )

@router.put("/collaborator/update-job-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_job_info(data: schema.JobUpdate,
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Job.update_job(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Update job information successfully",
                    data=None
                )

@router.put("/collaborator/create-job-draft",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def create_job_draft(
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Job.create_draft(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Update job information successfully",
                    data=None
                )
    
@router.get("/collaborator/list-job/{is_draft}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_created_job(
                is_draft: bool,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Job.list_job(is_draft, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    
@router.get("/collaborator/get-detail-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_job(
        job_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)
    ):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Job.get_job(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
