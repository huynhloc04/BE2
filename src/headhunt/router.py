import os, math, json
from config import db
from sqlmodel import Session
from fastapi import UploadFile
from starlette.requests import Request
from headhunt import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt


router = APIRouter(prefix="/headhunt", tags=["Headhunt"])
security_bearer = HTTPBearer()

# ===========================================================
#                       NTD post Job
# ===========================================================

@router.post("/recruiter/upload-jd",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def upload_jd(uploaded_file: UploadFile):

    if uploaded_file.content_type != 'application/pdf':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")

    extracted_result, _ = service.Recruiter.Job.jd_parsing(uploaded_file)
    return schema.CustomResponse(
                    message="Extract JD successfully!",
                    data=extracted_result
                )


@router.post("/recruiter/fill-extracted-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def fill_parsed_job(data: schema.FillJob = Depends(schema.FillJob.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Job.fill_job(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Fill-in job information successfully",
                    data=None
                )
    
    
@router.post("/recruiter/create-draft-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def create_draft_job(data: schema.FillDraftJob = Depends(schema.FillDraftJob.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Job.create_draft_job(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Create draft job successfully",
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
    
    
@router.get("/recruiter/get-detailed-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_job(
                job_id: int,
                request: Request,
                db_session: Session = Depends(db.get_session)):

    jobs = service.Recruiter.Job.get_detail_job(request, job_id, db_session)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )


@router.put("/recruiter/is-active-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary="NTD tạm dừng Job")
def is_active_job(data: schema.RecruitPauseJob, db_session: Session = Depends(db.get_session)):

    service.Recruiter.Job.is_active_job(data, db_session)
    return schema.CustomResponse(
                    message="Update job successfully",
                    data=None
                )
    
@router.post("/recruiter/list-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_created_job(
                data: schema.RecruitListJob,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Job.list_created_job(data.is_draft, db_session, current_user)

    total_items = len(jobs)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                    message=None,
                    data={
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "item_lst": jobs[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                    }
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
    
    
@router.post("/recruiter/get-detail-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_candidate(
                request: Request,
                data: schema.ResumeIndex,  # cv_id
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    jobs = service.Recruiter.Resume.get_detail_candidate(request, data.cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message=None,
                    data=jobs
            )
    

@router.post("/recruiter/choose-candidate",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def choose_candidate(
        data: schema.ResumeIndex,
        background_taks: BackgroundTasks,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.choose_candidate(data, background_taks, db_session, current_user)
    return schema.CustomResponse(
                    message=f"Transaction successfully!",
                    data=None
                )
    

@router.post("/recruiter/choose-interview_form/schedule-booking",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def schedule_booking(
        data: schema.InterviewBooking,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.schedule_booking(data, db_session, current_user)
    return schema.CustomResponse(
                    message=f"Transaction successfully!",
                    data=None
                )
    

@router.post("/recruiter/choose-interview_form/send-test",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def send_test(
        background_taks: BackgroundTasks,
        data: schema.TestSending = Depends(schema.TestSending.as_form),
        db_session: Session = Depends(db.get_session)):
    service.Recruiter.Resume.send_test(data, background_taks, db_session)
    return schema.CustomResponse(
                    message=f"Transaction successfully!",
                    data=None
                )
    

@router.get("/recruiter/choose-interview_form/phone",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def phone(
    cv_id: int,
    db_session: Session = Depends(db.get_session),
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    email = service.Recruiter.Resume.phone(cv_id, db_session, current_user)
    return schema.CustomResponse(
                    message="Interview via phone!",
                    data={
                        "email": email
                    }
                )
    

@router.post("/recruiter/reject-resume",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def reject_resume(
                data_form: schema.RecruitRejectResume,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.reject_resume(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume has been rejected.",
                    data=None
                )
    

@router.delete("/recruiter/remove-rejected-resume",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def remove_rejected_resume(
                data: schema.ResumeIndex,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Recruiter.Resume.remove_rejected_resume(data, db_session, current_user)
    return schema.CustomResponse(
                    message="Resume has been restored.",
                    data=None
                )


@router.get("/recruiter/get-candidate-reply-interview/{status}",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_candidate_reply_interview(
            cv_id: int,
            status: schema.CandidateMailReply,
            db_session: Session = Depends(db.get_session)):

    service.Recruiter.Resume.get_candidate_reply_interview(cv_id, status, db_session)
    return schema.CustomResponse(
                    message="Update candidate reply.",
                    data=None
    )

    
# ===========================================================
#                       CTV uploads Resumes
# ===========================================================
    
@router.post("/collaborator/list-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_job(
        request: Request,
        data: schema.CollabListJob,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    results = service.Collaborator.Job.list_job(request, data.job_status, db_session, current_user)    

    #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                        message="Get list job successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                        }
    )


@router.get("/collaborator/get-detail-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detail_job(
                job_id: int,
                request: Request, 
                db_session: Session = Depends(db.get_session)):

    jobs = service.Collaborator.Job.get_detail_job(request, job_id, db_session)
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
    
@router.get("/collaborator/get-general-info",
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
        background_task: BackgroundTasks,
        data_form: schema.AddCandidate = Depends(schema.AddCandidate.as_form),
        db_session: Session = Depends(db.get_session)):
    result = service.Collaborator.Resume.add_candidate(background_task, data_form, db_session)
    return schema.CustomResponse(
                    message="Add candidate successfully",
                    data=result
    )

#   Get information filled from User => Check duplicate (by email & phone) => Save to DB 
@router.post("/collaborator/fill-extracted-resume",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def fill_extracted_resume(
                    data_form: schema.FillResume = Depends(schema.FillResume.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    resume_db, version_db = service.Collaborator.Resume.fill_resume(data_form, db_session, current_user)
    #   Resume valuation
    valuate_result = service.Collaborator.Resume.resume_valuate(data_form, resume_db, db_session)
    return schema.CustomResponse(
                    message="Re-fill resume successfully",
                    data={
                        "cv_id": resume_db.id,
                        "valuate_result": valuate_result
                    }     #   Front-end will use this result to show valuation temporarily to User 
                )
    

@router.post("/collaborator/create-draft-resume",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def create_draft_resume(
                    data_form: schema.FillResume = Depends(schema.FillResume.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    resume_db, version_db = service.Collaborator.Resume.create_draft_resume(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Create draft resume successfully",
                    data=None #   Front-end will use this result to show valuation temporarily to User 
                )
    
    
@router.put("/collaborator/update-resume-info",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def update_resume_info(
                    data_form: schema.UpdateResume = Depends(schema.UpdateResume.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    service.Collaborator.Resume.update_resume_info(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Update resume successfully",
                    data=None 
                )
    

#   Get information filled from User => Check duplicate (by email & phone) => Save to DB 
@router.post("/collaborator/fill-extracted-resume-dummy",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def fill_extracted_resume_dummy(
                    data_form: schema.FillResume = Depends(schema.FillResume.as_form),
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    resume_db, version_db = service.Collaborator.Resume.fill_resume_dummy(data_form, db_session, current_user)
    #   Resume valuation
    valuate_result = service.Collaborator.Resume.resume_valuate_dummy(data_form, resume_db, db_session)
    return schema.CustomResponse(
                    message="Re-fill resume successfully",
                    data={
                        "cv_id": resume_db.id,
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


@router.post("/collaborator/resume-matching",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def resume_matching(
        data: schema.ResumeIndex,
        background_task: BackgroundTasks,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    matching_result, saved_dir, cv_id = service.Collaborator.Resume.cv_jd_matching(data.cv_id, db_session, background_task, current_user)
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


@router.get("/collaborator/get-candidate-reply",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_candidate_reply(
            cv_id: int,
            status: schema.CandidateMailReply,
            db_session: Session = Depends(db.get_session)):

    service.Collaborator.Resume.get_candidate_reply(cv_id, status, db_session)
    return schema.CustomResponse(
                    message="Update candidate reply.",
                    data=None
    )


@router.post("/collaborator/get-matching-result",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_matching_result(
        data: schema.ResumeIndex,
        db_session: Session = Depends(db.get_session),
        credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    matching_result = service.Collaborator.Resume.get_matching_result(data.cv_id, db_session)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume_id": data.cv_id,
                        "match_data": matching_result
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
    
    
@router.post("/collaborator/get-detail-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_candidate(
                request: Request,
                data: schema.ResumeIndex,
                db_session: Session = Depends(db.get_session)):

    resume_info = service.Collaborator.Resume.get_detail_candidate(request, data.cv_id, db_session)
    return schema.CustomResponse(
                    message="Get resume information successfully!",
                    data=resume_info
            )
    
    
@router.post("/collaborator/get-interview-schedule",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_interview_schedule(
                data: schema.ResumeIndex,
                db_session: Session = Depends(db.get_session)):

    resume_info = service.Collaborator.Resume.get_interview_schedule(data, db_session)
    return schema.CustomResponse(
                    message="Get resume information successfully!",
                    data=resume_info
            )


@router.put("/collaborator/confirm-interview",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def confirm_interview(
                    data: schema.ResumeIndex, 
                    db_session: Session = Depends(db.get_session)):  
    
    service.Collaborator.Resume.confirm_interview(data, db_session)

    return schema.CustomResponse(
                        message="Collaborator confirm interview successfully!",
                        data=None
    )


#     ======== >>> Trigger a notification to Recruiter to announce that schedule has been changed...
@router.put("/collaborator/reschedule",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def reschedule(data: schema.Reschedule, db_session: Session = Depends(db.get_session)):
    service.Collaborator.Resume.reschedule(data, db_session)

    return schema.CustomResponse(
                        message="Collaborator update schedule successfully!",
                        data=None
    )
    
# ===========================================================
#                       Admin filters Job
# ===========================================================
    
@router.post("/admin/list-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_job_status(
                request: Request,
                data: schema.AdminListJob,
                db_session: Session = Depends(db.get_session)):
    
    jobs = service.Admin.Job.list_job_status(request, data.job_status, db_session)  
    #   Pagination
    total_items = len(jobs)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                        message="Get list job successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": jobs[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                        }
    )
    

@router.get("/admin/get-detailed-job",
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
    
    
#   Admin approved/reject Job
@router.post("/admin/review-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def review_job(
        data_form: schema.AdminReviewJob,
        db_session: Session = Depends(db.get_session)):

    service.Admin.Job.review_job(data_form, db_session)
    return schema.CustomResponse(
                    message="Admin reviewed job.",
                    data={
                        "job_id": data_form.job_id,
                        "status": "Job approved" if data_form.is_approved==True else "Job rejected"
                    }
            )


@router.put("/admin/is-active-job",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary="Admin tạm dừng job")
def is_active_job(data: schema.AdminPauseJob, db_session: Session = Depends(db.get_session)):

    service.Admin.Job.is_active_job(data, db_session)
    return schema.CustomResponse(
                    message="Update job successfully",
                    data=None
                )


#   Khi admin click button: Chỉnh sửa" => Admin check/edit job information and send to NTD check (if JD not good)
@router.post("/admin/edit-job-info",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def edit_job_info(
                data: schema.JobUpdate,
                db_session: Session = Depends(db.get_session)):
    """
        1. Admin edit job temporarily, save edited version to a json file, FE load that json file and show to user (NTD)
        2. User (NTD) read/re-edit and re-send that job to Admin filter
    """
    save_dir = service.Admin.Job.save_temp_edit(data, db_session)
    return schema.CustomResponse(
                    message="Edit job information successfully",
                    data=save_dir
                )


@router.post("/admin/list-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary="Admin views resume valuation results.")
def list_candidate(
            data: schema.AdminListCandidate,
            db_session: Session = Depends(db.get_session)):

    results = service.Admin.Resume.list_candidate(data.candidate_status, db_session)

    #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/data.limit)

    return schema.CustomResponse(
                        message="Get list job successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(data.page_index-1)*data.limit: (data.page_index-1)*data.limit + data.limit]
                        }
    )
    
    
@router.post("/collaborator/get-detailed-candidate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_detailed_candidate(
                request: Request,
                data: schema.ResumeIndex,
                db_session: Session = Depends(db.get_session)):

    resume_info = service.Admin.Resume.get_detail_candidate(request, data.cv_id, db_session)
    return schema.CustomResponse(
                    message="Get resume information successfully!",
                    data=resume_info
            )


@router.post("/admin/get-matching-result",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def collaborator_get_matching_result(
        data: schema.ResumeIndex,
        db_session: Session = Depends(db.get_session)):

    matching_result = service.Admin.Resume.get_matching_result(data.cv_id, db_session)
    return schema.CustomResponse(
                    message="CV-JD matching completed.",
                    data={
                        "resume_id": data.cv_id,
                        "match_data": matching_result
                    }
    )
    
    
#   Admin approved/reject AI's matching results
@router.put("/admin/review-matching",
             status_code=status.HTTP_200_OK,
             response_model=schema.CustomResponse)
def review_matching(
        data_form: schema.AdminReviewMatching,
        db_session: Session = Depends(db.get_session)):

    service.Admin.Resume.admin_review_matching(data_form, db_session)
    return schema.CustomResponse(
                    message="Resume matching approved" if data_form.resume_status==schema.MatchedResult.admin_matching_approved else "Resume matching rejected",
                    data={
                        "resume_id": data_form.cv_id,
                        "status": data_form.resume_status,
                        "decline_reason": data_form.decline_reason
                    }
            )


@router.post("/admin/get-resume-valuate",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary="Admin views resume valuation results.")
def get_resume_valuate(
                    data: schema.ResumeIndex,
                    request: Request,
                    db_session: Session = Depends(db.get_session)):

    result = service.General.get_resume_valuate(data.cv_id, db_session)
    
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
    resume = service.General.get_detail_resume_by_id(data.cv_id, db_session)
    return schema.CustomResponse(
                    message="Get resume valuation successfully",
                    data={
                        "cv_id": data.cv_id,
                        "cv_pdf": os.path.join(str(request.base_url), resume.ResumeVersion.cv_file),
                        "hard_item": result.hard_item,
                        "hard_point": result.hard_point,
                        "degrees": result.degrees,
                        "degree_point": result.degree_point,
                        "certificates": [parse_dict(cert_dict) for cert_dict in result.certificates],
                        "certificates_point": result.certificates_point,
                        "total_point": result.total_point
                    }
                )