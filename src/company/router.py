import os
from config import db
from sqlmodel import Session
from starlette.requests import Request
from company import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/company", tags=["Company"])
security_bearer = HTTPBearer()

# ===========================================================
#                           Company
# ===========================================================

@router.post("/add-company-info",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_company_info(
                data_form: schema.CompanyBase = Depends(schema.CompanyBase.as_form),
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.Company.add_company(db_session, data_form, current_user)
    return schema.CustomResponse(
                    message="Add company information successfully",
                    data={
                        "company_id": info.id,
                        "company_name": info.company_name,
                        "company_size": info.company_size
                    }
    )


@router.get("/get-company-info",
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
                            "cover_image": os.path.join(str(request.base_url), info.cover_image) if info.cover_image else None,
                            "company_images": [os.path.join(str(request.base_url), company_image) for company_image in info.company_images] if info.company_images else None,
                            "company_video": os.path.join(str(request.base_url), info.company_video) if info.company_video else None,
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


@router.put("/update-company-info",
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


@router.get("/check-company-exist",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse,
             summary='Check to see if recruiter have registered company information')
def check_company_exist(
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    is_exist = service.Company.check_company_exist(db_session, current_user)
    return schema.CustomResponse(
                    message="You have registered company information" if is_exist else "You have not registered coommpany information",
                    data={
                        "is_exist": is_exist
                    }
    )


@router.get("/list-city",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_city():
    info = service.Company.list_city()
    return schema.CustomResponse(
                    message=None,
                    data=[industry for industry in info]
            )

@router.get("/list-country",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_country():
    info = service.Company.list_country()
    return schema.CustomResponse(
                    message=None,
                    data=[industry for industry in info]
            )


@router.get("/list-industry",
             status_code=status.HTTP_200_OK, 
             response_model=schema.CustomResponse)
def list_industry():
    info = service.Company.list_industry()
    return schema.CustomResponse(
                    message="Get list industries successfully.",
                    data=[industry for industry in info]
    )

@router.post("/add-bank-info",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_bank_info(
                data_form: schema.BankBase,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.Bank.add_bank_info(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Add bank information successfully",
                    data=None
    )