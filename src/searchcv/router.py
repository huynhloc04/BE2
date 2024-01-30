import os
import shutil
import math
import pickle
from config import db
from typing import List, Any
from sqlmodel import Session
from fastapi import UploadFile
from starlette.requests import Request
from searchcv import schema, service
from postjob.db_service.db_service import DatabaseService
from authentication import get_current_active_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, status, Depends, Security, HTTPException
from config import JD_SAVED_DIR, CV_SAVED_DIR


router = APIRouter(prefix="/searchcv", tags=["SearchCV"])
security_bearer = HTTPBearer()


@router.post("/recruiter/basic-search",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def basic_search(
            uploaded_file: UploadFile,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    pass

#   Upload JD => JD Parsing
@router.post("/recruiter/upload-jd",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(
            uploaded_file: UploadFile,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    if uploaded_file.content_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
    
    #   Extract and save results
    cleaned_filename = DatabaseService.clean_filename(uploaded_file.filename)
    with open(os.path.join(JD_SAVED_DIR,  cleaned_filename), 'w+b') as file:
        shutil.copyfileobj(uploaded_file.file, file)    
    #   JD parsing
    _, job_db = service.Recruiter.Job.jd_parsing(uploaded_file, cleaned_filename, db_session, current_user)
    
    return schema.CustomResponse(
                    message="Uploaded JD successfully",
                    data={
                        "job_id": job_db.id
                    }
    )


#   Filter above JD with multiple CV (CV used basic_search)
@router.post("recruiter/batch-filter",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def batch_filter(
            data_form: schema.BatchFilter,
            db_session: Session = Depends(db.get_session)
):  
    good_match = []     #   Good match save resume index that matches over 50% with relevant JD
    for cv_id in data_form.cv_lst:
        #   Get Resume results
        resume_result = service.General.get_detail_resume_by_id(cv_id, db_session)
        #   Get Job results
        job_result = service.General.get_job_by_id(data_form.job_id, db_session)
        matching_result, saved_dir = service.Recruiter.Resume.matching_base(
                                                            cv_filename=resume_result.ResumeVersion.filename, 
                                                            jd_filename=job_result.jd_file.split("/")[-1])
        if matching_result["overall"]["score"] > 50:
            good_match.append(cv_id)
        #   Store matching result to DB
        service.Recruiter.Resume.save_matching_result(
                                                resume_result.Resume.cv_id,
                                                job_result.id,
                                                matching_result,
                                                db_session)
    #   Save good match results
    jd_filename = job_result.jd_file.split("/")[-1].split(".") + '.pkl'
    with open(os.path.join('static/good_match', jd_filename), 'wb') as file:
        pickle.dump(good_match, file)
        
    return schema.CustomResponse(
                    message="Filter Cv-JD successfully.",
                    data={
                        "job_id": good_match
                    }
    )


@router.post("/recruiter/list-good-match",
            status_code=status.HTTP_200_OK, 
            response_model=schema.CustomResponse)
def list_good_match(
                data_form: schema.ListGoodMatch,
                db_session: Session = Depends(db.get_session)
):
    #   Get Job results
    job_result = service.General.get_job_by_id(data_form.job_id, db_session)
    #   Load good matches
    jd_filename = job_result.jd_file.split("/")[-1].split(".")[0] + '.pkl'
    with open(os.path.join('static/good_match', jd_filename), 'rb') as file:
        good_match = pickle.load(file)
    #   Get information of each Resume
    results = service.Recruiter.Resume.list_good_match(good_match, db_session)

    total_items = len(results)
    total_pages = math.ceil(total_items/data_form.limit)

    return schema.CustomResponse(
                    message=None,
                    data={
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "item_lst": results[(data_form.page_index-1)*data_form.limit: (data_form.page_index-1)*data_form.limit + data_form.limit]
                    }
            )


@router.get("/recruiter/get-matching-result",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_matching_result(
        cv_id: int,
        db_session: Session = Depends(db.get_session)):

    matching_result = service.Recruiter.Resume.get_matching_result(cv_id, db_session)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume_id": cv_id,
                        "match_data": matching_result
                    }
    )
    
    
@router.get("/recruiter/get-detail-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_candidate(
                request: Request,
                cv_id: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Resume.get_detail_candidate(request, cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    
    
@router.post("/recruiter/list-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_candidate(
                data: schema.RecruitListCandidate,
                db_session: Session = Depends(db.get_session)):
    results = service.Recruiter.Resume.list_candidate(data.state, db_session)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                        message="Get list candidate successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                        }
    )


#   Upload JD => JD Parsing
@router.post("/collaborator/upload-cv",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_cv(
            data_form: schema.UploadResume = Depends(schema.UploadResume.as_form),
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    if data_form.cv_file.content_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
    
    #   Extract and save results
    cleaned_filename = DatabaseService.clean_filename(data_form.cv_file.filename)
    with open(os.path.join(CV_SAVED_DIR,  cleaned_filename), 'w+b') as file:
        shutil.copyfileobj(data_form.cv_file.file, file)    
    #   JD parsing
    extracted_result, version_db = service.Collaborator.Resume.cv_parsing(data_form, cleaned_filename, db_session, current_user)
    #   Resume valuation
    valuate_result = service.Collaborator.Resume.resume_valuate(version_db, db_session)   #   cv_id, session
    return schema.CustomResponse(
                    message="Uploaded resume successfully",
                    data={
                        "cv_id": version_db.cv_id,
                        "valuate_result": valuate_result
                    }     #   Front-end will use this result to show valuation temporarily to User 
                )


@router.get("/collaborator/get-resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_resume_valuate(
                    cv_id: int,
                    request: Request,
                    db_session: Session = Depends(db.get_session)):

    result = service.General.get_resume_valuate(cv_id, db_session)
    
    def parse_dict(data):
        pairs = data.split()
        # Initialize an empty dictionary to store the key-value pairs
        certificate_dict = {}
        for pair in pairs:
            key, value = pair.split('=')
            # Remove single quotes from the value
            value = value.strip("'")
            certificate_dict[key] = value
        return certificate_dict
    
    #   Get resume pdf file
    resume = service.General.get_detail_resume_by_id(cv_id, db_session)
    level_lst = [str(level) for level in schema.Level]
    hard_item = {
        "level": result.hard_item if result.hard_item in level_lst else None,
        "salary": result.hard_item if result.hard_item not in level_lst else None
    }
    return schema.CustomResponse(
                    message="Get resume valuation successfully",
                    data={
                        "cv_id": cv_id,
                        "cv_pdf": os.path.join(str(request.base_url), resume.ResumeVersion.cv_file),
                        "hard_item": hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certificates": [cert_dict for cert_dict in result.certificates],
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

    level_lst = [str(level) for level in schema.Level]
    hard_item = {
        "level": result.hard_item if result.hard_item in level_lst else None,
        "salary": result.hard_item if result.hard_item not in level_lst else None
    }
    return schema.CustomResponse(
                    message="Resume re-valuated successfully",
                    data={
                        "resume_id": result.cv_id,
                        "hard_item": hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certificates": result.certificates,
                        "certificates_point": result.certificates_point,
                        "total_point": result.total_point
                    }
                )


@router.post("/collaborator/list-candidate",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def list_candidate(
            data: schema.CollabListResume,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    results = service.Collaborator.Resume.list_candidate(data.is_draft, db_session, current_user)

    total_items = len(results)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                    message=None,
                    data={
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "item_lst": results[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                    }
            )







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