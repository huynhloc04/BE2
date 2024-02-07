import os, math
import model
from config import db
from authentication import get_current_active_user
from sqlmodel import Session
from fastapi.requests import Request
from money2point import schema, service
from fastapi import APIRouter, status, Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES


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
    

@router.post("/recruiter/purchase-point",
             status_code=status.HTTP_201_CREATED, 
             response_model=schema.CustomResponse)
def purchase_point(
            request: Request,
            data_form: schema.PurchasePoint,
            db_session: Session = Depends(db.get_session),
            credentials: HTTPAuthorizationCredentials = Security(security_bearer)): 
    # Get curent active user
    _, current_user = get_current_active_user(db_session, credentials)    
    result = service.MoneyPoint.purchase_point(request, data_form, db_session, current_user)
    return schema.CustomResponse(
                    message="Get payment information successfully!",
                    data=result
    )
    
    
@router.post('/recruiter/make-transaction')
def make_transaction(data: dict, db_session: Session = Depends(db.get_session)):
    error = data.get('error', 0)
    if error != 0:
        return
    transactions = data.get('data', [])

    service.MoneyPoint.make_transaction(transactions, db_session)
    return schema.CustomResponse(
                    message="Transaction successfully!",
                    data=None
    )