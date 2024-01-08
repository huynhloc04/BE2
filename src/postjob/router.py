import os
from config import db
from typing import List, Optional
from sqlmodel import Session
from fastapi import Query, UploadFile, Form
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

@router.post("/recruiter/add-company-info",
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


@router.get("/recruiter/get-company-info",
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

@router.put("/recruiter/update-company-info",
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
@router.post("/recruiter/add-industry",
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


@router.get("/recruiter/list-industry",
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

@router.post("/recruiter/upload-jd",
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


@router.put("/recruiter/upload-jd-again/{job_id}",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(
        job_id: int,
        request: Request,
        uploaded_file: UploadFile,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    _ = service.Job.upload_jd_again(job_id, request, uploaded_file, db_session, current_user)
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data=None
    )


@router.post("/recruiter/jd-parsing",
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


@router.put("/recruiter/fill-extracted-job",
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

@router.put("/recruiter/update-job-info",
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

@router.put("/recruiter/create-job-draft/{job_id}",
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
    
@router.get("/recruiter/list-job/{is_draft}",
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
    
    
@router.get("/recruiter/get-detailed-job/{status}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_job_(
                status: schema.JobStatus,
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Job.get_job_status(status, job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )


@router.put("/recruiter/update-job-status/{status}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_job_status(job_id: int,
                    status: schema.JobStatus,
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Job.update_job_status(job_id, status, db_session, current_user)
    
    return schema.CustomResponse(
                    message="JD status changed.",
                    data={
                        "job_id": result.id,
                        "status": result.status}
                )
    
@router.get("/recruiter/get-jd-pdf/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_jd_file(
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jd_file = service.Job.get_jd_file(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jd_file
            )
    
    
# ===========================================================
#                       Admin filters Job
# ===========================================================
    
@router.get("/admin/list-job/{status}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_job_status(
                status: schema.JobStatus,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Job.list_job_status(status, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    

@router.get("/admin/get-detailed-job/{status}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_job(
            status: schema.JobStatus,
            job_id: int,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    return get_detailed_job_(status, job_id, db_session, credentials)


#   Khi admin click button: Chỉnh sửa" => Admin check/edit job information and send to NTD check (if JD not good)
@router.post("/admin/edit-job-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def edit_job_info(
                data: schema.JobUpdate,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    #   1. Admin edit job temporarily, save edited version to a json file, FE load that json file and show to user (NTD)
    #   2. User (NTD) read/re-edit and re-send that job to Admin filter
    save_dir = service.Job.save_temp_edit(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Edit job information successfully",
                    data=save_dir
                )
    
    
#   Admin approved/reject Job
@router.post("/admin/filter-job/{job_id}/{is_approved}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def filter_job(
        job_id: int,
        is_approved: bool,
        decline_reason: Optional[str] = Form(None),
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Job.filter_job(job_id, decline_reason, is_approved, db_session, current_user)
    return schema.CustomResponse(
                    message="Job approved" if is_approved==True else "Job rejected",
                    data=result.is_admin_approved
            )
    
    
@router.get("/admin/get-jd-pdf/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def admin_get_jd_file(
            job_id: int,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    return get_jd_file(job_id, db_session, credentials)
    
    
#   Admin remove Job
@router.delete("/admin/remove-job/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def remove_job(
        job_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Job.remove_job(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Remove job successfully!!!",
                    data=None
            )
    
    
# ===========================================================
#                       CTV uploads Resumes
# ===========================================================