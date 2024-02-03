
import os
import model
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from config import db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status


class BearAuthException(Exception):
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_token_payload(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')])
        payload_sub: str = payload.get("sub")
        if payload_sub is None:
            raise BearAuthException("Token could not be validated")
        return payload_sub
    except JWTError:
        raise BearAuthException("Token could not be validated")
    

def get_current_active_user(db_session: Session = Depends(db.get_session), token: str = Depends(oauth2_scheme)):
    try:
        user_email = get_token_payload(token)
    except BearAuthException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db_session.query(model.User).filter(model.User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized, could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user