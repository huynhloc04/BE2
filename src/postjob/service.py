import model
import os, shutil, json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from config import db
from postjob import schema
from sqlmodel import Session, func, and_
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
                                company_images=[str(request.base_url) + company_img.filename for company_img in data.company_images] if data.company_images else None,
                                company_video=str(request.base_url) + data.company_video.filename if data.company_video else None,
                                linkedin=data.linkedin,
                                website=data.website,
                                facebook=data.facebook,
                                instagram=data.instagram)
        db_session.add(db_company)
        db.commit_rollback(db_session)

        #   Save file
        companies = ["logo", "cover_image", "company_images", "company_video"]
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
                shutil.copyfileobj(data.logo.file, file)
        if data.company_images:
            for image in data.company_images:
                with open(os.path.join(os.getenv("COMPANY_DIR"), "company_images",  image.filename), 'w+b') as file:
                    shutil.copyfileobj(image.file, file)
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
            lang_certs = [model.LanguageJobCertificate(job_id=data_form.job_id,
                                                **dict(lang_cert)) for lang_cert in data_form.language_certificates]
            db_session.add_all(lang_certs)
        if data_form.other_certificates:
            other_certs = [model.OtherJobCertificate(job_id=data_form.job_id,
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
        db_session.execute(model.LanguageJobCertificate.__table__.delete().where(model.LanguageJobCertificate.job_id == data_form.job_id)) 
        db_session.execute(model.OtherJobCertificate.__table__.delete().where(model.OtherJobCertificate.job_id == data_form.job_id)) 
        
        #   Add new Job information as an Update
        job_edus = [model.JobEducation(job_id=data_form.job_id,
                                      **dict(education)) for education in data_form.education]
        lang_certs = [model.LanguageJobCertificate(job_id=data_form.job_id,
                                              **dict(lang_cert)) for lang_cert in data_form.language_certificates]
        other_certs = [model.OtherJobCertificate(job_id=data_form.job_id,
                                             **dict(other_cert)) for other_cert in data_form.other_certificates]
            
        db_session.add_all(job_edus)
        db_session.add_all(lang_certs)
        db_session.add_all(other_certs)
        db.commit_rollback(db_session) 
        
        
    @staticmethod
    def create_draft(job_id: int, is_draft: bool, db_session: Session, user):
        result = Job.get_job_by_id(job_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        #   Create draft
        result.is_draft = is_draft
        db.commit_rollback(db_session) 
        
        
    @staticmethod
    def list_job(is_draft, db_session, user):
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                        model.JobDescription.is_draft == is_draft)
        results = db_session.execute(job_query).scalars().all() 
        if not results:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        query = select(func.count(model.Resume.job_id)).where(model.Resume.job_id == model.JobDescription.id)
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
        lang_certs = db_session.execute(select(model.LanguageJobCertificate).where(model.LanguageJobCertificate.job_id == job_id)).scalars().all()
        other_certs = db_session.execute(select(model.OtherJobCertificate).where(model.OtherJobCertificate.job_id == job_id)).scalars().all()
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
                    "language": lang_cert.certificate_language,
                    "certificate_name": lang_cert.certificate_name,
                    "certificate_level": lang_cert.certificate_level,
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
                    "language": lang_cert.certificate_language,
                    "certificate_name": lang_cert.certificate_name,
                    "certificate_level": lang_cert.certificate_level,
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
        
        query = select(func.count(model.Resume.job_id))  \
                                        .where(model.Resume.job_id == model.JobDescription.id)
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
    def ctv_get_detail_job(job_id, db_session, user):
        #   Company
        company_query = select(model.Company).where(model.Company.user_id == user.id)
        company_result = db_session.execute(company_query).scalars().first() 
        if not company_result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")
        #   Job
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                       model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")

        job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
        lang_certs = db_session.execute(select(model.LanguageJobCertificate).where(model.LanguageJobCertificate.job_id == job_id)).scalars().all()
        other_certs = db_session.execute(select(model.OtherJobCertificate).where(model.OtherJobCertificate.job_id == job_id)).scalars().all()
        
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
                "language": lang_cert.certificate_language,
                "certificate_name": lang_cert.certificate_name,
                "certificate_level": lang_cert.certificate_level,
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
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.user_id == current_user.id,
                   model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    def get_resume_by_id(cv_id: int, db_session: Session, current_user):
        query = select(model.Resume).where(model.Resume.user_id == current_user.id,
                                                model.Resume.id == cv_id)
        result = db_session.execute(query).first() 
        return result
    

    @staticmethod
    def send_email_request(cv_id: int, 
                           content: str,
                           db_session: Session,
                           current_user,
                           background_tasks: BackgroundTasks):
        resume_data = Resume.get_detail_resume_by_id(cv_id, db_session, current_user)
        try:
            background_tasks.add_task(
                                GoogleService.CONTENT_GOOGLE,
                                message=content, 
                                input_email=resume_data.ResumeVersion.email)
        except:
            raise HTTPException(status_code=503, detail="Could not send email!")
    
    
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
        db_resume = model.Resume(
                            user_id=user.id,
                            job_id=data.job_id,
                        )       
        db_session.add(db_resume)
        db.commit_rollback(db_session)
        db_version = model.ResumeVersion(
                            cv_id=db_resume.id,
                            filename=cleaned_filename,
                            cv_file=str(request.base_url) + cleaned_filename
                        )
        db_session.add(db_version)
        db.commit_rollback(db_session)
        return extracted_result


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
        result = Resume.get_detail_resume_by_id(data_form.cv_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")

        #   If the resume never existed in System => add to Database
        for key, value in dict(data_form).items():
            if key != "cv_id" and key != "level":
                if value is not None and key not in ["education",
                                                     "work_experiences",
                                                     "awards",
                                                     "projects",
                                                     "language_certificates",
                                                     "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
        if data_form.education:
            edus = [model.ResumeEducation(cv_id=data_form.cv_id,
                                              **dict(education)) for education in data_form.education]
            db_session.add_all(edus)
        if data_form.work_experiences:
            expers = [model.ResumeExperience(cv_id=data_form.cv_id,
                                            **dict(exper)) for exper in data_form.work_experiences]
            db_session.add_all(expers)
        if data_form.awards:
            awards = [model.ResumeAward(cv_id=data_form.cv_id,
                                        **dict(award)) for award in data_form.awards]
            db_session.add_all(awards)
        if data_form.projects:
            projects = [model.ResumeAward(cv_id=data_form.cv_id,
                                        **dict(project)) for project in data_form.projects]
            db_session.add_all(projects)
        if data_form.language_certificates:
            lang_certs = [model.ResumeAward(cv_id=data_form.cv_id,
                                        **dict(lang_cert)) for lang_cert in data_form.language_certificates]
            db_session.add_all(lang_certs)
        if data_form.other_certificates:
            other_certs = [model.ResumeAward(cv_id=data_form.cv_id,
                                        **dict(other_cert)) for other_cert in data_form.other_certificates]
            db_session.add_all(other_certs)
            
        db.commit_rollback(db_session) 
        
        return data_form


    #   ========================= Resume Valuation =========================
        
    @staticmethod
    def percent_estimate(filename: str):
        prompt_template = Extraction.resume_percent_estimate(filename)      
        #   Start parsing
        extracted_result = OpenAIService.gpt_api(prompt_template)
        point, explain = extracted_result["point"], extracted_result["explanation"]
        return point/100, explain
        

    @staticmethod
    def resume_valuate(data: schema.ResumeUpdate, db_session: Session, user):
        result = Resume.get_detail_resume_by_id(data.cv_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")
        
        #   Add "hard_point" initialization
        hard_point = 0
        for level, point in level_map.items():
            if data.level in levels[int(level)]:
                hard_point += point
                #   Save to Database
                db_valuate = model.ValuationInfo(
                                            cv_id=data.cv_id,
                                            hard=data.level,
                                            hard_point=point)
                db_session.add(db_valuate)
                db.commit_rollback(db_session)

        #   ============================== Soft point ==============================
            #   Degrees
        degrees = [edu.degree for edu in data.education if edu.degree in ["Bachelor", "Master", "Ph.D"]]
        degree_point = 0.5 * len(degrees)
            #   Certificates
        certs = []
        for cert in data.language_certificates:
            if cert.certificate_language == "English":
                if (cert.certificate_name == "TOEIC" and float(cert.certificate_point_level) > 700) or (cert.certificate_name == "IELTS" and float(cert.certificate_point_level) > 7.0):
                    certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
            elif cert.certificate_language == "Japan" and cert.certificate_point_level in ["N1", "N2"]:
                    certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
            elif cert.certificate_language == "Korean":
                if cert.certificate_name == "Topik II" and cert.certificate_point_level in ["Level 5", "Level 6"]:
                    certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
            elif cert.certificate_language == "Chinese" and cert.certificate_point_level == ["HSK-5", "HSK6"]:
                    certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
        cert_point = 0.5 * len(certs)
        #   Add "soft_point" to Database
        db_valuate.degrees = degrees,
        db_valuate.degree_point = degree_point,
        db_valuate.certificates = certs,
        db_valuate.certificates_point = cert_point,
        db_valuate.total_point = hard_point + degree_point + cert_point
        db.commit_rollback(db_session)

        #   Update Resume valuation status
        result.ResumeVersion.status = "Pricing Approved"
        return db_valuate
        
        
    @staticmethod
    def update_draft(cv_id: int, is_draft: bool, db_session: Session, user):
        result = Resume.get_detail_resume_by_id(cv_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")
        
        #   Create draft
        result.ResumeVersion.is_draft = is_draft
        db.commit_rollback(db_session) 
        

    @staticmethod
    def update_valuate(data: schema.ResumeValuation, db_session: Session, user):
        result = Resume.get_detail_resume_by_id(data.cv_id, db_session, user) 
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == data.cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This Resume has not been valuated!")
        
        #   Point initialization
        hard_point = 0
        if data.current_salary != 0:
            percent, _ = Resume.percent_estimate(filename=result.ResumeVersion.filename)
            hard_point = round(percent*data.current_salary / 100000, 1)   # Convert money to point: 100000 (vnđ) => 1đ
            valuate_result.hard = data.current_salary
            valuate_result.hard_point = hard_point
            #   Commit to Database
            result.ResumeVersion.status = "Pricing Approved"
            db.commit_rollback(db_session)
        elif data.level:
            for level, point in level_map.items():
                if data.level in levels[int(level)]:
                    hard_point += point
                    valuate_result.hard = data.level
                    valuate_result.hard_point = hard_point
                    #   Commit to Database
                    result.ResumeVersion.status = "Pricing Approved"
                    db.commit_rollback(db_session)
                    break
        else:
            pass

        #   ================================== Soft point ==================================
        #   Degrees
        if data.degrees:
            degrees = [degree for degree in data.degrees if degree in ["Bachelor", "Master", "Ph.D"]]
            degree_point = 0.5 * len(degrees)
            #   Add "soft_point" to Database
            valuate_result.degrees = degrees
            valuate_result.degree_point = degree_point
            result.ResumeVersion.status = "Pricing Approved"
            db.commit_rollback(db_session)
        #   Certificates
        if data.language_certificates:
            certs = []
            for cert in data.language_certificates:
                if cert.certificate_language == "English":
                    if (cert.certificate_name == "TOEIC" and float(cert.certificate_point_level) > 700) or (cert.certificate_name == "IELTS" and float(cert.certificate_point_level) > 7.0):
                        certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
                elif cert.certificate_language == "Japan" and cert.certificate_point_level in ["N1", "N2"]:
                        certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
                elif cert.certificate_language == "Korean":
                    if cert.certificate_name == "Topik II" and cert.certificate_point_level in ["Level 5", "Level 6"]:
                        certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
                elif cert.certificate_language == "Chinese" and cert.certificate_point_level == ["HSK-5", "HSK6"]:
                        certs.append(cert.certificate_language + " - " + cert.certificate_name + " - " + cert.certificate_point_level)
            cert_point = 0.5 * len(certs)
            #   Add "soft_point" to Database
            valuate_result.certificates = certs
            valuate_result.certificates_point = cert_point
            valuate_result.total_point = hard_point + degree_point + cert_point

            #   Update Resume valuation status
            result.ResumeVersion.status = "Pricing Approved"
            db.commit_rollback(db_session)
        return valuate_result
    
    
    @staticmethod
    def get_resume_valuate(cv_id, db_session):
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This resume has not been valuated!")
        return valuate_result

        

    
    @staticmethod
    def matching_base(cv_filename: str, jd_filename: str):
        #   Create saved file name
        match_filename = jd_filename.split(".")[0] + "__" + cv_filename
        #   Check duplicated filename
        if not DatabaseService.check_file_duplicate(match_filename, MATCHING_DIR):
            prompt_template = Extraction.matching_template(cv_filename, jd_filename)

            #   Read parsing requirements
            with open(MATCHING_PROMPT, "r") as file:
                require = file.read()
            prompt_template += require 
            
            #   Start parsing
            matching_result = OpenAIService.gpt_api(prompt_template)        
            saved_path = DatabaseService.store_matching_result(extracted_json=matching_result, saved_name=match_filename)
        else:
            #   Read available extracted result
            saved_path = os.path.join(MATCHING_DIR, match_filename.split(".")[0] + ".json")
            with open(saved_path) as file:
                matching_result = json.loads(file.read())
        return matching_result, saved_path


    @staticmethod
    def cv_jd_matching(cv_id: int, db_session: Session, user, background_task: BackgroundTasks):
        resume_result = Resume.get_detail_resume_by_id(cv_id, db_session, user)       
        if not resume_result:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume does not exist")
        
        #   Get Job by cv_id
        job_result = Job.get_job_by_id(resume_result.Resume.job_id,
                                       db_session,
                                       user)

        matching_result, saved_dir = Resume.matching_base(cv_filename=resume_result.ResumeVersion.filename, 
                                                          jd_filename=job_result.jd_file.split("/")[-1])
        
        overall_score = int(matching_result["overall"]["score"])
        if overall_score >= 50:
            mail_content = f"""
            <html>
                <body>
                    <p> Dear {resume_result.ResumeVersion.name}, <br>
                        Warm greetings from sharecv.vn ! 
                        Your profile has been recommended on sharecv.vn. However, please be aware that only when we have your permission, the profile will be sent to the employer to review and evaluate. <br>
                        Hence, please CLICK to below: <br>
                        - <a href="https://sharecv.vn/?page=accept&id={user.id}&token=&act=accept">"Accept"</a> Job referral acceptance letter. <br>
                        - <a href="https://sharecv.vn/?page=decline&id={user.id}&token=&act=decline">"Decline"</a> Job referral refusal letter. <br>
                        Thank you for your cooperation. Should you need any further information or assistance, please do not hesitate to contact us. <br>

                        Thanks and best regards, <br>
                        Team ShareCV Customer Support <br>
                        Hotline: 0888818006 – 0914171381 <br>
                        Email: info@sharecv.vn <br>

                        THANK YOU
                    </p>
                </body>
            </html>
            """
            #  Send mail
            Resume.send_email_request(cv_id, mail_content, db_session, user, background_task)
            #   Update resume status 
            resume_result.ResumeVersion.status = "Waiting Candidate Approve"
            #   Write matching result to Database
            matching_db = model.ResumeMatching(
                                    job_id=resume_result.Resume.job_id,
                                    cv_id=cv_id,
                                    title_score=int(matching_result["job_title"]["score"]),
                                    title_explain=matching_result["job_title"]["explanation"],
                                    exper_score=int(matching_result["experience"]["score"]),
                                    exper_explain=matching_result["experience"]["explanation"],
                                    skill_score=int(matching_result["skill"]["score"]),
                                    skill_explain=matching_result["skill"]["explanation"],
                                    education_score=int(matching_result["education"]["score"]),
                                    education_explain=matching_result["education"]["explanation"],
                                    orientation_score=int(matching_result["orientation"]["score"]),
                                    orientation_explain=matching_result["orientation"]["explanation"],
                                    overall_score=int(matching_result["overall"]["score"]),
                                    overall_explain=matching_result["overall"]["explanation"]
            )
            db_session.add(matching_db)
        else:
            #   Update resume status 
            resume_result.ResumeVersion.status = "AI Matching Rejected"
        db.commit_rollback(db_session)
        return matching_result, saved_dir, cv_id
    
    
    @staticmethod
    def get_matching_result(cv_id: int, db_session: Session, user):
        #   Get resume information
        resume = Resume.get_detail_resume_by_id(cv_id, db_session, user)
        matching_query = select(model.ResumeMatching).where(model.ResumeMatching.cv_id == cv_id,
                                                            model.ResumeMatching.job_id == resume.Resume.job_id)
        matching_result = db_session.execute(matching_query).scalars().first()
        if not matching_result:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This CV and JD have not been matched")
       
        return {
            "job_title": {
                "score": matching_result.title_score,
                "explanation": matching_result.title_explain
            },
            "experience": {
                "score": matching_result.exper_score,
                "explanation": matching_result.exper_explain
            },
            "skill": {
                "score": matching_result.skill_score,
                "explanation": matching_result.skill_explain
            },
            "education": {
                "score": matching_result.education_score,
                "explanation": matching_result.education_explain
            },
            "orientation": {
                "score": matching_result.orientation_score,
                "explanation": matching_result.orientation_explain
            },
            "overall": {
                "score": matching_result.overall_score,
                "explanation": matching_result.overall_explain
            }
        }


    @staticmethod
    def candidate_reply(cv_id: int, reply_status: str, db_session: Session, user):
        resume_result = Resume.get_detail_resume_by_id(cv_id, db_session, user)       
        if not resume_result.ResumeVersion.filename:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload atleast 1 CV PDF")
        
        #   Update resume status 
        resume_result.ResumeVersion.status = reply_status
        db.commit_rollback(db_session)


    @staticmethod
    def get_detail_resume(cv_id, db_session, user):
        
        resume_result = Resume.get_detail_resume_by_id(cv_id, db_session, user) 
        if not resume_result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")
        job_result = Job.get_job_by_id(cv_id, db_session, user)
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")

        educations = db_session.execute(select(model.ResumeEducation).where(model.ResumeEducation.cv_id == cv_id)).scalars().all()
        experience = db_session.execute(select(model.ResumeExperience).where(model.ResumeExperience.cv_id == cv_id)).scalars().all()
        projects = db_session.execute(select(model.ResumeProject).where(model.ResumeProject.cv_id == cv_id)).scalars().all()
        awards = db_session.execute(select(model.ResumeAward).where(model.ResumeAward.cv_id == cv_id)).scalars().all()
        lang_certs = db_session.execute(select(model.LanguageResumeCertificate).where(model.LanguageResumeCertificate.cv_id == cv_id)).scalars().all()
        other_certs = db_session.execute(select(model.OtherResumeCertificate).where(model.OtherResumeCertificate.cv_id == cv_id)).scalars().all()
        
        return {
            "cv_id": cv_id,
            "status": resume_result.ResumeVersion.status,
            "job_service": job_result.job_service,
            "avatar": resume_result.ResumeVersion.avatar,
            "candidate_name": resume_result.ResumeVersion.name,
            "current_job": resume_result.ResumeVersion.current_job,
            "industry": resume_result.ResumeVersion.industry,
            "birthday": resume_result.ResumeVersion.birthday,
            "gender": resume_result.ResumeVersion.gender,
            "objectives": resume_result.ResumeVersion.objectives,
            "email": resume_result.ResumeVersion.email,
            "phone": resume_result.ResumeVersion.phone,
            "identification_code": resume_result.ResumeVersion.identification_code,
            "address": resume_result.ResumeVersion.address,
            "city": resume_result.ResumeVersion.city,
            "country": resume_result.ResumeVersion.country,
            "linkedin": resume_result.ResumeVersion.linkedin,
            "website": resume_result.ResumeVersion.website,
            "facebook": resume_result.ResumeVersion.facebook,
            "instagram": resume_result.ResumeVersion.instagram,
            "experience": [{
                "job_tile": exper.job_tile,
                "company_name": exper.company_name,
                "start_time": exper.start_time,
                "end_time": exper.end_time,
                "levels": exper.levels,  #   Cấp bậc đảm nhiêm 
                "roles": exper.roles,    #   Vai trò đảm nhiệm
            } for exper in experience],
            "educations": [{
                "institute": edu.institute_name,
                "degree": edu.degree,
                "major": edu.major,
                "start_time": edu.start_time,
                "end_time": edu.end_time,
            } for edu in educations],
            "projects": [{
                "project_name": project.project_name,
                "description": project.description,
                "start_time": project.start_time,
                "end_time": project.end_time,
            } for project in projects],
            "awards": [{
                "name": award.name,
                "time": award.time,
                "description": award.description,
            } for award in awards],
            "certificates": {
                "language_certificates": [{
                    "certificate_language": lang_cert.certificate_language,
                    "certificate_name": lang_cert.certificate_name,
                    "certificate_level": lang_cert.certificate_level
                } for lang_cert in lang_certs],
                "other_certificate": [{
                    "certificate_name": other_cert.certificate_name,
                    "certificate_level": other_cert.certificate_level
                } for other_cert in other_certs]
          }
        }
    
        
    @staticmethod
    def get_cv_file(cv_id, db_session, user):
        result = Resume.get_detail_resume_by_id(cv_id, db_session, user)    
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")        
        #   Return link to JD PDF file 
        return result.ResumeVersion.cv_file


    @staticmethod
    def list_job(job_status, db_session, user):
        #   ======================= Đã giới thiệu =======================
        if job_status == schema.CollaborateJobStatus.referred:
            query_referred = (
                        select(
                            model.Company.id,
                            model.Company.logo, 
                            model.Company.company_name, 
                            model.JobDescription.id,
                            model.JobDescription.job_title,
                            model.JobDescription.industries,
                            model.JobDescription.created_at,
                            model.JobDescription.job_service, 
                            model.JobDescription.status
                        )
                        .join(model.JobDescription, model.Company.user_id == model.JobDescription.user_id)
                        .outerjoin(model.Resume, model.JobDescription.id == model.Resume.job_id)
                        .group_by(
                            model.Company.id,
                            model.Company.logo, 
                            model.Company.company_name, 
                            model.JobDescription.id,
                            model.JobDescription.job_title,
                            model.JobDescription.industries,
                            model.JobDescription.created_at,
                            model.JobDescription.job_service, 
                            model.JobDescription.status)
                        .having(func.count(model.Resume.id) > 0)
                    )
            result_referred = db_session.execute(query_referred).all() 
            if not result_referred:
                raise HTTPException(status_code=404, detail="Could not find any referred jobs!")
            return result_referred, len(result_referred)
        
        #  ======================= Favorite Jobs ======================= 
        
        elif job_status == schema.CollaborateJobStatus.favorite:
            query_favorite = (
                        select(
                            model.Company.id,
                            model.Company.logo,
                            model.Company.company_name, 
                            model.JobDescription.id,
                            model.JobDescription.job_title,
                            model.JobDescription.industries,
                            model.JobDescription.created_at,
                            model.JobDescription.job_service, 
                            model.JobDescription.status
                        )
                        .join(model.JobDescription, model.JobDescription.user_id == model.Company.user_id)
                        .filter(model.JobDescription.is_favorite == True)
                    )
            result_favorite = db_session.execute(query_favorite).all() 
            if not result_favorite:
                raise HTTPException(status_code=404, detail="Could not find any favorite jobs!")
            return result_favorite, len(result_favorite)
        
        #  ======================= Chưa giới thiệu =======================
        elif job_status == schema.CollaborateJobStatus.unreferred:
            query_unreferred = (
                        select(
                            model.Company.id,
                            model.Company.logo, 
                            model.Company.company_name, 
                            model.JobDescription.id,
                            model.JobDescription.job_title,
                            model.JobDescription.industries,
                            model.JobDescription.created_at,
                            model.JobDescription.job_service, 
                            model.JobDescription.status
                        )
                        .join(model.JobDescription, model.Company.user_id == model.JobDescription.user_id)
                        .outerjoin(model.Resume, model.JobDescription.id == model.Resume.job_id)
                        .group_by(
                            model.Company.id,
                            model.Company.logo, 
                            model.Company.company_name, 
                            model.JobDescription.id,
                            model.JobDescription.job_title,
                            model.JobDescription.industries,
                            model.JobDescription.created_at,
                            model.JobDescription.job_service, 
                            model.JobDescription.status)
                        .having(func.count(model.Resume.id) == 0)
                        .filter(model.JobDescription.is_favorite == False)
            )
            result_unreferred = db_session.execute(query_unreferred).all() 
            if not result_unreferred:
                raise HTTPException(status_code=404, detail="Could not find any unreferred jobs")
            return result_unreferred, len(result_unreferred)
        else:
            pass

    
    @staticmethod
    def list_candidate(db_session: Session, current_user):
        resume_query = select(model.ResumeVersion).where(model.ResumeVersion.cv_id == current_user.id)
        resume_result = db_session.execute(resume_query).all() 

        return {
            "data_lst": [{
                "id": result.id,
                "fullname": result.name,
                "email": result.email,
                "phone": result.phone,
                "job_title": result.job_title,
                "industry": result.industry,
                "job_service": Job.get_job_by_id(),
                "status": result.status,
                "referred_time": result.created_at
            } for result in resume_result],
            "data_len": len(resume_result)
        }


    @staticmethod
    def list_draft_candidate(db_session: Session, current_user):
        resume_query = select(model.ResumeVersion).where(model.ResumeVersion.cv_id == current_user.id)
        resume_result = db_session.execute(resume_query).scalars().all() 

        return {
            "data_lst": [{
                "id": result.cv_id,
                "fullname": result.name,
                "job_title": result.current_job,
                "industry": result.industry,
                "drafted_time": result.created_at
            } for result in resume_result],
            "data_len": len(resume_result)
        }


    

