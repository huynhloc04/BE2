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



class MoneyPointConvert:

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
    def add_point_to_cart(data: schema.ChoosePackage,
                          db_session: Session,
                          current_user):
        cart_db = model.UserPointCart(
                                user_id=current_user.id,
                                package_id=data.package_id,
                                quantity=data.quantity
        )
        db_session.add(cart_db)
        db.commit_rollback(db_session)
