import os, math
from config import db
from sqlmodel import Session
from fastapi import UploadFile
from starlette.requests import Request
from general import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/general", tags=["General"])
security_bearer = HTTPBearer()
    

#   ============================================================
#                          Recruiter
#   ============================================================

@router.get("/recruiter/list-interview-schedule",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_interview_schedule(
                limit: int, 
                page_index: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    results = service.Recruiter.Resume.list_interview_schedule(db_session, current_user)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="List interview schedule successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    
@router.get("/recruiter/transaction-history",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def transaction_history(
                limit: int, 
                page_index: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    user_point, results = service.Recruiter.Resume.transaction_history(db_session, current_user)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="Get list transaction history successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "wallet_point": user_point,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    

#   ============================================================
#                          Collaborator
#   ============================================================
    
@router.get("/collaborator/list-interview-schedule",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_interview_schedule(
                limit: int, 
                page_index: int,
                request: Request,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    results = service.Collaborator.Resume.list_interview_schedule(request, db_session, current_user)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="List interview schedule successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    
@router.get("/collaborator/referral-histrory",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def referral_histrory(
                limit: int, 
                page_index: int,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    results = service.Collaborator.Resume.referral_history(db_session, current_user)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="Get referral history successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "current_wallet_point": current_user.point,
                            "max_drawed_point": current_user.point - current_user.warranty_point,
                            "warranty_point": current_user.warranty_point,
                            "referral_list": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    
@router.post("/collaborator/require-draw-point",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def draw_point(
            data_form: schema.DrawMoney,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    service.Collaborator.Resume.require_draw_point(data_form, db_session, current_user)

    return schema.CustomResponse(
                        message="Draw point-money successfully!",
                        data=None
    )
    
    
@router.get("/collaborator/list-draw-history",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def draw_history(
            page_index: int,
            limit: int,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    results = service.Collaborator.Resume.draw_history(db_session, current_user)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="List draw money history successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )    
    

#   ============================================================
#                          Admin
#   ============================================================
    
@router.get("/admin/list-interview-schedule",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_interview_schedule(
                limit: int, 
                page_index: int,
                request: Request,
                db_session: Session = Depends(db.get_session)):
    results = service.Admin.Resume.list_interview_schedule(request, db_session)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)
    return schema.CustomResponse(
                        message="List interview schedule successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
@router.get("/admin/purchase-point-history",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def purchase_point_history(
                limit: int, 
                page_index: int,
                request: Request,
                db_session: Session = Depends(db.get_session)):
    results = service.Admin.Resume.purchase_point_history(request, db_session)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)
    return schema.CustomResponse(
                        message="Get list transaction successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    
@router.get("/admin/list-required-draw-history",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def required_draw_history(
            page_index: int,
            limit: int,
            db_session: Session = Depends(db.get_session)):
    results = service.Admin.Resume.required_draw_history(db_session)
     #   Pagination
    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                        message="List draw money history successfully!",
                        data={
                            "total_items": total_items,
                            "total_pages": total_pages,
                            "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                        }
    )
    
    
@router.post("/get-resume-status",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def get_resume_status(
                data: schema.ResumeIndex,
                db_session: Session = Depends(db.get_session)):
    status = service.General.get_resume_status(data, db_session)
    return schema.CustomResponse(
                    message="Get resume status successfully.",
                    data={
                        "status": status
                    }
            )
    
    
@router.get("/get-jd-pdf",
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
    
    
@router.get("/get-cv-pdf",
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