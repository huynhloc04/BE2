import os
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Security
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from datetime import timedelta, datetime
from pydantic import EmailStr
from fastapi.security import HTTPBearer
from sqlmodel import Session
from config import db
from auth import schema, service, security
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import JWTError, jwt

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/sign-up", 
            status_code=status.HTTP_201_CREATED, 
            response_model=schema.SignUpResponse)
def sign_up(background_tasks: BackgroundTasks,
            db_session: Session = Depends(db.get_session),
            data: schema.SignUp = Depends(schema.SignUp.as_form)):
    #   Check wheather this user is exist?
    user = service.AuthRequestRepository.get_user_by_email(db_session, data.email)
    if user:
        return JSONResponse(status_code=409,
                            content={
                                "message": "Account already exist!",
                                "data": None,
                                "errorCode": 4006,
                                "errors": None})
    
    #   Hash password
    hashed_password = security.get_password_hash(password=data.password)
    #   Write information to database
    try:
        user = service.AuthRequestRepository.add_user(
                                                db_session,
                                                fullname=data.fullname,
                                                email=data.email,
                                                phone=data.phone,
                                                role=data.role)
        otp = security.random_otp(6)
        background_tasks.add_task(service.AuthRequestRepository.OTP_GOOGLE, otp=otp, input_email=user.email)

        user.password = hashed_password
        user.last_signed_in = datetime.now()
        user.otp_token = otp
        db.commit_rollback(db_session)

    except Exception as error:
        return JSONResponse(status_code=503,
                            content={
                                "message": "Error accounting when creating your account.",
                                "data": None,
                                "errorCode": 4006,
                                "errors": None})

    return schema.SignUpResponse(
                            user_id= user.id,
                            email=user.email,
                            role=user.role)


@router.put("/resend-otp", 
            status_code=status.HTTP_200_OK, 
            response_model=schema.SignUpResponse)
def resend_otp(
            background_tasks: BackgroundTasks,
            user_id: int,
            db_session: Session = Depends(db.get_session)):
    user = service.AuthRequestRepository.get_user_by_id(db_session, user_id)
    if user.is_verify == True:
        return JSONResponse(status_code=403,
                            content={
                                "message": "Account is already active",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
    try:
        new_otp = security.random_otp(6)
        #   Send OTP to specified email
        background_tasks.add_task(service.AuthRequestRepository.OTP_GOOGLE, otp=new_otp, input_email=user.email)
        #   Update with the lastest OTP code
        user.otp_token = new_otp
        db.commit_rollback(db_session)
        
        return JSONResponse(status_code=200,
                            content={
                                "message": "OTP sent!",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
    except Exception:
        return JSONResponse(status_code=503,
                            content={
                                "message": "Error occurs when sending OTP.",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
    
    
@router.post("/verify-otp")
async def verify_otp(
                db_session: Session = Depends(db.get_session),
                data_form: schema.VerifyOTP = Depends(schema.VerifyOTP.as_form)):

    if not service.OTPRepo.check_otp(
                            db_session,
                            user_id=data_form.user_id,
                            otp=data_form.received_otp):
        return JSONResponse(status_code=404,
                            content={
                                "mesage": "Bad request",
                                "data": None,
                                "errorCode": None,
                                "errors": "Xac thuc OTP that bai",
                                })
    
    user = service.AuthRequestRepository.get_user_by_id(db_session, data_form.user_id)
    if not user:
        return JSONResponse(status_code=404,
                            content={
                                "mesage": "Bad request",
                                "data": None,
                                "errorCode": None,
                                "errors": "Khong ton tai nguoi dung"})
    #   Update user status
    user.is_verify = True
    db.commit_rollback(db_session)
    #   Disable OTP
    service.OTPRepo.disable_otp(db_session, data_form.received_otp)
    
    # access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    # access_token = auth_service.create_access_token(
    #     data={"sub": user.email}, expires_delta=access_token_expires)
    # refresh_token = auth_service.create_refresh_token(
    #     data={"sub": user.email}, expires_delta=refresh_token_expires)
    # user.refresh_token = refresh_token
    # commit_rollback()
    return JSONResponse(
                status_code=201,
                content={
                    "message": "User verify successfully!",
                    "data": None,
                    "errorCode": None,
                    "errors": None})


@router.post("/log-in")
def login_for_access_token(
                data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db_session: Session = Depends(db.get_session)):
    user = service.AuthRequestRepository.authenticate_user(db_session, data.username, data.password)
    if not user:
        return JSONResponse(
                    status_code=401,
                    content={
                        "message": "Access Denied",
                        "data": None,
                        "errorCode": 2001,
                        "errors": None})
   
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires)
    user.refresh_token = refresh_token
    db.commit_rollback(db_session)
    return JSONResponse(
                content={
                    "message": "Dang nhap thanh cong",
                    "data": {
                        "role": user.role,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": 'Bearer',
                        "token_key": 'Authorization'
                        },
                    "errorCode": None,
                    "errors": None})


@router.post('/logout')
def logout(credentials: HTTPAuthorizationCredentials = Security(security),
           db_session: Session = Depends(db.get_session)):
    #   Get access token
    token = credentials.credentials    
    if service.JWTRepo.check_token(db_session, token):
        return JSONResponse(status_code=401,
                            content={
                                "message": "Yeu cau xac thuc!!!",
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
    service.OTPRepo.add_to_blacklist(db_session, token)
    #   Delete refresh token of the current_user => successfully logout
    current_user.refresh_token = None
    db.commit_rollback(db_session)
    return JSONResponse(status_code=200,
                        content={
                            "message": "Dang xuat thành công!",
                            "data": None,
                            "errorCode": None,
                            "errors": None})