import os, math
import shutil
from config import db
from typing import List, Any
from typing import Optional
from sqlmodel import Session
from fastapi import UploadFile, Form, File
from starlette.requests import Request
from money2point import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import jwt


router = APIRouter(prefix="/money2point", tags=["Money to Point"])
security_bearer = HTTPBearer()

# ===========================================================
#                           Recruiter
# ===========================================================

@router.post("/recruiter/add-point-package",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_point_package(
                data_form: schema.PointPackage,
                db_session: Session = Depends(db.get_session)):

    service.MoneyPointConvert.add_point_package(data_form, db_session)
    return schema.CustomResponse(
                    message="Add point package successfully",
                    data=None
    )

@router.post("/recruiter/add-point-cart",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def add_point_cart(
                data_form: schema.ChoosePackage,
                db_session: Session = Depends(db.get_session),
                credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    result = service.MoneyPointConvert.add_point_cart(data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Add point package to cart successfully",
                    data={
                        "user_id": result.current_user.id,
                        "package_id": result.package_id,
                        "quantity": result.quantity
                    }
    )