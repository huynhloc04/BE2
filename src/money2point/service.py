import model
import os, shutil, json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from config import db
from money2point import schema
from sqlmodel import Session, func, and_, or_, not_
from sqlalchemy import select
from fastapi import HTTPException, Request, BackgroundTasks, UploadFile, status
from postjob.gg_service.gg_service import GoogleService
from postjob.api_service.extraction_service import Extraction
from postjob.api_service.openai_service import OpenAIService
from postjob.db_service.db_service import DatabaseService
from config import (JD_SAVED_DIR, 
                    CV_SAVED_DIR, 
                    CV_PARSE_PROMPT, 
                    JD_PARSE_PROMPT,
                    CV_EXTRACTION_PATH,
                    JD_EXTRACTION_PATH, 
                    CANDIDATE_AVATAR_DIR,
                    SAVED_TEMP,
                    EDITED_JOB,
                    MATCHING_PROMPT,
                    MATCHING_DIR)


class General:   

    def get_userjob_by_id(job_id: int, db_session: Session, current_user):
        job_query = select(model.JobDescription).where(
                                                    model.JobDescription.user_id == current_user.id,
                                                    model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result 
            
    def get_job_by_id(job_id: int, db_session: Session):
        job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
    
    def get_detail_resumeuser_by_id(cv_id: int, db_session: Session, current_user):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.user_id == current_user.id,
                   model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
            
    def get_detail_resume_by_id(cv_id: int, db_session: Session):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    

class MoneyPoint:

    @staticmethod
    def add_point_package(data: schema.PointPackage,
                          db_session: Session):
        package_db = model.PointPackage(
                                point=data.point,
                                price=data.price,
                                currency=data.currency
        )
        db_session.add(package_db)
        db.commit_rollback(db_session)

    @staticmethod
    def add_point_cart(
                    data: schema.ChoosePackage,
                    db_session: Session,
                    current_user):
        #   Update if cart already exist
        cart_db = db_session.execute(select(model.UserPointCart).where(and_(model.UserPointCart.user_id == current_user.id,
                                                                            model.UserPointCart.package_id == data.package_id))).scalars().first()
        if cart_db:
            cart_db.quantity += data.quantity
        else:
            cart_db = model.UserPointCart(
                                    user_id=current_user.id,
                                    package_id=data.package_id,
                                    quantity=data.quantity
            )
            db_session.add(cart_db)
        db.commit_rollback(db_session)
        return cart_db


    @staticmethod
    def list_point_cart(db_session: Session, current_user):
        cart_query = select(model.UserPointCart, model.PointPackage)    \
                                .join(model.PointPackage, model.UserPointCart.package_id == model.PointPackage.id)  \
                                .filter(model.UserPointCart.user_id == current_user.id)
        results = db_session.execute(cart_query).all()
        print(results)
        return [{
            "package_id": result.UserPointCart.package_id,
            "package_name": result.PointPackage.point,
            "price": result.PointPackage.price,
            "quantity": result.UserPointCart.quantity,
            "total": result.UserPointCart.quantity * result.PointPackage.price
        } for result in results]


    @staticmethod
    def delete_point_package(package_id: int, db_session: Session, current_user):
        
        cart_db = db_session.execute(select(model.UserPointCart).where(and_(model.UserPointCart.user_id == current_user.id,
                                                                            model.UserPointCart.package_id == package_id))).scalars().first()
        if not cart_db:
            raise HTTPException(status_code=404, detail="Package not found!")
        db_session.delete(cart_db)
        db.commit_rollback(db_session)



class MoneyResume:

    @staticmethod
    def get_job_from_resume(cv_id: int, db_session: Session):
        resume = db_session.execute(select(model.Resume).where(model.Resume.id == cv_id)).scalars().first()
        job = db_session.execute(select(model.JobDescription).where(model.JobDescription.id == resume.job_id)).scalars().first()
        return job
    
    @staticmethod
    def get_package_from_resume(cv_id: int, db_session: Session, current_user):
        query = select(model.RecruitResumeJoin).where(and_(model.RecruitResumeJoin.resume_id == cv_id,
                                                           model.RecruitResumeJoin.user_id == current_user.id))
        result = db_session.execute(query).scalars().first()
        return result
    
    @staticmethod
    def get_resume_valuate(cv_id, db_session):
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This resume has not been valuated!")
        return valuate_result

    @staticmethod
    def list_resume_cart(db_session: Session, current_user):
        cart_query = select(model.UserResumeCart, model.ResumeVersion)    \
                                .join(model.ResumeVersion, model.UserResumeCart.resume_id == model.ResumeVersion.cv_id)  \
                                .filter(model.UserResumeCart.user_id == current_user.id)
        results = db_session.execute(cart_query).all()
        return [{
            "package_id": result.UserResumeCart.resume_id,
            "job_title": result.ResumeVersion.current_job,
            "industry": result.ResumeVersion.industry,
            "birthday": result.ResumeVersion.birthday,
            "job_service": MoneyResume.get_job_from_resume(result.ResumeVersion.cv_id, db_session).job_service,
            "package": MoneyResume.get_package_from_resume(result.ResumeVersion.cv_id, db_session, current_user).package,
            "resume_point": MoneyResume.get_resume_valuate(result.ResumeVersion.cv_id, db_session).total_point,
        } for result in results]