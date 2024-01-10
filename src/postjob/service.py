import model
from fastapi import HTTPException, Request
from sqlalchemy import select
from fastapi import UploadFile, status, Depends
import os, shutil
import pandas as pd
import json
from typing import Dict, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from config import db
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
from postjob import schema
from sqlmodel import Session, func
from postjob.api_service.extraction_service import Extraction
from postjob.api_service.openai_service import OpenAIService
from postjob.db_service.db_service import DatabaseService


class AuthRequestRepository:
    @staticmethod
    def get_user_by_email(db_session: Session, email: str):
        query = select(model.User).where(model.User.email == email)
        result = db_session.execute(query).scalars().first()
        return result

    @staticmethod
    def get_user_by_id(db_session: Session, user_id: int):
        query = select(model.User).where(model.User.id == user_id)
        result = db_session.execute(query).scalars().first()
        return result


class OTPRepo:
    @staticmethod
    def check_otp(
            db_session: Session,
            user_id: int, 
            otp: str):
        query = select(model.User).where(
                                    model.User.id==user_id,
                                    model.User.otp_token == otp)
        result = db_session.execute(query).scalars().first()
        if result:
            return True
        return False
        
    @staticmethod
    def check_token(db_session: Session, token: str):
        token = (db_session.execute(select(model.JWTModel).where(model.JWTModel.token == token))).scalar_one_or_none()
        if token:
            return True
        return False


class Company:

    @staticmethod
    def add_company(request: Request,
                    db_session: Session,
                    data: schema.CompanyBase,
                    current_user):
        db_company = model.Company(
                                user_id=current_user.id,
                                company_name=data.company_name, 
                                industry=data.industry, 
                                description=data.description, 
                                tax_code=data.tax_code, 
                                phone=data.phone, 
                                email=data.email, 
                                founded_year=data.founded_year, 
                                company_size=data.company_size, 
                                address=data.address, 
                                city=data.city, 
                                country=data.country, 
                                logo=str(request.base_url) + data.logo.filename if data.logo else None,
                                cover_image=str(request.base_url) + data.cover_image.filename if data.cover_image else None, 
                                # company_images=[str(request.base_url) + company_img.filename for company_img in data.company_images] if data.company_images else None,
                                company_video=str(request.base_url) + data.company_video.filename if data.company_video else None,
                                linkedin=data.linkedin,
                                website=data.website,
                                facebook=data.facebook,
                                instagram=data.instagram)
        db_session.add(db_company)
        db.commit_rollback(db_session)

        #   Save file
        companies = ["logo", "cover_image", "company_video"]
        for folder in companies:
            dir = os.path.join(os.getenv("COMPANY_DIR"), folder)
            if not os.path.exists(dir):
                os.makedirs(dir)
        if data.logo:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "logo",  data.logo.filename), 'w+b') as file:
                shutil.copyfileobj(data.logo.file, file)
        if data.cover_image:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "cover_image",  data.cover_image.filename), 'w+b') as file:
                shutil.copyfileobj(data.cover_image.file, file)
        if data.company_video:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "company_video",  data.company_video.filename), 'w+b') as file:
                shutil.copyfileobj(data.company_video.file, file)
        return db_company
    
    
    @staticmethod
    def get_company(db_session: Session, user):
        query = select(model.Company).where(model.Company.user_id == user.id)
        results = db_session.execute(query).scalars().first()
        return results
    

    @staticmethod
    def get_general_company_info(job_id, db_session, user):
        #   Company
        company_query = select(model.Company).where(model.Company.user_id == user.id)
        company_result = db_session.execute(company_query).scalars().first() 
        if not company_result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")
        #   Job
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                       model.JobDescription.id == job_id,
                                                       model.JobDescription.status == status)
        job_result = db_session.execute(job_query).scalars().first() 
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        return {
            #   Company
            "logo": company_result.logo,
            "company_name": company_result.company_name,
            "industry": company_result.industry,
            #   Job
            "status": job_result.status,
            "job_service": job_result.job_service,
            "job_title": job_result.job_title,
            "company_size": job_result.company_size,
            "founded_year": job_result.founded_year,
            "tax_code": job_result.tax_code,
            "address": job_result.address,
            "city": job_result.city,
            "country": job_result.country
        }
    

    @staticmethod
    def update_company(
                    request: Request,
                    db_session: Session,
                    data: schema.CompanyUpdate,
                    user):
    
        #   Get the current blog
        query = select(model.Company).where(model.Company.user_id == user.id)
        result = db_session.execute(query).scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")

        #   Update whether product is a feature product?  
        
        for key, value in dict(data).items():
            if value is not None and (key != "logo" or key != "cover_image" or key != "company_images" or key != "company_video"):
                setattr(result, key, value)
        if data.logo:
            result.logo = str(request.base_url) + data.logo.filename
        if data.cover_image:
            result.cover_image = str(request.base_url) + data.cover_image.filename
        # if data.company_images:
        #     result.company_images = [str(request.base_url) + company_img.filename for company_img in data.company_images]
        if data.company_video:
            result.company_video = str(request.base_url) + data.company_video.filename
            
        db.commit_rollback(db_session)    
        return result
    
    @staticmethod
    def add_industry(industry_names, db_session, user):
        db_industry = model.Industry(
                    user_id=user.id,
                    name=industry_names
        )
        db_session.add(db_industry)
        db.commit_rollback(db_session)
        return db_industry
    
    
    @staticmethod
    def list_city():
        cities = [
            "Hà Nội", "Hồ Chí Minh", "An Giang", "Bà Rịa - Vũng Tàu", "Bạc Liêu", "Bắc Giang", "Bắc Kạn", "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau", "Cần Thơ", "Cao Bằng", "Đà Nẵng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc", "Yên Bái" 
        ]
        return cities
    
    
    @staticmethod
    def list_country():
        cities = [
            "Mỹ (US)", "Trung Quốc (CN)", "Ấn Độ (IN)", "Brazil (BR)", "Nga (RU)", "Nhật Bản (JP)", "Đức (DE)", "Anh (GB)", "Pháp (FR)", "Úc (AU)", "Canada (CA)", "Đan Mạch (DK)", "Hà Lan (NL)", "Bỉ (BE)", "Thụy Sĩ (CH)", "Thụy Điển (SE)", "Ý (IT)", "Tây Ban Nha (ES)", "Đức (DE)", "Pháp (FR)", "Hàn Quốc (KR)", "Singapore (SG)", "Malaysia (MY)", "Thái Lan (TH)", "Indonesia (ID)", "Úc (AU)", "New Zealand (NZ)", "Nigeria (NG)", "Nam Phi (ZA)", "Kenya (KE)", "Ghana (GH)", "Ethiopia (ET)", "Mexico (MX)", "Brazil (BR)", "Argentina (AR)", "Colombia (CO)", "Chile (CL)", "Saudi Arabia (SA)", "Israel (IL)", "Thổ Nhĩ Kỳ (TR)", "Iran (IR)"
        ]
        return cities
    
    
    @staticmethod
    def list_industry(db_session: Session):
        results = db_session.execute(select(model.Industry.name)).scalars().all()
        return results
    

class Job:
    
    def get_job_by_id(job_id: int, db_session: Session, current_user):
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == current_user.id,
                                                        model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
    

    @staticmethod
    def upload_jd(request: Request, 
                  uploaded_file: UploadFile, 
                  db_session: Session, 
                  user):
        if uploaded_file.content_type != 'application/pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
        
        cleaned_filename = DatabaseService.clean_filename(uploaded_file.filename)
        db_job = model.JobDescription(
                    user_id=user.id,
                    jd_file=str(request.base_url) + cleaned_filename 
        )
        db_session.add(db_job)
        db.commit_rollback(db_session)

        #   Save JD file
        with open(os.path.join(JD_SAVED_DIR,  cleaned_filename), 'w+b') as file:
            shutil.copyfileobj(uploaded_file.file, file)
    

    @staticmethod
    def upload_jd_again(job_id: int,
                        request: Request, 
                        uploaded_file: UploadFile, 
                        db_session: Session, 
                        user):
        if uploaded_file.content_type != 'application/pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
        
        query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                   model.JobDescription.id == job_id)
        result = db_session.execute(query).scalars().first()
        
        #   Update other JD file
        cleaned_filename = Job.clean_filename(uploaded_file.filename)
        result.jd_file = str(request.base_url) + cleaned_filename 
        db.commit_rollback(db_session)

        #   Save JD file
        with open(os.path.join(JD_SAVED_DIR,  cleaned_filename), 'w+b') as file:
            shutil.copyfileobj(uploaded_file.file, file)


    @staticmethod
    def jd_parsing(job_id: int, db_session: Session, user):
        result = Job.get_job_by_id(job_id, db_session, user)       
        if not result.jd_file:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload at least 1 JD_PDF")

        filename = result.jd_file.split("/")[-1]
        #   Check duplicated filename
        if not DatabaseService.check_file_duplicate(filename, JD_EXTRACTION_PATH):
            prompt_template = Extraction.jd_parsing_template(filename)

            #   Read parsig requirements
            with open(JD_PARSE_PROMPT, "r") as file:
                require = file.read()
            prompt_template += require 
            
            #   Start parsing
            extracted_result = OpenAIService.gpt_api(prompt_template)
            
            #   Save extracted result
            saved_path = DatabaseService.store_jd_extraction(extracted_json=extracted_result, jd_file=filename)
        else:
            #   Read available extracted result
            saved_path = os.path.join(JD_EXTRACTION_PATH, filename.split(".")[0] + ".json")
            with open(saved_path) as file:
                extracted_result = file.read()
        return extracted_result, saved_path
        
        
    @staticmethod
    def fill_job(data_form: schema.JobUpdate,
                 db_session: Session,
                 user):
        result = Job.get_job_by_id(data_form.job_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")   
        
        for key, value in dict(data_form).items():
            if key != "job_id" and value is not None:
                if (key != "education" and key != "language_certificates" and key != "other_certificates"):
                    setattr(result, key, value)  
        
        if data_form.education:
            job_edus = [model.JobEducation(job_id=data_form.job_id,
                                        **dict(education)) for education in data_form.education]
            db_session.add_all(job_edus)
        if data_form.language_certificates:
            lang_certs = [model.LanguageCertificate(job_id=data_form.job_id,
                                                **dict(lang_cert)) for lang_cert in data_form.language_certificates]
            db_session.add_all(lang_certs)
        if data_form.other_certificates:
            other_certs = [model.OtherCertificate(job_id=data_form.job_id,
                                                **dict(other_cert)) for other_cert in data_form.other_certificates]
            db_session.add_all(other_certs)
            
        db.commit_rollback(db_session) 
        
        
    @staticmethod
    def update_job(data_form: schema.JobUpdate,
                 db_session: Session,
                 user):
        result = Job.get_job_by_id(data_form.job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        for key, value in dict(data_form).items():
            if key != "job_id":
                if value is not None and (key != "education" and key != "language_certificates" and key != "other_certificates"):
                    setattr(result, key, value) 
                    
        
        #   Delete all old information and add new ones    (Methoods to delete multiple rows in one Table)      
        db_session.execute(model.JobEducation.__table__.delete().where(model.JobEducation.job_id == data_form.job_id)) 
        db_session.execute(model.LanguageCertificate.__table__.delete().where(model.LanguageCertificate.job_id == data_form.job_id)) 
        db_session.execute(model.OtherCertificate.__table__.delete().where(model.OtherCertificate.job_id == data_form.job_id)) 
        
        #   Add new Job information as an Update
        job_edus = [model.JobEducation(job_id=data_form.job_id,
                                      **dict(education)) for education in data_form.education]
        lang_certs = [model.LanguageCertificate(job_id=data_form.job_id,
                                              **dict(lang_cert)) for lang_cert in data_form.language_certificates]
        other_certs = [model.OtherCertificate(job_id=data_form.job_id,
                                             **dict(other_cert)) for other_cert in data_form.other_certificates]
            
        db_session.add_all(job_edus)
        db_session.add_all(lang_certs)
        db_session.add_all(other_certs)
        db.commit_rollback(db_session) 
        
        
    @staticmethod
    def create_draft(job_id: int, db_session: Session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        #   Create draft
        result.is_draft = True
        db.commit_rollback(db_session) 
        
        
    @staticmethod
    def list_job(is_draft, db_session, user):
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                        model.JobDescription.is_draft == is_draft)
        results = db_session.execute(job_query).scalars().all() 
        if not results:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        query = select(func.count(model.ResumeNew.job_id))  \
                                        .where(model.ResumeNew.job_id == model.JobDescription.id)
        cv_count = db_session.execute(query).scalar()
        
        if is_draft:
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngành nghề": result.industries,
                "Loại dịch vụ": result.job_service,
                "Ngày tạo": result.created_at
            } for result in results]
            
        else:
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngày đăng tuyển": result.created_at,
                "Loại dịch vụ": result.job_service,
                "Trạng thái": result.status,
                "CVs": cv_count
            } for result in results]
        
        
    @staticmethod
    def get_job_status(status, job_id, db_session, user):
        #   Company
        company_query = select(model.Company).where(model.Company.user_id == user.id)
        company_result = db_session.execute(company_query).scalars().first() 
        if not company_result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")
        #   Job
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                       model.JobDescription.id == job_id,
                                                       model.JobDescription.status == status)
        job_result = db_session.execute(job_query).scalars().first() 
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")

        job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
        lang_certs = db_session.execute(select(model.LanguageCertificate).where(model.LanguageCertificate.job_id == job_id)).scalars().all()
        other_certs = db_session.execute(select(model.OtherCertificate).where(model.OtherCertificate.job_id == job_id)).scalars().all()
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        if status==schema.JobStatus.pending or status==schema.JobStatus.browsing:
            return {
                "status": job_result.status,
                "job_title": job_result.job_title,
                "industry": job_result.industries,
                "gender": job_result.gender,
                "job_type": job_result.job_type,
                "skills": job_result.skills,
                "received_job_time": job_result.received_job_time,
                "working_time": job_result.working_time,
                "description": job_result.description,
                "requirement": job_result.requirement,
                "benefits": job_result.benefits,
                "levels": job_result.levels,
                "roles": job_result.roles,
                "yoe": job_result.yoe,
                "num_recruit": job_result.num_recruit,
                "education": [{
                    "degree": edu.degree,
                    "major": edu.major,
                    "gpa": edu.gpa,
                } for edu in job_edus],
                "language_certificate": [{
                    "language": lang_cert.language,
                    "certificate_name": lang_cert.language_certificate_name,
                    "certificate_level": lang_cert.language_certificate_level,
                } for lang_cert in lang_certs],
                "other_certificate": [{
                    "certificate_name": cert.certificate_name,
                    "certificate_level": cert.certificate_level,
                } for cert in other_certs],
                "min_salary": job_result.min_salary,
                "max_salary": job_result.max_salary,                
                "address": job_result.address,
                "city": job_result.city,
                "country": job_result.country,
                "admin_decline_reason": job_result.admin_decline_reason 
            }
        else:
            return {
                #   Company
                "logo": company_result.logo,
                "company_name": company_result.company_name,
                "industry": company_result.industry,
                #   Job
                "status": job_result.status,
                "job_service": job_result.job_service,
                "job_title": job_result.job_title,
                "address": job_result.address,
                "city": job_result.city,
                "country": job_result.country,
                "job_type": job_result.job_type,
                "description": job_result.description,
                "requirement": job_result.requirement,
                "benefits": job_result.benefits,
                "skills": job_result.skills,
                "education": [{
                    "degree": edu.degree,
                    "major": edu.major,
                    "gpa": edu.gpa,
                } for edu in job_edus],
                "language_certificate": [{
                    "language": lang_cert.language,
                    "certificate_name": lang_cert.language_certificate_name,
                    "certificate_level": lang_cert.language_certificate_level,
                } for lang_cert in lang_certs],
                "other_certificate": [{
                    "certificate_name": cert.certificate_name,
                    "certificate_level": cert.certificate_level,
                } for cert in other_certs],
                "min_salary": job_result.min_salary,
                "max_salary": job_result.max_salary,
                "received_job_time": job_result.received_job_time,
                "working_time": job_result.working_time,
                "levels": job_result.levels,
                "roles": job_result.roles,
                "yoe": job_result.yoe,
                "num_recruit": job_result.num_recruit
            }
        
        
    @staticmethod
    def update_job_status(job_id, status, db_session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        
        #   Update status
        result.status = status
        db.commit_rollback(db_session)
        return result
    
        
    @staticmethod
    def get_jd_file(job_id, db_session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        
        #   Return link to JD PDF file 
        return result.jd_file
    
    
    
    
    # ===========================================================
    #                       Admin filters Job
    # ===========================================================        
        
    @staticmethod
    def list_job_status(status, db_session, user):
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                        model.JobDescription.status == status)
        results = db_session.execute(job_query).scalars().all() 
        if not results:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        query = select(func.count(model.ResumeNew.job_id))  \
                                        .where(model.ResumeNew.job_id == model.JobDescription.id)
        cv_count = db_session.execute(query).scalar()
        
        if status == schema.JobStatus.pending or status == schema.JobStatus.browsing:   #  Chờ duyệt - Đang duyệt
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngày tạo": result.created_at,
                "Ngành nghề": result.industries,
                "Loại dịch vụ": result.job_service
            } for result in results]
            
        else:       #  Đang tủyển - Đã tủyển
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngày đăng tuyển": result.created_at,
                "Loại dịch vụ": result.job_service,
                "CVs": cv_count
            } for result in results]
            
        
    @staticmethod
    def save_temp_edit(data: int, db_session: Session, user):
        result = Job.get_job_by_id(data.job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        #   Save edited information as a parquet JSON file
        try:
            df = pd.DataFrame(json.loads(data.json()))
            table = pa.Table.from_pandas(df)
            save_dir = os.path.join(EDITED_JOB, f'{result.jd_file.split("/")[-1][:-4]}.parquet')
            pq.write_table(table, save_dir)
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This edit could not be saved")
        
        # Update Job status: 
        result.status = schema.JobStatus.browsing
        db.commit_rollback(db_session)
        
    
    @staticmethod
    def filter_job(job_id, decline_reason, is_approved, db_session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        
        #   Admin duyet Job
        result.is_admin_approved = is_approved
        #   Update Job status
        if is_approved:
            result.status = schema.JobStatus.recruiting   # Đang tuyển
        elif not is_approved:
            result.status = schema.JobStatus.browsing      # Đang duyệt
            result.admin_decline_reason = decline_reason
        db.commit_rollback(db_session)
        return result
        
    
    @staticmethod
    def remove_job(job_id, db_session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        
        #   Admin remove Job
        db_session.delete(result)
        db.commit_rollback(db_session)
    
    
    # ===========================================================
    #                       CTV uploads Resumes
    # =========================================================== 

        
        
    @staticmethod
    def ctv_get_job_status(status, job_id, db_session, user):
        #   Company
        company_query = select(model.Company).where(model.Company.user_id == user.id)
        company_result = db_session.execute(company_query).scalars().first() 
        if not company_result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")
        #   Job
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                       model.JobDescription.id == job_id,
                                                       model.JobDescription.status == status)
        job_result = db_session.execute(job_query).scalars().first() 
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")

        job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
        lang_certs = db_session.execute(select(model.LanguageCertificate).where(model.LanguageCertificate.job_id == job_id)).scalars().all()
        other_certs = db_session.execute(select(model.OtherCertificate).where(model.OtherCertificate.job_id == job_id)).scalars().all()
        
        return {
            #   Company
            "logo": company_result.logo,
            "company_name": company_result.company_name,
            "industry": company_result.industry,
            #   Job
            "status": job_result.status,
            "job_service": job_result.job_service,
            "job_title": job_result.job_title,
            "address": job_result.address,
            "city": job_result.city,
            "country": job_result.country,
            "job_type": job_result.job_type,
            "description": job_result.description,
            "requirement": job_result.requirement,
            "benefits": job_result.benefits,
            "skills": job_result.skills,
            "education": [{
                "degree": edu.degree,
                "major": edu.major,
                "gpa": edu.gpa,
            } for edu in job_edus],
            "language_certificate": [{
                "language": lang_cert.language,
                "certificate_name": lang_cert.language_certificate_name,
                "certificate_level": lang_cert.language_certificate_level,
            } for lang_cert in lang_certs],
            "other_certificate": [{
                "certificate_name": cert.certificate_name,
                "certificate_level": cert.certificate_level,
            } for cert in other_certs],
            "min_salary": job_result.min_salary,
            "max_salary": job_result.max_salary,
            "received_job_time": job_result.received_job_time,
            "working_time": job_result.working_time,
            "levels": job_result.levels,
            "roles": job_result.roles,
            "yoe": job_result.yoe,
            "num_recruit": job_result.num_recruit
        }
        
    @staticmethod
    def add_favorite(job_id, db_session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        

        result.is_favorite = True
        db.commit_rollback(db_session)        
        return result.jd_file



class Resume:    
    
    def get_detail_resume_by_id(cv_id: int, db_session: Session, current_user):
        cv_query = select(model.ResumeNew, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.new_id == cv_id) \
            .filter(model.ResumeNew.user_id == current_user.id,
                   model.ResumeNew.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    def get_resume_by_id(cv_id: int, db_session: Session, current_user):
        query = select(model.ResumeNew).where(model.ResumeNew.user_id == current_user.id,
                                                model.ResumeNew.id == cv_id)
        result = db_session.execute(query).first() 
        return result
    
    
    @staticmethod
    def parse_base(filename: str, check_dup: bool = False):
        #   Check duplicated filename
        if not DatabaseService.check_file_duplicate(filename, CV_EXTRACTION_PATH):
            prompt_template = Extraction.cv_parsing_template(filename, check_dup)

            #   Read parsing requirements
            with open(CV_PARSE_PROMPT, "r") as file:
                require = file.read()
            prompt_template += require 
            
            #   Start parsing
            extracted_result = OpenAIService.gpt_api(prompt_template)        
            saved_path = DatabaseService.store_cv_extraction(extracted_json=extracted_result, cv_file=filename)
        else:
            #   Read available extracted result
            saved_path = os.path.join(CV_EXTRACTION_PATH, filename.split(".")[0] + ".json")
            with open(saved_path) as file:
                extracted_result = json.loads(file.read())
        return extracted_result, saved_path
    

    @staticmethod
    def add_candidate(request, data, db_session, user):
        #   PDF uploaded file validation        
        if data.cv_pdf.content_type != 'application/pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file") 
        cleaned_filename = DatabaseService.clean_filename(data.cv_pdf.filename)

        #   Save CV file as temporary
        with open(os.path.join(SAVED_TEMP, cleaned_filename), 'w+b') as file:
            shutil.copyfileobj(data.cv_pdf.file, file)
            
        extracted_result, _ = Resume.parse_base(cleaned_filename, check_dup=True)
        #   Check duplicated CVs
        DatabaseService.check_db_duplicate(extracted_result["contact_information"], cleaned_filename, db_session)
        #   Save Resume's basic info to DB
        shutil.move(os.path.join(SAVED_TEMP, cleaned_filename), os.path.join(CV_SAVED_DIR, cleaned_filename))
        db_resume = model.ResumeNew(
                            user_id=user.id,
                            job_id=data.job_id,
                        )       
        db_session.add(db_resume)
        db.commit_rollback(db_session)
        db_version = model.ResumeVersion(
                            new_id=db_resume.id,
                            filename=cleaned_filename,
                            cv_file=str(request.base_url) + cleaned_filename,
                            level=extracted_result["levels"][0],
                            email=extracted_result["contact_information"]["email"][0],
                            phone=extracted_result["contact_information"]["phone"][0]
                        )
        db_session.add(db_version)
        db.commit_rollback(db_session)


    @staticmethod
    def cv_parsing(cv_id: int, db_session: Session, user):
        result = Resume.get_detail_resume_by_id(cv_id, db_session, user)       
        if not result.ResumeVersion.filename:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload at least 1 CV_PDF")
        return Resume.parse_base(result.ResumeVersion.filename)
    

    @staticmethod
    def upload_avatar(request: Request,
                      data: schema.UploadAvatar, 
                      db_session: Session,
                      user):
        
        cleaned_filename = DatabaseService.clean_filename(data.avatar.filename)
        
        result = Resume.get_detail_resume_by_id(data.cv_id, db_session, user) 
        result.ResumeVersion.avatar = str(request.base_url) + cleaned_filename
        db.commit_rollback(db_session)

        #   Save logo image
        with open(os.path.join(CANDIDATE_AVATAR_DIR,  cleaned_filename), 'w+b') as file:
            shutil.copyfileobj(data.avatar.file, file)
        
        
    @staticmethod
    def fill_resume(data_form: schema.ResumeUpdate,
                    db_session: Session,
                    user):
        result = Resume.get_detail_resume_by_id(data_form.new_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")   

        #   If the resume never existed in System => add to Database
        for key, value in dict(data_form).items():
            if key != "new_id" and key != "level":
                if value is not None and key not in ["education",
                                                     "work_experiences",
                                                     "awards",
                                                     "projects",
                                                     "language_certificates",
                                                     "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
        if data_form.education:
            edus = [model.ResumeEducation(cv_id=data_form.new_id,
                                              **dict(education)) for education in data_form.education]
            db_session.add_all(edus)
        if data_form.work_experiences:
            expers = [model.ResumeExperience(cv_id=data_form.new_id,
                                            **dict(exper)) for exper in data_form.work_experiences]
            db_session.add_all(expers)
        if data_form.awards:
            awards = [model.ResumeAward(cv_id=data_form.new_id,
                                        **dict(award)) for award in data_form.awards]
            db_session.add_all(awards)
        if data_form.projects:
            projects = [model.ResumeAward(cv_id=data_form.new_id,
                                        **dict(project)) for project in data_form.projects]
            db_session.add_all(projects)
        if data_form.language_certificates:
            lang_certs = [model.ResumeAward(cv_id=data_form.new_id,
                                        **dict(lang_cert)) for lang_cert in data_form.language_certificates]
            db_session.add_all(lang_certs)
        if data_form.other_certificates:
            other_certs = [model.ResumeAward(cv_id=data_form.new_id,
                                        **dict(other_cert)) for other_cert in data_form.other_certificates]
            db_session.add_all(other_certs)
            
        db.commit_rollback(db_session) 


    @staticmethod
    def percent_estimate(filename: str):
        prompt_template = Extraction.resume_percent_estimate(filename)      
        #   Start parsing
        extracted_result = OpenAIService.gpt_api(prompt_template)
        point, explain = extracted_result["point"], extracted_result["explanation"]
        print("-------------------------------------------")
        print(point)
        print(explain)
        return point/100, explain

    
    @staticmethod
    def valuate_base(db_resume: model.ResumeVersion,
                     data: Optional[schema.ResumeValuation]) -> List[float]:
        
        #   Point initialization
        hard_point = 0
        soft_point = 0
        
        #   ================================== Hard points ==================================
        levels = [["Executive", "Senior", "Engineer", "Developer"], 
                  ["Leader", "Supervisor", "Senior Leader", "Senior Supervisor", "Assitant Manager"], 
                  ["Manager", "Senior Manager", "Assitant Director"],
                  ["Vice Direcctor", "Deputy Direcctor"], 
                  ["Direcctor"], 
                  ["Head"], 
                  ["Group"], 
                  ["Chief Operating Officer (COO)", "Chief Executive Officer (CEO)", "Chief Product Officer (CPO)", "Chief Financial Officer (CFO)"], 
                  ["General Manager", "General Director"]]
        
        level_map = {"0": 2, "1": 3, "2": 4, "3": 5, "4": 8, "5": 15, "6": 20, "7": 25, "8": 30}
        if data.current_salary:
            percent, _ = Resume.percent_estimate(filename=db_resume.ResumeVersion.filename)
            hard_point = round(percent*data.current_salary / 100000, 1)   # Convert money to point: 100000 (vnđ) => 1đ
        else:
            for level, point in level_map.items():
                if db_resume.level in levels[int(level)]:
                    hard_point += point
                    break

        #   ================================== Soft point ==================================
        degrees = [degree for degree in extracted_result["education"]["degree"]]

        return hard_point, soft_point
        

    @staticmethod
    def update_valuate(data: schema.ResumeValuation, db_session: Session, user):
        result = Resume.get_detail_resume_by_id(data.cv_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")
        
        #   Get point after re-define ResumeValuation
        hard_point, soft_point = Resume.valuate_base(result, data)
        result.ResumeVersion.hard_point = hard_point
        result.ResumeVersion.soft_point = soft_point
        db.commit_rollback(db_session)
        return result
    
    
    @staticmethod
    def matching_base(filename: str, check_dup: bool = False):
        #   Check duplicated filename
        if not DatabaseService.check_file_duplicate(filename, MATCHING_DIR):
            prompt_template = Extraction.matching_template(filename, check_dup)

            #   Read parsing requirements
            with open(MATCHING_PROMPT, "r") as file:
                require = file.read()
            prompt_template += require 
            
            #   Start parsing
            extracted_result = OpenAIService.gpt_api(prompt_template)        
            saved_path = DatabaseService.store_cv_extraction(extracted_json=extracted_result, cv_file=filename)
        else:
            #   Read available extracted result
            saved_path = os.path.join(CV_EXTRACTION_PATH, filename.split(".")[0] + ".json")
            with open(saved_path) as file:
                extracted_result = json.loads(file.read())
        return extracted_result, saved_path



        


    # @staticmethod
    # def ctv_list_job(job_status, db_session, user):

    #     query = (
    #         select(model.Company.logo, model.Company.company_name, 
    #                model.JobDescription.job_title, 
    #                model.JobDescription.industries, 
    #                model.JobDescription.created_at, 
    #                model.JobDescription.job_title, 
    #                model.JobDescription.job_service, 
    #                model.JobDescription.status)
    #                 .join(model.JobDescription, model.JobDescription.user_id == user.id)
    #                 .filter(model.JobDescription.ctv_job_status == job_status)
    #     )
    #     results = db_session.execute(query).all() 
    #     if not results:
    #         raise HTTPException(status_code=404, detail="Could not find any jobs!")
        
    #     query = select(func.count(model.ResumeNew.job_id))  \
    #                                     .where(model.ResumeNew.job_id == model.JobDescription.id)
    #     cv_count = db_session.execute(query).scalar()

        
    #     if status == schema.JobStatus.pending or status == schema.JobStatus.browsing:   #  Chờ duyệt - Đang duyệt
    #         return [{
    #             "ID": result.id,
    #             "Tên vị trí": result.job_title,
    #             "Ngày tạo": result.created_at,
    #             "Ngành nghề": result.industries,
    #             "Loại dịch vụ": result.job_service
    #         } for result in results]
            
    #     else:       #  Đang tủyển - Đã tủyển
    #         return [{
    #             "ID": result.id,
    #             "Tên vị trí": result.job_title,
    #             "Ngày đăng tuyển": result.created_at,
    #             "Loại dịch vụ": result.job_service,
    #             "CVs": cv_count
    #         } for result in results]