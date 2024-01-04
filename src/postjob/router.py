import os
from config import db
from typing import Annotated
from sqlmodel import Session
from datetime import timedelta, datetime
from starlette.requests import Request
from fastapi_sso.sso.google import GoogleSSO
from postjob import schema, service
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
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
        return JSONResponse(status_code=401,
                            content={
                                "message": "Authentication is required!!!",
                                "data": None,
                                "errorCode": 1002,
                                "errors": None})
    #   Decode
    payload = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms=os.environ.get("ALGORITHM"))
    email = payload.get("sub")
        
    current_user = service.AuthRequestRepository.get_user_by_email(db_session, email)
    if not current_user:
        return JSONResponse(
                            status_code=404,
                            content={
                                "message": "Account doesn't exist!!!",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
    return token, current_user


@router.post("/collaborate/add-company-info")
def add_company_info(request: Request,
                     db_session: Session = Depends(db.get_session),
                     data_form: schema.CompanyBase = Depends(schema.CompanyBase.as_form),
                     credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    info = service.add_company(request, db_session, data_form, current_user)
    return JSONResponse(status_code=201,
                        content={
                            "message": "Add Company information successfully!",
                            "data": {
                                "company_id": info.id
                                },
                            "errorCode": None,
                            "errors": None})