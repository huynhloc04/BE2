import os, math
import shutil
from config import db
from typing import List, Any
from typing import Optional
from sqlmodel import Session
from dotenv import load_dotenv
from fastapi import UploadFile, Form, File
from starlette.requests import Request
from money2point import schema, service
from authentication import get_current_active_user
from fastapi import APIRouter, status, Depends, BackgroundTasks, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from jose import jwt


load_dotenv()

from_date = "2024-01-01"
page = 1
page_size = 10
sort = "DESC"
api_url = os.environ.get("API_URL")
api_key_or_token = os.environ.get("API_KEY_OR_TOKEN")

curl_command = [
        "curl",
        "--location",
        "--request",
        "GET",
        f"'{api_url}?fromDate={from_date}&page={page}&pageSize={page_size}&sort={sort}'",
        "--header",
        f"'Authorization: Apikey {api_key_or_token}'"
    ]
curl_command_str = " ".join(curl_command)


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

    service.MoneyPoint.add_point_package(data_form, db_session)
    return schema.CustomResponse(
                    message="Add point package successfully",
                    data=None
    )


@router.get("/recruiter/list-point-package",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def list_point_package(db_session: Session = Depends(db.get_session)):

    results = service.MoneyPoint.list_point_package(db_session)
    return schema.CustomResponse(
                    message="List point packages successfully",
                    data=[{
                        "package_id": result.id,
                        "point": result.point,
                        "price": result.price,
                        "currency": result.currency
                    } for result in results]
    )


@router.get("/recruiter/get-point-package",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def get_point_package(
                package_id: int,
                db_session: Session = Depends(db.get_session)):

    result = service.MoneyPoint.get_point_package(package_id, db_session)
    return schema.CustomResponse(
                    message="Get point packages successfully",
                    data={
                        "package_id": result.id,
                        "point": result.point,
                        "price": result.price
                    }
    )


@router.post("/recruiter/purchase_point",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def purchase_point(
            data_form: schema.PurchasePoint,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)):    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    service.MoneyPoint.purchase_point(data_form, curl_command_str, db_session, current_user)
    return schema.CustomResponse(
                    message="Transaction successfully!",
                    data=None
    )


@router.get("/recruiter/list-history-purchase",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def list_history_purchase(
                    limit: int,
                    page_index: int,
                    db_session: Session = Depends(db.get_session),
                    credentials: HTTPAuthorizationCredentials = Security(security_bearer)):    
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)

    results = service.MoneyPoint.list_history_purchase(db_session, current_user)

    total_items = len(results)
    total_pages = math.ceil(total_items/limit)

    return schema.CustomResponse(
                    message=None,
                    data={
                        "total_items": total_items,
                        "total_pages": total_pages,
                        "item_lst": results[(page_index-1)*limit: (page_index-1)*limit + limit]
                    }
            )













# @router.delete("/recruiter/delete-point-package",
#              status_code=status.HTTP_201_CREATED, 
#              response_model=schema.CustomResponse)
# def delete_point_package(
#                 package_id: int,
#                 db_session: Session = Depends(db.get_session),
#                 credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
#     # Get curent active user
#     _, current_user = get_current_active_user(db_session, credentials)

#     result = service.MoneyPoint.delete_point_package(package_id, db_session, current_user)
#     return schema.CustomResponse(
#                     message="Delete package successfully",
#                     data=result
#     )

# @router.post("/recruiter/add-point-cart",
#              status_code=status.HTTP_201_CREATED, 
#              response_model=schema.CustomResponse)
# def add_point_cart(
#                 data_form: schema.ChoosePackage,
#                 db_session: Session = Depends(db.get_session),
#                 credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
#     # Get curent active user
#     _, current_user = get_current_active_user(db_session, credentials)

#     result = service.MoneyPoint.add_point_cart(data_form, db_session, current_user)
#     return schema.CustomResponse(
#                     message="Add point package to cart successfully",
#                     data={
#                         "user_id": result.user_id,
#                         "package_id": result.package_id,
#                         "quantity": result.quantity
#                     }
#     )

# @router.get("/recruiter/list-point-cart",
#              status_code=status.HTTP_201_CREATED, 
#              response_model=schema.CustomResponse)
# def list_point_cart(
#                 db_session: Session = Depends(db.get_session),
#                 credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
#     # Get curent active user
#     _, current_user = get_current_active_user(db_session, credentials)

#     result = service.MoneyPoint.list_point_cart(db_session, current_user)
#     return schema.CustomResponse(
#                     message="List point packages successfully",
#                     data=result
#     )


# @router.get("/recruiter/list-resume-cart",
#              status_code=status.HTTP_201_CREATED, 
#              response_model=schema.CustomResponse)
# def list_resume_cart(
#                 db_session: Session = Depends(db.get_session),
#                 credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    
#     # Get curent active user
#     _, current_user = get_current_active_user(db_session, credentials)

#     result = service.MoneyResume.list_resume_cart(db_session, current_user)
#     return schema.CustomResponse(
#                     message="List resume carts successfully",
#                     data=result
#     )