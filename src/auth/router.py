import os
from config import db
from typing import Annotated
from sqlmodel import Session
from datetime import timedelta, datetime
from starlette.requests import Request
from fastapi_sso.sso.google import GoogleSSO
from auth import schema, service, security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import jwt

SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "default_session_cookie_name")
GOOGLE_CLIENT_ID =  os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET =  os.getenv("GOOGLE_CLIENT_SECRET")

google_sso = GoogleSSO(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET, 
    "http://localhost:6060/auth/callback",
    allow_insecure_http=True
)

router = APIRouter(prefix="/auth", tags=["Account"])
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


@router.post("/sign-up", 
            status_code=status.HTTP_201_CREATED, 
            response_model=schema.SignUpResponse)
def sign_up(background_tasks: BackgroundTasks,
            data: schema.SignUp,
            db_session: Session = Depends(db.get_session)):
    #   Check wheather this user is exist?
    user = service.AuthRequestRepository.get_user_by_email(db_session, data.email)
    if user:
        raise HTTPException(status_code=409, detail="Account already exists!")
    
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
        print(error)

    return schema.SignUpResponse(
                            user_id= user.id,
                            email=user.email,
                            role=user.role)


@router.put("/resend-otp", 
            status_code=status.HTTP_200_OK, 
            response_model=schema.SignUpResponse)
def resend_otp(
        user_id: int,
        background_tasks: BackgroundTasks,
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
                data_form: schema.VerifyOTP,
                db_session: Session = Depends(db.get_session)):

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
    service.OTPRepo.disable_otp(db_session, data_form)
    return JSONResponse(
                status_code=201,
                content={
                    "message": "User verify successfully!",
                    "data": None,
                    "errorCode": None,
                    "errors": None})


@router.post("/login",
            status_code=status.HTTP_200_OK, 
            response_model=schema.LoginForm)
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
    #    Set cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(SESSION_COOKIE_NAME, access_token)
    return schema.LoginForm(
                role=user.role,
                access_token=access_token,
                refresh_token=refresh_token
            )
    
    

@router.get("/google-login")
async def google_login():
    with google_sso:
        return await google_sso.get_login_redirect(params={"prompt": "consent", "access_type": "offline"})


@router.get("/callback",
            status_code=status.HTTP_200_OK, 
            response_model=schema.LoginForm)
async def google_callback(
                request: Request,
                db_session: Session = Depends(db.get_session)):
    """Process login response from Google and return user info"""

    try:
        with google_sso:
            user = await google_sso.verify_and_process(request)
        #   Check weathear user is already exist in Database???
        user_stored = service.AuthRequestRepository.get_user_by_email(db_session, user.email)
        if not user_stored:
            user_stored = service.AuthRequestRepository.add_user(
                                                db_session,
                                                fullname=user.display_name,
                                                email=user.email)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
                    data={"sub": user_stored.email}, expires_delta=access_token_expires)
        #   Set cookie with access token
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(SESSION_COOKIE_NAME, access_token)
        return schema.LoginForm(
                    access_token=access_token
                )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")
        

@router.post('/logout')
def logout(db_session: Session = Depends(db.get_session),
           credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    access_token, current_user = get_current_active_user(db_session, credentials)
    
    service.OTPRepo.add_to_blacklist(db_session, access_token)
    #   Delete refresh token of the current_user => successfully logout
    current_user.refresh_token = None
    db.commit_rollback(db_session)
    
    #   Delete cookie
    try:
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return JSONResponse(status_code=200,
                            content={
                                "message": "Logout successfully!",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")
    

@router.put('/change-password')
def change_password(
                data: schema.ChangePassword,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)): 
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    
    # Xác nhận lại mật khẩu cũ (old_password)
    if not service.AuthRequestRepository.authenticate_user(db_session,
                                                           email=current_user.email,
                                                           password=data.old_password):
        return JSONResponse(status_code=401,
                            content={"detail":"Current password is not correct.",
                                     "data": None,
                                     "metadata": None, 
                                     "status_code": 401})
    
    # Cập nhật mật khẩu mới
    new_hashed_password = security.get_password_hash(data.new_password)
    service.AuthRequestRepository.update_password(db_session,
                                                  current_user,
                                                  hashed_password=new_hashed_password)
        
    return JSONResponse(status_code=201,
                        content={
                            "message": "Change password successfully!",
                            "data": None,
                            "errorCode": None,
                            "errors": None})
    
    
@router.get("/get-current-user-info", 
            summary="Get information of the existing user",
            status_code=status.HTTP_200_OK, 
            response_model=schema.UserInfo
            )
def get_current_user(
              db_session: Session = Depends(db.get_session),
              credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    
    if not current_user:
        return JSONResponse(status_code=404,
                            content={
                                "message": "Acccount doesn't exist.",
                                "data": None,
                                "errorCode": None,
                                "errors": None})
        
    return schema.UserInfo(
                    fullname=current_user.fullname,
                    email=current_user.email,
                    phone=current_user.phone
    )


@router.put("/update-current-user-info",
            status_code=status.HTTP_200_OK, 
            response_model=schema.UserInfo)
def upate_user_info(
                data_form: schema.UserInfo,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)
    
    #   Update user info
    if data_form.fullname:
        current_user.fullname = data_form.fullname
    if data_form.email:
        current_user.email = data_form.email
    if data_form.phone:
        current_user.phone = data_form.phone
    db.commit_rollback(db_session)
        
    return schema.UserInfo(
                    fullname=current_user.fullname,
                    email=current_user.email,
                    phone=current_user.phone
            )
    
@router.post("/add-admin-member",
            status_code=status.HTTP_201_CREATED, 
            response_model=schema.AdminMember)
def add_admin_member(
                data_form: schema.MemberBase,
                db_session: Session = Depends(db.get_session)): 
    
    member = service.AuthRequestRepository.add_admin(db_session, data_form)
    return schema.AdminMember(
                    fullname=member.fullname,
                    email=member.email,
                    password=member.password,
            )
    

@router.get("/list-admin-member",
            status_code=status.HTTP_200_OK)
def list_admin_member(db_session: Session = Depends(db.get_session)):
    results = service.AuthRequestRepository.list_admin(db_session)    
    response = {
        "message": None,
        "data": [{
            "member_id": result.id,
            "name": result.fullname,
            "role": result.role
            } for result in results] if results else None,
        "errorCode": None,
        "errors": None
    }
    return response


@router.delete("/remove-admin-member")
def remove_admin_member(member_id: int,
                        db_session: Session = Depends(db.get_session)):
    result = service.AuthRequestRepository.remove_member(db_session, member_id) 
    return JSONResponse(status_code=200,
                        content={
                            "message": "Remove member successfully!",
                            "data": {
                                "member_id": result.id    
                            },
                            "errorCode": None,
                            "errors": None})