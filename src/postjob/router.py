import os, math, json
import shutil
from config import db
from typing import List, Any
from typing import Optional
from sqlmodel import Session
from fastapi import UploadFile, Form, File
from starlette.requests import Request
from postjob import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import jwt


router = APIRouter(prefix="/postjob", tags=["Post Job"])
security_bearer = HTTPBearer()

# ===========================================================
#                           Company
# ===========================================================

@router.post("/recruiter/add-company-info",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_company_info(request: Request,
                     data_form: schema.CompanyBase = Depends(schema.CompanyBase.as_form),
                     db_session: Session = Depends(db.get_session),
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
             response_model=schema.CustomResponse)
def get_company_info(request: Request,
                     db_session: Session = Depends(db.get_session),
                     credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.get_company(db_session, current_user)
    if not info:
        raise HTTPException(status_code=404, detail="Company not found!")
    return schema.CustomResponse(
                        message="Get company information successfully!",
                        data={
                            "company_id": info.id,
                            "company_name": info.company_name,
                            "logo": os.path.join(str(request.base_url), info.logo),
                            "description": info.description,
                            "cover_image": os.path.join(str(request.base_url) + info.cover_image),
                            "company_images": [os.path.join(str(request.base_url) + company_image) for company_image in info.company_images] if info.company_images else None,
                            "company_video": os.path.join(str(request.base_url)+ info.company_video) if info.company_video else None,
                            "industry": info.industry,
                            "phone": info.phone,
                            "email": info.email,
                            "founded_year": info.founded_year,
                            "company_size": info.company_size,
                            "tax_code": info.tax_code,
                            "address": info.address,
                            "city": info.city,
                            "country": info.country,
                            "linkedin": info.linkedin,
                            "website": info.website,
                            "facebook": info.facebook,
                            "instagram": info.instagram
                        }
    )


@router.put("/recruiter/update-company-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_company_info(
                    data_form: schema.CompanyUpdate = Depends(schema.CompanyUpdate.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.update_company(db_session, data_form, current_user)
    return schema.CustomResponse(
                    message="Update company information successfully",
                    data={
                        "company_id": info.id,
                        "company_name": info.company_name,
                        "company_size": info.company_size
                    }
    )


@router.get("/recruiter/list-city",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_city():
    info = service.Company.list_city()
    return schema.CustomResponse(
                    message=None,
                    data=[industry for industry in info]
            )

@router.get("/recruiter/list-country",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_country():
    info = service.Company.list_country()
    return schema.CustomResponse(
                    message=None,
                    data=[industry for industry in info]
            )


@router.get("/recruiter/list-industry",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_industry():
    info = service.Company.list_industry()
    return schema.CustomResponse(
                    message="Get list industries successfully.",
                    data=[industry for industry in info]
            )


# ===========================================================
#                       NTD post Job
# ===========================================================

@router.post("/recruiter/upload-jd",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(
        uploaded_file: UploadFile,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    job_db = service.Recruiter.Job.upload_jd(uploaded_file, db_session, current_user)
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data={
                        "job_id": job_db.id
                    }
    )


@router.put("/recruiter/upload-jd-again",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd_again(
        job_id: int,
        uploaded_file: UploadFile,
        db_session: Session = Depends(db.get_session)):

    result = service.Recruiter.Job.upload_jd_again(job_id, uploaded_file, db_session)
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data={
                        "job_id": result.id
                    }
    )


@router.post("/recruiter/jd-parsing",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def jd_parsing(
        job_id: int,
        db_session: Session = Depends(db.get_session)):

    extracted_result, saved_path = service.Recruiter.Job.jd_parsing(job_id, db_session)
    return schema.CustomResponse(
                    message="Extract JD successfully!",
                    data=extracted_result
                )


@router.put("/recruiter/fill-extracted-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def fill_parsed_job(data: schema.JobUpdate,
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Job.fill_job(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Fill-in job information successfully",
                    data=None
                )


@router.put("/recruiter/update-job-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_job_info(data: schema.JobUpdate,
                    db_session: Session = Depends(db.get_session)):

    service.Recruiter.Job.update_job(data, db_session)
    return schema.CustomResponse(
                    message="Update job information successfully",
                    data=None
                )

@router.put("/recruiter/update-job-draft",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def update_job_draft(
                job_id: int,
                is_draft: bool,
                db_session: Session = Depends(db.get_session)):

    service.Recruiter.Job.create_draft(job_id, is_draft, db_session)
    return schema.CustomResponse(
                    message="Create job drate successfully",
                    data=None
                )
    
@router.get("/recruiter/list-job/{is_draft}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_created_job(
                is_draft: bool,
                page_index: int,
                limit: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Job.list_created_job(is_draft, db_session, current_user)

    total_items = len(jobs)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                    message=None,
                    data={
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "item_lst": jobs[(page_index-1)*limit: (page_index-1)*limit + limit]
                    }
            )
    
    
@router.get("/recruiter/get-detailed-job/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_job(
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Job.get_detail_job(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    
    
@router.get("/recruiter/get-detail-candidate/{candidate_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_candidate(
                candidate_id: int,  # cv_id
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Resume.get_detail_candidate(candidate_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    

@router.post("/recruiter/reject-resume",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def reject_resume(
                cv_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.reject_resume(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume has been rejected.",
                    data=None
                )
    

@router.delete("/recruiter/remove-rejected-resume",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def remove_rejected_resume(
                cv_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.remove_rejected_resume(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume has been restored.",
                    data=None
                )
    

@router.post("/recruiter/add-cart",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_cart(
        cv_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.add_cart(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Add resume to cart successfully.",
                    data=None
                )
    
    
@router.get("/recruiter/list-candidate/{state}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_candidate(
                state: schema.CandidateState,
                db_session: Session = Depends(db.get_session)):
    result = service.Recruiter.Resume.list_candidate(state, db_session)
    return schema.CustomResponse(
                    message=None,
                    data=result
            )
    

@router.post("/recruiter/choose-resume",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def choose_resume(
        cv_id: int,
        package: schema.ResumePackage,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.choose_resume_package(cv_id, package, db_session, current_user)
    return schema.CustomResponse(
                    message=f"Package {package} has been choosen for this Resume.",
                    data={
                        "resume_id": cv_id,
                        "package": package  
                    }
                )


@router.post("/recruiter/cv-parsing",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def cv_parsing(
        cv_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    extracted_result, saved_path = service.Collaborator.Resume.cv_parsing(cv_id, db_session, current_user)

    return schema.CustomResponse(
                    message="Extract CV successfully!",
                    data={
                        "extracted_result": extracted_result,
                        "json_saved_path": saved_path
                    }
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

    jobs = service.Admin.Job.list_job_status(status, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    

@router.get("/admin/get-detailed-job/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_job(
            job_id: int,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Admin.Job.get_detail_job_status(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )


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
    save_dir = service.Admin.Job.save_temp_edit(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Edit job information successfully",
                    data=save_dir
                )
    
    
#   Admin approved/reject Job
@router.post("/admin/review-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def review_job(
        job_id: int,
        is_approved: bool,
        decline_reason: Optional[str] = Form(None),
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Admin.Job.review_job(job_id, decline_reason, is_approved, db_session, current_user)
    return schema.CustomResponse(
                    message="Job approved" if is_approved==True else "Job rejected",
                    data=result.is_admin_approved
            )
    
    
#   Admin remove Job
@router.delete("/admin/remove-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def remove_job(
        job_id: int,
        db_session: Session = Depends(db.get_session)):

    service.Admin.Job.remove_job(job_id, db_session)
    return schema.CustomResponse(
                    message="Remove job successfully!!!",
                    data=None
            )


@router.get("/admin/get-matching-result",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def collaborator_get_matching_result(
        cv_id: int,
        job_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    matching_result = service.Admin.Resume.get_matching_result(cv_id, job_id, db_session, current_user)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume_id": cv_id,
                        "match data": matching_result
                    }
    )
    
    
#   Admin approved/reject AI's matching results
@router.put("/admin/review-matching",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def admin_review_matching(
        cv_id: int,
        resume_status: schema.AdminReviewMatching, 
        decline_reason: Optional[str] = Form(None),
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Admin.Resume.admin_review_matching(cv_id, resume_status, decline_reason, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume matching approved" if resume_status==schema.AdminReviewMatching.admin_matching_approved else "Resume matching rejected",
                    data={
                        "resume_id": cv_id,
                        "status": resume_status,
                        "decline_reason": decline_reason
                    }
            )
    
    
# ===========================================================
#                       CTV uploads Resumes
# ===========================================================
    
@router.get("/collaborator/list-job/{job_status}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_job(
        page_index: int,
        limit: int,
        job_status: schema.CollaborateJobStatus,
        db_session: Session = Depends(db.get_session)):

    results = service.Collaborator.Job.list_job(job_status, db_session)    

    #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="Get list job successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )


@router.get("/collaborator/get-detail-job/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_job(
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Collaborator.Job.get_detail_job(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    
@router.put("/collaborator/add-favorite",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def add_favorite(
            job_id: int,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Collaborator.Job.add_favorite(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Job has been added to your favorites list",
                    data=None
            )
    
@router.get("/collaborator/get-general-info/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_general_info(
                job_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Company.get_general_info(job_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )


#   Add preliminary information to the table
@router.post("/collaborator/add-candidate",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_candidate(
        data_form: schema.AddCandidate = Depends(schema.AddCandidate.as_form),
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Collaborator.Resume.add_candidate(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Add candidate successfully",
                    data=result
    )


@router.put("/collaborator/upload-avatar",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_avatar(
        data: schema.UploadAvatar = Depends(schema.UploadAvatar.as_form),
        db_session: Session = Depends(db.get_session)):

    _ = service.Collaborator.Resume.upload_avatar(data, db_session)
    return schema.CustomResponse(
                    message="Uploaded candidate avatar successfully",
                    data=None
    )


#   Get information filled from User => Check duplicate (by email & phone) => Save to DB 
@router.put("/collaborator/fill-extracted-resume",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def fill_extracted_resume(data: schema.ResumeUpdate,
                    db_session: Session = Depends(db.get_session)):
    service.Collaborator.Resume.fill_resume(data, db_session)
    #   Resume valuation
    result = service.Collaborator.Resume.resume_valuate(data, db_session)
    return schema.CustomResponse(
                    message="Re-fill resume successfully",
                    data=result     #   Front-end will use this result to show temporarily to User 
                )


@router.post("/collaborator/resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary="============== This is an abundant API ==============")
def resume_valuate(
                data: schema.ResumeUpdate,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Collaborator.Resume.resume_valuate(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume valuated successfully",
                    data=result
                )
    

#    Admin press "Send CV" => Save resume valuation to DB
@router.post("/collaborator/confirm-resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def confirm_resume_valuate(
                cv_id: int,
                data: schema.ResumeValuateResult,
                db_session: Session = Depends(db.get_session)):

    result = service.Collaborator.Resume.confirm_resume_valuate(cv_id, data, db_session)
    return schema.CustomResponse(
                    message="Your resume has been sent!!!",
                    data={
                        "resume_id": result.cv_id,
                        "hard_item": result.hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certs": [str(cert) for cert in result.certificates],
                        "certs_point": result.certificates_point,
                        "total_point": result.total_point
            }
                )


@router.get("/collaborator/get-resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_resume_valuate(
                    cv_id: int,
                    db_session: Session = Depends(db.get_session)):

    result = service.Collaborator.Resume.get_resume_valuate(cv_id, db_session)
    
    def parse_dict(data):
        pairs = data.split()
        # Initialize an empty dictionary to store the key-value pairs
        certificate_dict = {}
        for pair in pairs:
            print(pair)
            print(type(pair))
            key, value = pair.split('=')
            # Remove single quotes from the value
            value = value.strip("'")
            certificate_dict[key] = value
        return certificate_dict
    return schema.CustomResponse(
                    message="Get resume valuation successfully",
                    data={
                        "cv_id": cv_id,
                        "hard_item": result.hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certificates": [parse_dict(cert_dict) for cert_dict in result.certificates],
                        "certificates_point": result.certificates_point,
                        "total_point": result.total_point
                    }
                )


@router.put("/collaborator/update-resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def update_resume_valuate(
                    data: schema.UpdateResumeValuation,
                    db_session: Session = Depends(db.get_session)):

    result = service.Collaborator.Resume.update_valuate(data, db_session)
    return schema.CustomResponse(
                    message="Resume re-valuated successfully",
                    data={
                        "resume_id": result.cv_id,
                        "hard_item": result.hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certificates": result.certificates,
                        "certificates_point": result.certificates_point,
                        "total_point": result.total_point
                    }
                )


@router.put("/collaborate/update-resume-draft",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def update_resume_draft(
                cv_id: int,
                is_draft: bool,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Collaborator.Resume.update_draft(cv_id, is_draft, db_session, current_user)
    return schema.CustomResponse(
                    message="Create resume draft successfully",
                    data=None
                )


@router.post("/collaborator/resume-matching",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def resume_matching(
        cv_id: int,
        background_task: BackgroundTasks,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    matching_result, saved_dir, cv_id = service.Collaborator.Resume.cv_jd_matching(cv_id, db_session, current_user, background_task)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume id": cv_id,
                        "match data": {
                            "job_title": {
                                    "score": matching_result["job_title"]["score"],
                                    "explanation": matching_result["job_title"]["explanation"]
                                },
                            "experience": {
                                    "score": matching_result["experience"]["score"],
                                    "explanation": matching_result["experience"]["explanation"]
                                },
                            "skill": {
                                    "score": matching_result["skill"]["score"],
                                    "explanation": matching_result["skill"]["explanation"]
                                },
                            "education": {
                                    "score": matching_result["education"]["score"],
                                    "explanation": matching_result["education"]["explanation"]
                                },
                            "orientation": {
                                    "score": matching_result["orientation"]["score"],
                                    "explanation": matching_result["orientation"]["explanation"]
                                },
                            "overall": {
                                    "score": matching_result["overall"]["score"],
                                    "explanation": matching_result["overall"]["explanation"]
                                }
                        }       
                    }
    )

@router.get("/collaborator/get-candidate-reply/{status}",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def resume_matching(
            cv_id: int,
            status: schema.CandidateMailReply,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Collaborator.Resume.candidate_reply(cv_id, status, db_session, current_user)
    return schema.CustomResponse(
                    message="Update candidate reply.",
                    data=None
    )
    
    
@router.get("/collaborator/get-detailed-resume/{cv_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_resume(
                cv_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    resume_info = service.Collaborator.Resume.get_detail_resume(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Get resume information successfully!",
                    data=resume_info
            )


@router.get("/collaborator/get-matching-result",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_matching_result(
        cv_id: int,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    matching_result = service.Collaborator.Resume.get_matching_result(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume_id": cv_id,
                        "match data": matching_result
                    }
    )


@router.get("/collaborator/get-list-candidate",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def list_candidate(
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Collaborator.Resume.list_candidate(db_session, current_user)
    return schema.CustomResponse(
                    message="Get list candidate successfully.",
                    data=result
    )


@router.get("/collaborator/list-draft-candidate",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def list_draft_candidate(
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.Collaborator.Resume.list_draft_candidate(db_session, current_user)
    return schema.CustomResponse(
                    message="Get list candidate successfully.",
                    data=result
    )




    
    
# ===========================================================
#                       General APIs
# ===========================================================
    
@router.get("/general/get-jd-pdf/{job_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_jd_file(request: Request,
                job_id: int,
                db_session: Session = Depends(db.get_session)):

    jd_file = service.General.get_jd_file(request, job_id, db_session)
    return schema.CustomResponse(
                    message=None,
                    data=jd_file
            )
    
    
@router.get("/general/get-cv-pdf/{cv_id}",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_cv_file(request: Request,
                cv_id: int,
                db_session: Session = Depends(db.get_session)):

    jd_file = service.General.get_cv_file(request, cv_id, db_session)
    return schema.CustomResponse(
                    message=None,
                    data=jd_file
            )