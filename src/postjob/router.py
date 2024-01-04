import os
from config import db
from sqlmodel import Session
from datetime import timedelta, datetime
from starlette.requests import Request
from postjob import schema, service
from fastapi.responses import JSONResponse, RedirectResponse
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