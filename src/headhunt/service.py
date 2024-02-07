import model
import time
import os, shutil, json
from config import db
from datetime import datetime, timedelta
from headhunt import schema
from sqlmodel import Session, func, and_, or_, not_
from sqlalchemy import select
from fastapi import HTTPException, Request, BackgroundTasks, UploadFile, status
from postjob.gg_service.gg_service import GoogleService
from postjob.api_service.extraction_service import Extraction
from postjob.api_service.openai_service import OpenAIService
from postjob.db_service.db_service import DatabaseService
from config import (
                CV_PARSE_PROMPT, 
                JD_PARSE_PROMPT,
                CV_EXTRACTION_PATH,
                JD_EXTRACTION_PATH, 
                JD_SAVED_TEMP_DIR,
                JD_SAVED_DIR,
                CV_SAVED_DIR,
                CV_SAVED_TEMP_DIR,
                EDITED_JOB,
                MATCHING_PROMPT,
                MATCHING_DIR)

background_task_results = {}


""" 
Class_Model_Structure
        |___ AuthRequestRepository
        |
        |___ OTPRepo
        |
        |___ Company
        |
        |___ General
        |
        |___ Recruiter
        |   |
        |   |_____ Resume
        |   |
        |   |_____ Job
        |
        |___ Admin
        |   |
        |   |_____ Resume
        |   |
        |   |_____ Job
        |
        |___ Collaborator
            |
            |_____ Resume
            |
            |_____ Job

"""


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
        token = db_session.execute(select(model.JWTModel).where(model.JWTModel.token == token)).scalar_one_or_none()
        if token:
            return True
        return False

    
levels = [
        ["Executive", "Senior", "Engineer", "Developer"], 
        ["Leader", "Supervisor", "Senior Leader", "Senior Supervisor", "Assitant Manager"], 
        ["Manager", "Senior Manager", "Assitant Director"],
        ["Vice Direcctor", "Deputy Direcctor"], 
        ["Direcctor"], 
        ["Head"], 
        ["Group"], 
        ["Chief Operating Officer", "Chief Executive Officer", "Chief Product Officer", "Chief Financial Officer"], 
        ["General Manager", "General Director"]]
            
level_map = {"0": 2, "1": 3, "2": 4, "3": 5, "4": 8, "5": 15, "6": 20, "7": 25, "8": 30}


class Company:

    @staticmethod
    def add_company(
                db_session: Session,
                data: schema.CompanyBase,
                current_user):
        current_company = db_session.execute(select(model.Company).where(model.Company.user_id == current_user.id)).scalars().first()
        if current_company:
            raise HTTPException(status_code=409, detail="You have registered company information!")

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
                                logo=os.path.join("static/company/logo", data.logo.filename) if data.logo else None,
                                cover_image=os.path.join("static/company/cover_image", data.cover_image.filename) if data.cover_image else os.path.join("static/company/cover_image", "default_cover_image.jpg"),
                                company_video=os.path.join("static/company/company_video", data.company_video.filename) if data.company_video else None,
                                company_images=[os.path.join("static/company/company_images", company_image.filename) for company_image in data.company_images] if data.company_images else None,
                                linkedin=data.linkedin,
                                website=data.website,
                                facebook=data.facebook,
                                instagram=data.instagram)
        db_session.add(db_company)
         #   Set as default image if there's no uploaded cover image
        db_company.cover_image = os.path.join("static/company/cover_image", "default_cover_image.jpg")
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
        if data.company_video:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "company_video",  data.company_video.filename), 'w+b') as file:
                shutil.copyfileobj(data.company_video.file, file)
        if data.company_images:
            for company_image in data.company_images:
                with open(os.path.join(os.getenv("COMPANY_DIR"), "company_images",  company_image.filename), 'w+b') as file:
                    shutil.copyfileobj(company_image.file, file)
        return db_company
    
    
    @staticmethod
    def get_company(db_session: Session, user):
        query = select(model.Company).where(model.Company.user_id == user.id)
        results = db_session.execute(query).scalars().first()
        return results
    

    @staticmethod
    def get_general_info(job_id, db_session, user):
        #   Company
        company_query = select(model.Company).where(model.Company.user_id == user.id)
        company_result = db_session.execute(company_query).scalars().first() 
        if not company_result:
            raise HTTPException(status_code=404, detail="Company doesn't exist!")
        #   Job
        job_result = General.get_job_by_id(job_id, db_session)
        if not job_result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        return {
            #   Company
            "company_logo": company_result.logo,
            "company_name": company_result.company_name,
            "industry": company_result.industry,
            "company_size": company_result.company_size,
            "founded_year": company_result.founded_year,
            "tax_code": company_result.tax_code,
            "address": company_result.address,
            "city": company_result.city,
            "country": company_result.country,
            #   Job
            "status": job_result.status,
            "job_service": job_result.job_service,
            "job_title": job_result.job_title
        }
    

    @staticmethod
    def update_company(
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
            if value is not None and (key != "logo" or key != "company_video" or key != "company_images" or key != "cover_image"):
                setattr(result, key, value)

        #   Update images
        result.logo = os.path.join("static/company/logo", data.logo.filename) if data.logo else None
        if data.logo:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "logo",  data.logo.filename), 'w+b') as file:
                shutil.copyfileobj(data.logo.file, file)

        #   Company cover_image
        result.cover_image = os.path.join("static/company/cover_image", data.cover_image.filename) if data.cover_image else None
        if data.cover_image:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "cover_image",  data.cover_image.filename), 'w+b') as file:
                shutil.copyfileobj(data.cover_image.file, file)

        #   Company_video
        result.company_video = os.path.join("static/company/company_video", data.company_video.filename) if data.company_video else None
        if data.company_video:
            with open(os.path.join(os.getenv("COMPANY_DIR"), "company_video",  data.company_video.filename), 'w+b') as file:

        #   Company_image
                shutil.copyfileobj(data.company_video.file, file)
        result.company_images=[os.path.join("static/company/company_images", company_image.filename) for company_image in data.company_images] if data.company_images else None
        if data.company_images:
            for company_image in data.company_images:
                with open(os.path.join(os.getenv("COMPANY_DIR"), "company_images",  company_image.filename), 'w+b') as file:
                    shutil.copyfileobj(company_image.file, file)
        db.commit_rollback(db_session)    
        return result
    
    
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
    def list_industry():
        industries = [
            "Education", "Construction", "Design", "Corporate Services", "Retail", "Energy & Mining", "Manufacturing", "Finance", "Recreation & Travel", "Arts", "Health Care", "Hardware & Networking", "Software & IT Services", "Real Estate", "Legal", "Agriculture", "Media & Communications", "Transportation & Logistics", "Entertainment", "Wellness & Fitness", "Public Safety", "Public Administration"
        ]
        return industries
    
    
class General:  
    
    def string_parse(data):
        indices = []
        index = data.find("\\n")
        while index != -1:
            indices.append(index)
            index = data.find('\\n', index + 1)
        if indices:
            new_data = [data[1:indices[0]-2]]
            new_data += [data[indices[i]+2:indices[i+1]-2] for i in range(len(indices)-1)]
            new_data.append(data[indices[-1]+2:-2])
            return new_data
        return data

    def json_parse(data):
        open_indices = []
        close_indices = []
        open_index = data.find("{")
        close_index = data.find("}")
        while open_index != -1:
            open_indices.append(open_index)
            open_index = data.find('{', open_index + 1)
        while close_index != -1:
            close_indices.append(close_index)
            close_index = data.find('}', close_index + 1)
        parsed_json = []
        for i, j in zip(open_indices, close_indices):
            parsed_json.append(json.loads(data[i: j+1]))
        return parsed_json
    
    def count_remaining_days(cv_id: int, headhunt_point: float, user: model.User, db_session: Session):
        while True:
            resume_db = db_session.execute(select(model.RecruitResumeJoin).where(model.RecruitResumeJoin.resume_id == cv_id)).scalars().first()
            remain_time = resume_db.remain_warantty_time
            if remain_time > 0:
                resume_db.remain_warantty_time -= 1
                db.commit_rollback(db_session)
                if remain_time == 0:
                    user.point = headhunt_point
                    user.warranty_point = 0
                    db.commit_rollback(db_session)
            else:
                time.sleep(86400)

            
    def get_job_by_id(job_id: int, db_session: Session):
        job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
        
    def get_job_from_resume(cv_id: int, db_session: Session):
        resume = db_session.execute(select(model.Resume).where(model.Resume.id == cv_id)).scalars().first()
        job = db_session.execute(select(model.JobDescription).where(model.JobDescription.id == resume.job_id)).scalars().first()
        return job
            
    def get_detail_resume_by_id(cv_id: int, db_session: Session):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    def background_send_email(input_data):
        for recipient in input_data.values():
            GoogleService.CONTENT_GOOGLE(recipient["content"], recipient["email"])
        
    @staticmethod
    def get_jd_file(request, job_id, db_session):
        result = General.get_job_by_id(job_id, db_session)    
        if not result:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")        
        #   Return link to JD PDF file 
        return os.path.join(str(request.base_url), result.jd_file)
    
    @staticmethod
    def get_cv_file(request, cv_id, db_session):
        result = General.get_detail_resume_by_id(cv_id, db_session)    
        if not result:
            raise HTTPException(status_code=404, detail="Resume doesn't exist!")        
        #   Return link to JD PDF file 
        return os.path.join(str(request.base_url), result.ResumeVersion.cv_file)
    
    
    @staticmethod
    def get_resume_valuate(cv_id, db_session):
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This resume has not been valuated!")
        return valuate_result
    
    
class Recruiter:
    
    class Job:

        @staticmethod
        def jd_parsing(uploaded_file: UploadFile):    
            #   Save file as temporarily
            cleaned_filename = DatabaseService.clean_filename(uploaded_file.filename)
            with open(os.path.join(JD_SAVED_TEMP_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(uploaded_file.file, file)    
            #   Check duplicated filename
            if not DatabaseService.check_file_duplicate(cleaned_filename, JD_EXTRACTION_PATH):
                prompt_template = Extraction.jd_parsing_template(store_path=JD_SAVED_TEMP_DIR, filename=cleaned_filename)

                #   Read parsing requirements
                with open(JD_PARSE_PROMPT, "r") as file:
                    require = file.read()
                prompt_template += require 
                
                #   Start parsing
                extracted_result = OpenAIService.gpt_api(prompt_template)
                
                #   Save extracted result
                saved_path = DatabaseService.store_jd_extraction(extracted_json=extracted_result, jd_file=cleaned_filename)
            else:
                #   Read available extracted result
                saved_path = os.path.join(JD_EXTRACTION_PATH, cleaned_filename.split(".")[0] + ".json")
                with open(saved_path) as file:
                    extracted_result = file.read()
            #   Remove saved temporary file
            os.remove(os.path.join(JD_SAVED_TEMP_DIR, cleaned_filename))
            return extracted_result, saved_path
            
            
        @staticmethod
        def fill_job(data_form: schema.FillJob,
                     db_session: Session,
                     user):            
            #   Save UploadedFile first
            cleaned_filename = DatabaseService.clean_filename(data_form.jd_file.filename)
            #   Get company information
            company_result = db_session.execute(select(model.Company).where(model.Company.user_id == user.id)).scalars().first()
            db_job = model.JobDescription(
                        user_id=user.id,
                        company_id=company_result.id,
                        job_service="Headhunt",
                        jd_file=os.path.join("static/job/uploaded_jds", cleaned_filename)
            )
            db_session.add(db_job)
            db.commit_rollback(db_session)
            #   Save JD file
            with open(os.path.join(JD_SAVED_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data_form.jd_file.file, file)

            #   Save parsed information in JobDescription
            for key, value in dict(data_form).items():
                if key != "jd_file" and value is not None:
                    if (key != "education" and key != "language_certificates" and key != "other_certificates"):
                        setattr(db_job, key, value)  
                
            if data_form.education:
                job_edus = [model.JobEducation(job_id=db_job.id, **education) for education in General.json_parse(data_form.education[0])]
                db_session.add_all(job_edus)
            if data_form.language_certificates:
                lang_certs = [model.LanguageJobCertificate(job_id=db_job.id, **lang_cert) for lang_cert in General.json_parse(data_form.language_certificates[0])]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherJobCertificate(job_id=db_job.id, **other_cert) for other_cert in General.json_parse(data_form.other_certificates[0])]
                db_session.add_all(other_certs)

                
            db.commit_rollback(db_session) 
            
            
        @staticmethod
        def update_job(data_form: schema.JobUpdate,
                    db_session: Session):
            result = General.get_job_by_id(data_form.job_id, db_session)    
            if not result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            
            for key, value in dict(data_form).items():
                if value is not None and key != "job_id" and (key != "education" and key != "language_certificates" and key != "other_certificates"):
                    setattr(result, key, value) 
                        
            
            #   Delete all old information and add new ones    (Methoods to delete multiple rows in one Table)      
            if data_form.education:
                db_session.execute(model.JobEducation.__table__.delete().where(model.JobEducation.job_id == data_form.job_id)) 
                #   Add new Job information as an Update
                job_edus = [model.JobEducation(job_id=data_form.job_id,
                                            **dict(education)) for education in data_form.education]
                db_session.add_all(job_edus)
                
            if data_form.language_certificates:
                db_session.execute(model.LanguageJobCertificate.__table__.delete().where(model.LanguageJobCertificate.job_id == data_form.job_id)) 
                lang_certs = [model.LanguageJobCertificate(job_id=data_form.job_id,
                                                    **dict(lang_cert)) for lang_cert in data_form.language_certificates]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                db_session.execute(model.OtherJobCertificate.__table__.delete().where(model.OtherJobCertificate.job_id == data_form.job_id)) 
                other_certs = [model.OtherJobCertificate(job_id=data_form.job_id,
                                                    **dict(other_cert)) for other_cert in data_form.other_certificates]
                db_session.add_all(other_certs)
                
            db.commit_rollback(db_session) 
            
            
        @staticmethod
        def create_draft_job(
                        data_form: schema.FillDraftJob,
                        db_session: Session,
                        user):            
            #   Save UploadedFile first
            cleaned_filename = DatabaseService.clean_filename(data_form.jd_file.filename)
            #   Get company information
            company_result = db_session.execute(select(model.Company).where(model.Company.user_id == user.id)).scalars().first()
            db_job = model.JobDescription(
                            user_id=user.id,
                            company_id=company_result.id,
                            job_service="PostJob",
                            is_draft=True,
                            jd_file=os.path.join("static/job/uploaded_jds", cleaned_filename)
            )
            db_session.add(db_job)
            db.commit_rollback(db_session)
            #   Save JD file
            with open(os.path.join(JD_SAVED_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data_form.jd_file.file, file)

            #   Save parsed information in JobDescription
            for key, value in dict(data_form).items():
                if value is not None and (key != "jd_file" and key != "education" and key != "language_certificates" and key != "other_certificates"):
                        setattr(db_job, key, value)  
                
            if data_form.education:
                job_edus = [model.JobEducation(job_id=db_job.id, **education) for education in General.json_parse(data_form.education[0])]
                db_session.add_all(job_edus)
            if data_form.language_certificates:
                lang_certs = [model.LanguageJobCertificate(job_id=db_job.id, **lang_cert) for lang_cert in General.json_parse(data_form.language_certificates[0])]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherJobCertificate(job_id=db_job.id, **other_cert) for other_cert in General.json_parse(data_form.other_certificates[0])]
                db_session.add_all(other_certs)                
            db.commit_rollback(db_session) 
            
            
        @staticmethod
        def list_created_job(is_draft, db_session, user):                   
            if is_draft:
                query = select(model.JobDescription).where(
                                            model.JobDescription.is_draft == is_draft,
                                            model.JobDescription.user_id == user.id)
                results = db_session.execute(query).scalars().all()      
                if not results:
                    raise HTTPException(status_code=404, detail="Could not found any relevant jobs!")
                return [{
                    "job_id": result.id,
                    "job_title": result.job_title,
                    "industry": result.industries,
                    "job_service": "Posting Job",  #result.job_service,
                    "created_time": result.created_at
                } for result in results]
            else:
                query = select(model.JobDescription, func.count(model.Resume.id).label("resume_count"))     \
                                    .join(model.Resume, model.JobDescription.id == model.Resume.job_id)   \
                                    .where(model.JobDescription.is_draft == is_draft,
                                            model.JobDescription.user_id == user.id)    \
                                    .group_by(model.JobDescription.id)
                
                # query = select(model.JobDescription, func.count(model.Resume.id).label("resume_count"))     \
                #             .join(model.Resume, model.JobDescription.id == model.Resume.job_id, isouter=True)   \
                #             .group_by(model.JobDescription.id)

                results = db_session.execute(query).all() 
                if not results:
                    raise HTTPException(status_code=404, detail="Could not found any relevant jobs!")

                return [{
                    "job_id": result.JobDescription.id,
                    "job_title": result.JobDescription.job_title,
                    "recruited_time": result.JobDescription.created_at,
                    "industry": result.JobDescription.industries,
                    "job_service": result.JobDescription.job_service,
                    "status": result.JobDescription.status,
                    "num_cvs": result[1]
                } for result in results]
            
            
        @staticmethod
        def get_detail_job(request, job_id, db_session):
            #   Get Job information
            job_result = General.get_job_by_id(job_id, db_session)
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Company
            company_query = select(model.Company).where(model.Company.id == job_result.company_id)
            company_result = db_session.execute(company_query).scalars().first() 
            if not company_result:
                raise HTTPException(status_code=404, detail="Company doesn't exist!")

            job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
            lang_certs = db_session.execute(select(model.LanguageJobCertificate).where(model.LanguageJobCertificate.job_id == job_id)).scalars().all()
            other_certs = db_session.execute(select(model.OtherJobCertificate).where(model.OtherJobCertificate.job_id == job_id)).scalars().all()
            
            if job_result.status==schema.JobStatus.pending:
                return {
                    "status": job_result.status,
                    "job_service": job_result.job_service,
                    "job_title": job_result.job_title,
                    "industry": job_result.industries,
                    "gender": job_result.gender,
                    "job_type": job_result.job_type,
                    "skills": job_result.skills,
                    "received_job_time": job_result.received_job_time,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
                    "levels": job_result.levels,
                    "roles": job_result.roles,
                    "num_recruit": job_result.num_recruit,
                    "education": [{
                        "degree": edu.degree,
                        "major": edu.major,
                        "gpa": edu.gpa,
                    } for edu in job_edus],
                    "language_certificate": [{
                        "language": lang_cert.certificate_language,
                        "certificate_name": lang_cert.certificate_name,
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,                
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country,
                    "point": job_result.point,
                    "correspone_price": job_result.correspone_price,
                    "warranty_time": job_result.warranty_time
                }
            elif job_result.status==schema.JobStatus.reviewing:
                return {
                    "status": job_result.status,
                    "job_service": job_result.job_service,
                    "admin_decline_reason": job_result.admin_decline_reason,
                    "job_title": job_result.job_title,
                    "industry": job_result.industries,
                    "gender": job_result.gender,
                    "job_type": job_result.job_type,
                    "skills": job_result.skills,
                    "received_job_time": job_result.received_job_time,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
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
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,   
                    #   Working localtion             
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country,
                    "point": job_result.point,
                    "correspone_price": job_result.correspone_price,
                    "warranty_time": job_result.warranty_time
                }
            elif job_result.status==schema.JobStatus.recruiting:
                return {
                    "company_logo": os.path.join(str(request.base_url), company_result.logo) if company_result.logo else None,
                    "company_name": company_result.company_name,
                    "company_cover_image": os.path.join(str(request.base_url), company_result.cover_image) if company_result.cover_image else None,
                    "status": job_result.status,
                    "job_service": job_result.job_service,
                    "job_title": job_result.job_title,
                    "industry": job_result.industries,
                    "gender": job_result.gender,
                    "job_type": job_result.job_type,
                    "skills": job_result.skills,
                    "received_job_time": job_result.received_job_time,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
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
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,      
                    #   Working localtion                       
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country,
                    "point": job_result.point,
                    "correspone_price": job_result.correspone_price,
                    "warranty_time": job_result.warranty_time
                }
            else:
                pass
                
        @staticmethod
        def is_active_job(data: schema.RecruitPauseJob, db_session: Session):
            job = General.get_job_by_id(data.job_id, db_session)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found!")
            job.is_active = data.is_active
            db.commit_rollback(db_session)
                
    
    class Resume:

        @staticmethod
        def list_candidate(state: schema.CandidateState, db_session: Session): 
            
            if state == schema.CandidateState.all:
                resume_results = db_session.execute(select(model.ResumeVersion)    \
                                                .where(model.ResumeVersion.is_lastest == True)).scalars().all()
                return [{
                        "id": result.cv_id,
                        "fullname": result.name,
                        "job_title": result.current_job,
                        "industry": result.industry,
                        "status": result.status,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "referred_time": result.created_at
                    } for result in resume_results]
            
            elif state == schema.CandidateState.new_candidate:
                results = db_session.execute(select(model.RecruitResumeJoin, model.ResumeVersion)    \
                                                .join(model.ResumeVersion, not_(model.RecruitResumeJoin.resume_id == model.ResumeVersion.cv_id))    \
                                                .filter(model.ResumeVersion.is_lastest == True)).all()
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "status": result.ResumeVersion.status,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            elif state == schema.CandidateState.choosen_candidate:
                results = db_session.execute(select(model.RecruitResumeJoin, model.ResumeVersion)   \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.RecruitResumeJoin.resume_id)  \
                                                .filter(or_(model.RecruitResumeJoin.package == schema.ResumePackage.basic,
                                                           model.RecruitResumeJoin.package == schema.ResumePackage.platinum))    \
                                                .where(model.ResumeVersion.is_lastest == True)).all()
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "status": result.ResumeVersion.status,
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            elif state == schema.CandidateState.inappro_candidate:
                results = db_session.execute(select(model.RecruitResumeJoin, model.ResumeVersion)   \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.RecruitResumeJoin.resume_id)  \
                                                .filter(model.RecruitResumeJoin.is_rejected == True)    \
                                                .where(model.ResumeVersion.is_lastest == True)).all()
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "status": result.ResumeVersion.status,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            else:
                pass
                
                
        @staticmethod
        def get_detail_candidate(request: Request, candidate_id, db_session, current_user):
            resume_result = General.get_detail_resume_by_id(candidate_id, db_session) 
            if not resume_result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Get resume information of a specific recruiter
            choosen_result = db_session.execute(select(model.RecruitResumeJoin).where(and_(model.RecruitResumeJoin.user_id == current_user.id,
                                                                                           model.RecruitResumeJoin.resume_id == candidate_id))).scalars().first()
            
            educations = db_session.execute(select(model.ResumeEducation).where(model.ResumeEducation.cv_id == candidate_id)).scalars().all()
            experience = db_session.execute(select(model.ResumeExperience).where(model.ResumeExperience.cv_id == candidate_id)).scalars().all()
            projects = db_session.execute(select(model.ResumeProject).where(model.ResumeProject.cv_id == candidate_id)).scalars().all()
            awards = db_session.execute(select(model.ResumeAward).where(model.ResumeAward.cv_id == candidate_id)).scalars().all()
            lang_certs = db_session.execute(select(model.LanguageResumeCertificate).where(model.LanguageResumeCertificate.cv_id == candidate_id)).scalars().all()
            other_certs = db_session.execute(select(model.OtherResumeCertificate).where(model.OtherResumeCertificate.cv_id == candidate_id)).scalars().all()
            
            if not choosen_result:
                return {
                    "cv_id": candidate_id,
                    "status": resume_result.ResumeVersion.status,
                    "job_service": job_result.job_service,
                    "cv_point": General.get_resume_valuate(candidate_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), "static/resume/avatar/default_avatar.png"),
                    "candidate_name": "Họ và tên",
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "skills": resume_result.ResumeVersion.skills,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "email": "example@gmail.com",
                    "phone": "0348*****58",
                    "identification_code": "0522*******2325",
                    "address": "_________________",
                    "city": "_________________",
                    "country": "_________________",
                    "linkedin": "_________________",
                    "website": "_________________",
                    "facebook": "_________________",
                    "instagram": "_________________",
                    "experience": [{
                        "job_title": exper.job_title,
                        "company_name": exper.company_name,
                        "start_time": exper.start_time,
                        "end_time": exper.end_time,
                        "levels": exper.levels,  #   Cấp bậc đảm nhiêm 
                        "roles": exper.roles,    #   Vai trò đảm nhiệm
                    } for exper in experience],
                    "educations": [{
                        "institute": edu.institute_name,
                        "degree": edu.degree,
                        "gpa": edu.gpa,
                        "major": edu.major,
                        "start_time": edu.start_time,
                        "end_time": edu.end_time,
                    } for edu in educations],
                    "projects": [{
                        "project_name": project.project_name,
                        "descriptions": project.descriptions,
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
                            "certificate_level": lang_cert.certificate_point_level
                        } for lang_cert in lang_certs],
                        "other_certificate": [{
                            "certificate_name": other_cert.certificate_name,
                            "certificate_level": other_cert.certificate_point_level
                        } for other_cert in other_certs]
                    }
                }
            elif (choosen_result.package == schema.ResumePackage.basic) or (choosen_result == schema.ResumePackage.platinum and resume_result.ResumeVersion.status == schema.ResumeStatus.candidate_accepted_interview):
                return {
                    "cv_id": candidate_id,
                    "status": resume_result.ResumeVersion.status,
                    "job_service": job_result.job_service,
                    "cv_point": General.get_resume_valuate(candidate_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), resume_result.ResumeVersion.avatar),
                    "candidate_name": resume_result.ResumeVersion.name,
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "email": resume_result.ResumeVersion.email,
                    "skills": resume_result.ResumeVersion.skills,
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
                        "job_title": exper.job_title,
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
                        "descriptions": project.descriptions,
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
                            "certificate_level": lang_cert.certificate_point_level
                        } for lang_cert in lang_certs],
                        "other_certificate": [{
                            "certificate_name": other_cert.certificate_name,
                            "certificate_level": other_cert.certificate_point_level
                        } for other_cert in other_certs]
                    },
                    "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)
                }
            else:
                pass
            
        #   Collaborator reject resume
        @staticmethod
        def reject_resume(data: schema.RecruitRejectResume, db_session: Session, current_user):
            rejected_db = model.RecruitResumeJoin(
                                            user_id=current_user.id,    #   Current recruiter's account
                                            resume_id=data.cv_id,
                                            is_rejected=True,
                                            decline_reason=data.decline_reason
            )           
            db_session.add(rejected_db)
            db.commit_rollback(db_session)
            
        @staticmethod
        def remove_rejected_resume(data: schema.ResumeIndex, db_session: Session, current_user):
            rejected_db = db_session.execute(select(model.RecruitResumeJoin).where(
                                                model.RecruitResumeJoin.user_id==current_user.id,    #   Current recruiter's account
                                                model.RecruitResumeJoin.resume_id==data.cv_id,
                                                model.RecruitResumeJoin.is_rejected==True)).scalars().first()      
            db_session.delete(rejected_db)
            db.commit_rollback(db_session)
            
            
        @staticmethod
        def choose_candidate(cv_id: int, background_taks: BackgroundTasks, db_session: Session, current_user):
            #   Check wheather recruiter's point is available
            valuation_result = General.get_resume_valuate(cv_id, db_session)
            job = General.get_job_from_resume(cv_id, db_session)
            if current_user.point < job.headunt_point:
                raise HTTPException(status_code=500, 
                                    detail=f"You are {valuation_result.total_point*10 - current_user.point} points short when using this service. Please add more points")
            resume_db = model.RecruitResumeJoin(
                                        user_id=current_user.id,    #   Current recruiter's account
                                        resume_id=cv_id,
                                        remain_warantty_time=job.warranty_time
            )           
            db_session.add(resume_db) 
            #   Update point of recruiter's account
            current_user.point -=  job.headhunt_point
            #   Update point of collaborator's account
            resume = General.get_detail_resume_by_id(cv_id, db_session)
            collab = db_session.execute(select(model.User).where(model.User.id == resume.Resumme.user_id)).scalars().first()
            collab.warranty_point += job.headhunt_point
            resume.ResumeVersion.point_recieved_time = datetime.now()
            db.commit_rollback(db_session)
            #   Start calculate the remaining warranty time
            background_taks.add(General.count_remaining_days, 
                                resume,
                                job.headhunt_point, 
                                collab, 
                                db_session)
            
        
        @staticmethod
        def schedule_booking(data: schema.InterviewBooking, db_session: Session, current_user):
            #   Save interview schedule
            schedule_db = model.InterviewSchedule(
                                        user_id=current_user.id,
                                        candidate_id=data.cv_id,
                                        date=data.date,
                                        location=data.location,
                                        start_time=data.start_time,
                                        end_time=data.end_time,
                                        note=data.note
            )
            db_session.add(schedule_db)
            #   Update Resume status
            resume = General.get_detail_resume_by_id(data.cv_id, db_session)
            resume.ResumeVersion.sstatus = schema.ResumeStatus.waiting_accept_interview_booking
            db.commit_rollback(db_session)
            
        
        @staticmethod
        def send_test(data: schema.TestSending, 
                      background_tasks: BackgroundTasks, 
                      db_session: Session):
            #   Get candidate information: 
            resume = General.get_detail_resume_by_id(data.cv_id, db_session)
        
            #   Send mail and save information to DB
            with open(os.path.join("data", data.test_file.filename), 'w+b') as file:
                shutil.copyfileobj(data.test_file.file, file)
            # Use background task to send email in the background
            message = f"""
            Xin chào {resume.ResumeVersion.name}.
            
            Email nhận trả lời test: {data.recruit_email}
            
            Bạn có một nội dung phỏng vấn được gửi từ nhà tuyển dụng.
            
            Chú ý: 
                {data.note}

            Cảm ơn.
            """
            #   Get collaborator information
            collab = db_session.execute(select(model.User).where(model.User.id == resume.Resume.user_id)).scalars().first()
            background_tasks.add_task(GoogleService.CONTENT_GOOGLE, msg=message, file_path=os.path.join("static/resume/cv/send_test", data.test_file.filename), input_email=collab.email)
            resume = General.get_detail_resume_by_id(data.cv_id, db_session)
            resume.ResumeVersion.sstatus = schema.ResumeStatus.waiting_accept_interview_test
            db.commit_rollback(db_session)
            return {"message": "Email will be sent in the background."}
            
        
        @staticmethod
        def phone(cv_id: int, db_session: Session):
            resume = General.get_detail_resume_by_id(cv_id, db_session)
            resume.ResumeVersion.status = schema.ResumeStatus.waiting_accept_interview_phone
            db.commit_rollback(db_session)
            return resume.ResumeVersion.email
            

        @staticmethod
        def get_candidate_reply_interview(cv_id: int, reply_status: schema.CandidateMailReply, db_session: Session):
            resume_result = General.get_detail_resume_by_id(cv_id, db_session)       
            if not resume_result.ResumeVersion.filename:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not find Resume")            
            #   Update resume status 
            if reply_status == schema.CandidateMailReply.accept:
                resume_result.ResumeVersion.status = schema.ResumeStatus.candidate_accepted_interview
            else:
                resume_result.ResumeVersion.status = schema.ResumeStatus.candidate_rejected_interview                
            db.commit_rollback(db_session)
    
    
class Admin:
    
    class Job: 
        
        @staticmethod
        def list_job_status(request: Request, status: SystemError, db_session: Session):
            job_query = select(model.User, model.JobDescription, model.Company, func.count(model.Resume.id).label("resume_count"))  \
                                .join(model.Company, model.Company.user_id == model.User.id)    \
                                .join(model.JobDescription, model.JobDescription.user_id == model.User.id)     \
                                .join(model.Resume, (model.Resume.job_id == model.JobDescription.id) & (model.Resume.user_id == model.User.id), isouter=True)   \
                                .group_by(model.User.id, model.JobDescription.id, model.Company.id)     \
                                .where(model.JobDescription.status == status)
            results = db_session.execute(job_query).all() 
            if not results:
                return []
            if status == schema.JobStatus.pending or status == schema.JobStatus.reviewing:   #  Chờ duyệt - Đang duyệt
                return [{
                    "job_id": result.JobDescription.id,
                    "company_logo": os.path.join(str(request.base_url), result.Company.logo),
                    "company_name": result.Company.company_name,
                    "job_title": result.JobDescription.job_title,
                    "created_date": result.JobDescription.created_at,
                    "industries": result.JobDescription.industries,
                    "status": result.JobDescription.status,
                    "job_service": result.JobDescription.job_service if result.JobDescription.job_service else "SearchCV" 
                } for result in results]                
            else:       #  Đang tuyen - Đã tủyển
                return [{
                    "job_id": result.JobDescription.id,
                    "company_logo": os.path.join(str(request.base_url), result.Company.logo),
                    "company_name": result.Company.company_name,
                    "job_title": result.JobDescription.job_title,
                    "recruited_date": result.JobDescription.created_at,
                    "industries": result.JobDescription.industries,
                    "status": result.JobDescription.status,
                    "job_service": result.JobDescription.job_service if result.JobDescription.job_service else "SearchCV",
                    "num_cv": result[-1]
                } for result in results]
            
            
        @staticmethod
        def get_detail_job_status(job_id, db_session, user):
            #   Get Job information
            job_result = General.get_job_by_id(job_id, db_session)
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Company
            company_query = select(model.Company).where(model.Company.id == job_result.company_id)
            company_result = db_session.execute(company_query).scalars().first() 
            if not company_result:
                raise HTTPException(status_code=404, detail="Company doesn't exist!")

            job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
            lang_certs = db_session.execute(select(model.LanguageJobCertificate).where(model.LanguageJobCertificate.job_id == job_id)).scalars().all()
            other_certs = db_session.execute(select(model.OtherJobCertificate).where(model.OtherJobCertificate.job_id == job_id)).scalars().all()
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            
            if job_result.status==schema.JobStatus.pending:
                return {
                    "status": job_result.status,
                    "job_service": job_result.job_service,
                    "job_title": job_result.job_title,
                    "industries": job_result.industries,
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country,
                    "job_type": job_result.job_type,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
                    "skills": job_result.skills,
                    "education": [{
                        "degree": edu.degree,
                        "major": edu.major,
                        "gpa": edu.gpa,
                    } for edu in job_edus],
                    "language_certificate": [{
                        "language": lang_cert.certificate_language,
                        "certificate_name": lang_cert.certificate_name,
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,
                    "received_job_time": job_result.received_job_time,
                    "levels": job_result.levels,
                    "roles": job_result.roles,
                    "yoe": job_result.yoe,
                    "num_recruit": job_result.num_recruit,
                    "admin_decline_reason": job_result.admin_decline_reason 
                }
            elif job_result.status==schema.JobStatus.reviewing:
                return {
                    "status": job_result.status,
                    "job_title": job_result.job_title,
                    "industries": job_result.industries,
                    "gender": job_result.gender,
                    "job_type": job_result.job_type,
                    "skills": job_result.skills,
                    "received_job_time": job_result.received_job_time,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
                    "levels": job_result.levels,
                    "roles": job_result.roles,
                    "yoe": {
                        "from": job_result.yoe.split("-")[0],
                        "to": job_result.yoe.split("-")[1]
                    },
                    "num_recruit": job_result.num_recruit,
                    "education": [{
                        "degree": edu.degree,
                        "major": edu.major,
                        "gpa": edu.gpa,
                    } for edu in job_edus],
                    "language_certificate": [{
                        "language": lang_cert.certificate_language,
                        "certificate_name": lang_cert.certificate_name,
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,                
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country
                }
            else:
                pass
            
        
        @staticmethod
        def save_temp_edit(data: int, db_session: Session):
            result = General.get_job_by_id(data.job_id, db_session)    
            if not result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Save edited information as a parquet JSON file
            try:
                save_dir = os.path.join(EDITED_JOB, f'{result.jd_file.split("/")[-1][:-4]}.json')
                with open(save_dir, 'w') as f:
                    json.dump(json.loads(data.json()), f)
            except:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This edit could not be saved")
            
            # Update Job status: 
            result.status = schema.JobStatus.reviewing
            db.commit_rollback(db_session)
        
    
        @staticmethod
        def review_job(data, db_session):
            result = General.get_job_by_id(data.job_id, db_session)    
            if not result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")        
            #   Admin duyet Job
            result.is_admin_approved = data.is_approved
            #   Update Job status
            if data.is_approved:
                result.status = schema.JobStatus.recruiting   # Đang tuyển
            elif not data.is_approved:
                result.status = schema.JobStatus.reviewing      # Đang duyệt
                result.admin_decline_reason = data.decline_reason
            db.commit_rollback(db_session)
            return result
                
                
        @staticmethod
        def is_active_job(data: schema.AdminPauseJob, db_session: Session):
            job = General.get_job_by_id(data.job_id, db_session)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found!")
            job.is_active = data.is_active
            db.commit_rollback(db_session)
            
            
    class Resume:
        
        @staticmethod
        def get_matching_result(cv_id: int, db_session: Session):
            #   Get resume information
            resume = General.get_detail_resume_by_id(cv_id, db_session)
            matching_query = select(model.ResumeMatching).where(model.ResumeMatching.cv_id == cv_id)
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
        def admin_review_matching(data: schema.AdminReviewMatching, db_session: Session):
            result = General.get_detail_resume_by_id(data.cv_id, db_session)    
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")        
            #   Admin review matching results from AI, <=> status == "pricing_approved"
            if result.ResumeVersion.status != schema.ResumeStatus.candidate_accepted:
                raise HTTPException(status_code=503, detail=f"Your resume status needed to be '{schema.ResumeStatus.candidate_accepted}' before matching reviewed!")
            if data.resume_status.accept:
                result.ResumeVersion.status = schema.ResumeStatus.admin_matching_approved
            else:
                result.ResumeVersion.status = schema.ResumeStatus.admin_matching_rejected
                result.ResumeVersion.matching_decline_reason = data.decline_reason
            db.commit_rollback(db_session)
            
        
        @staticmethod
        def list_candidate(state: str, db_session: Session):
            if state == schema.CandidateStatus.all:
                results = db_session.execute(select(model.Resume, model.ResumeVersion)    \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id)    \
                                                .filter(model.ResumeVersion.is_lastest == True)).all()
                if not results:
                    raise HTTPException(status_code=404, detail="Could not find any relevant candidates!")
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "status": result.ResumeVersion.status,
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            
            elif state == schema.CandidateStatus.pending:
                results =  db_session.execute(select(model.Resume, model.ResumeVersion)    \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id)    \
                                                .filter(and_(model.ResumeVersion.is_lastest == True,
                                                             model.ResumeVersion.status == schema.ResumeStatus.candidate_accepted))).all()
                if not results:
                    raise HTTPException(status_code=404, detail="Could not find any relevant candidates!")
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersionname,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "status": result.ResumeVersion.status,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            elif state == schema.CandidateStatus.approved:
                results =  db_session.execute(select(model.Resume, model.ResumeVersion)    \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id)    \
                                                .filter(and_(model.ResumeVersion.is_lastest == True,
                                                             model.ResumeVersion.is_ai_matched == True))).all()
                if not results:
                    raise HTTPException(status_code=404, detail="Could not find any relevant candidates!")
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "status": result.ResumeVersion.status,
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            elif state == schema.CandidateStatus.declined:
                results =  db_session.execute(select(model.Resume, model.ResumeVersion)    \
                                                .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id)    \
                                                .filter(and_(model.ResumeVersion.is_lastest == True,
                                                            model.ResumeVersion.is_ai_matched == False))).all()
                if not results:
                    raise HTTPException(status_code=404, detail="Could not find any relevant candidates!")
                return [{
                        "id": result.ResumeVersion.cv_id,
                        "fullname": result.ResumeVersion.name,
                        "job_title": result.ResumeVersion.current_job,
                        "industry": result.ResumeVersion.industry,
                        "status": result.ResumeVersion.status,
                        "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            else:
                pass
            

        @staticmethod
        def get_detail_candidate(request: Request, cv_id: int, db_session: Session):
            
            resume_result = General.get_detail_resume_by_id(cv_id, db_session) 
            if not resume_result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)
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
                    "cv_point": General.get_resume_valuate(cv_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), resume_result.ResumeVersion.avatar),
                    "candidate_name": resume_result.ResumeVersion.name,
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "email": resume_result.ResumeVersion.email,
                    "skills": resume_result.ResumeVersion.skills,
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
                        "job_title": exper.job_title,
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
                        "descriptions": project.descriptions,
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
                            "certificate_level": lang_cert.certificate_point_level
                        } for lang_cert in lang_certs],
                        "other_certificate": [{
                            "certificate_name": other_cert.certificate_name,
                            "certificate_level": other_cert.certificate_point_level
                        } for other_cert in other_certs]
                    },
                    "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)
                }
            
        
        @staticmethod
        def list_all_company(db_session: Session):
            query = select(model.User, model.Company, model.JobDescription)     \
                            .join(model.Company, model.User.id == model.Company.user_id)    \
                            .join(model.JobDescription, model.User.id == model.JobDescription.user_id)
            results = db_session.execute(query).all()
            if not results:
                raise HTTPException(status_code=404, detail="Could not find any company!")
            return [{
                "company_logo": result.logo,
                "company_name": result.company_name,
                "industry": result.industry,
                "address": result.address,
                "phone": result.phone,
                "email": result.email,
                "website": result.website,
                "phone": result.phone,
                "job_service": result.job_service,
                
            } for result in results]      
                
    
    
class Collaborator:
    
    class Job:    
        
        @staticmethod
        def get_detail_job(request, job_id, db_session):
            #   Job
            job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
            job_result = db_session.execute(job_query).scalars().first() 
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Company
            company_query = select(model.Company).where(model.Company.id == job_result.company_id)
            company_result = db_session.execute(company_query).scalars().first() 
            if not company_result:
                raise HTTPException(status_code=404, detail="Company doesn't exist!")

            job_edus = db_session.execute(select(model.JobEducation).where(model.JobEducation.job_id == job_id)).scalars().all()
            lang_certs = db_session.execute(select(model.LanguageJobCertificate).where(model.LanguageJobCertificate.job_id == job_id)).scalars().all()
            other_certs = db_session.execute(select(model.OtherJobCertificate).where(model.OtherJobCertificate.job_id == job_id)).scalars().all()
            
            return {
                    "company_logo": os.path.join(str(request.base_url), company_result.logo) if company_result.logo else None,
                    "company_name": company_result.company_name,
                    "company_cover_image": os.path.join(str(request.base_url), company_result.cover_image) if company_result.cover_image else None,
                    "status": job_result.status,
                    "job_service": job_result.job_service,
                    "job_title": job_result.job_title,
                    "industry": job_result.industries,
                    "gender": job_result.gender,
                    "job_type": job_result.job_type,
                    "skills": job_result.skills,
                    "received_job_time": job_result.received_job_time,
                    "working_time": {
                                "week": job_result.working_time.split(',')[0],
                                "startTime": job_result.working_time.split(',')[1],
                                "Time": job_result.working_time.split(',')[2]
                    },
                    "descriptions": General.string_parse(job_result.descriptions),
                    "requirements": General.string_parse(job_result.requirements),
                    "benefits": General.string_parse(job_result.benefits),
                    "levels": job_result.levels,
                    "roles": job_result.roles,
                    "num_recruit": job_result.num_recruit,
                    "education": [{
                        "degree": edu.degree,
                        "major": edu.major,
                        "gpa": edu.gpa,
                    } for edu in job_edus],
                    "language_certificate": [{
                        "language": lang_cert.certificate_language,
                        "certificate_name": lang_cert.certificate_name,
                        "certificate_level": lang_cert.certificate_point_level,
                    } for lang_cert in lang_certs],
                    "other_certificate": [{
                        "certificate_name": cert.certificate_name,
                        "certificate_level": cert.certificate_point_level,
                    } for cert in other_certs],
                    "min_salary": job_result.min_salary,
                    "max_salary": job_result.max_salary,      
                    #   Working localtion                       
                    "address": job_result.address,
                    "city": job_result.city,
                    "country": job_result.country
                }
            
        
        @staticmethod
        def add_favorite(job_id, db_session, user):
            result = General.get_job_by_id(job_id, db_session)    
            if not result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")        

            db_result = model.CollaboratorJobJoin(
                                    user_id=user.id,
                                    job_id=job_id,
                                    is_favorite=True
            )
            db_session.add(db_result)
            db.commit_rollback(db_session) 


        @staticmethod
        def list_job(request, job_status, db_session, current_user):
            #   ======================= Đã giới thiệu =======================
            if job_status == schema.CollaborateJobStatus.referred:
                query_referred = (
                            select(
                                model.Company.id.label("company_id"),
                                model.Company.logo, 
                                model.Company.company_name, 
                                model.JobDescription.id.label("job_id"),
                                model.JobDescription.job_title,
                                model.JobDescription.industries,
                                model.JobDescription.created_at,
                                model.JobDescription.job_service, 
                                model.JobDescription.status,
                                func.count(model.Resume.id)
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
                    return []
                return [{
                    "job_id": result[3],
                    "company_logo": os.path.join(str(request.base_url), result[1]),
                    "company_name": result[2],
                    "job_title": result[4],
                    "industries": result[5],
                    "job_service": result[7],
                    "status": result[8],
                    "num_cv": result[-1]
                } for result in result_referred]
            
            #  ======================= Favorite Jobs ======================= 
            
            elif job_status == schema.CollaborateJobStatus.favorite:                
                query_favorite = (
                            select(
                                model.Company.id.label("company_id"),
                                model.Company.logo,
                                model.Company.company_name, 
                                model.JobDescription.id.label("job_id"),
                                model.JobDescription.job_title,
                                model.JobDescription.industries,
                                model.JobDescription.created_at,
                                model.JobDescription.job_service, 
                                model.JobDescription.status
                            )
                            .join(model.Company, model.Company.user_id == model.JobDescription.user_id)
                            .join(model.CollaboratorJobJoin, and_(model.CollaboratorJobJoin.user_id == current_user.id, model.CollaboratorJobJoin.job_id == model.JobDescription.id))
                            .where(model.CollaboratorJobJoin.is_favorite == True)  # Assuming is_favorite is a boolean column
                        )
                result_favorite = db_session.execute(query_favorite).all() 
                if not result_favorite:
                    return []
                return [{
                    "job_id": result[3],
                    "company_logo": os.path.join(str(request.base_url), result[1]),
                    "company_name": result[2],
                    "job_title": result[4],
                    "industries": result[5],
                    "job_service": result[7],
                    "status": result[8]
                } for result in result_favorite]
            
            #  ======================= Chưa giới thiệu =======================
            elif job_status == schema.CollaborateJobStatus.unreferred:
                query_unreferred = (
                            select(
                                model.Company.id.label("company_id"),
                                model.Company.logo, 
                                model.Company.company_name, 
                                model.JobDescription.id.label("job_id"),
                                model.JobDescription.job_title,
                                model.JobDescription.industries,
                                model.JobDescription.created_at,
                                model.JobDescription.job_service, 
                                model.JobDescription.status
                            )
                            .join(model.JobDescription, model.Company.user_id == model.JobDescription.user_id)
                            .outerjoin(model.Resume, model.JobDescription.id == model.Resume.job_id)
                            # .outerjoin(model.CollaboratorJobJoin, and_(model.CollaboratorJobJoin.user_id == current_user.id, 
                            #                                            model.CollaboratorJobJoin.job_id == model.JobDescription.id))
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
                            # .filter(and_(model.CollaboratorJobJoin.is_favorite == False)
                )
                result_unreferred = db_session.execute(query_unreferred).all() 
                if not result_unreferred:
                    return []
                return [{
                    "job_id": result[3],
                    "company_logo": os.path.join(str(request.base_url), result[1]),
                    "company_name": result[2],
                    "job_title": result[4],
                    "industries": result[5],
                    "job_service": result[7],
                    "status": result[8],
                } for result in result_unreferred]
            else:
                pass
    
    
    class Resume:    
        @staticmethod
        def parse_base(store_path: str, filename: str):
            #   Check duplicated filename
            if not DatabaseService.check_file_duplicate(filename, CV_EXTRACTION_PATH):
                prompt_template = Extraction.cv_parsing_template(store_path=store_path, filename=filename)

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
        def cv_parsing(cv_id: int, db_session: Session, user):
            result = General.get_detail_resume_by_id(cv_id, db_session, user)       
            if not result.ResumeVersion.filename:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload at least 1 CV_PDF")
            return Collaborator.Resume.parse_base(CV_SAVED_DIR, result.ResumeVersion.filename)
    

        @staticmethod
        def add_candidate(background_tasks: BackgroundTasks, data: schema.AddCandidate, db_session: Session):
            #   PDF uploaded file validation        
            if data.cv_pdf.content_type != 'application/pdf':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file") 
            cleaned_filename = DatabaseService.clean_filename(data.cv_pdf.filename)

            #   Save CV file as temporary
            with open(os.path.join(CV_SAVED_TEMP_DIR, cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data.cv_pdf.file, file)
            
            background_tasks.add_task(Collaborator.Resume.parse_base, CV_SAVED_TEMP_DIR, cleaned_filename)
            # extracted_result = background_task_results['extracted_result']
            extracted_result, _ = Collaborator.Resume.parse_base(CV_SAVED_TEMP_DIR, cleaned_filename)
            #   Check duplicated CVs
            DatabaseService.check_db_duplicate(extracted_result["contact_information"], cleaned_filename, db_session)
            #   Save Resume's basic information to DB
            os.remove(os.path.join(CV_SAVED_TEMP_DIR, cleaned_filename))
            return extracted_result
        
        
        @staticmethod
        def fill_resume(data_form: schema.FillResume,
                        db_session: Session,
                        user):      
            #   Save UploadedFile first
            cleaned_filename = DatabaseService.clean_filename(data_form.cv_file.filename)
            resume_db = model.Resume(
                                user_id=user.id,
                                job_id=data_form.job_id,
                            )       
            db_session.add(resume_db)
            db.commit_rollback(db_session)
            version_db = model.ResumeVersion(
                                cv_id=resume_db.id,
                                filename=cleaned_filename,
                                skills=[skill[1:-1] for skill in data_form.skills[0][1:-1].split(",")],
                                avatar=os.path.join("static/resume/avatar", data_form.avatar.filename),
                                cv_file=os.path.join("static/resume/cv/uploaded_cvs", cleaned_filename)
            )
            db_session.add(version_db)
            db.commit_rollback(db_session)
            #   Save CV file
            with open(os.path.join(CV_SAVED_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data_form.cv_file.file, file) 
            #   Save avatar image
            with open(os.path.join("static/resume/avatar",  data_form.avatar.filename), 'w+b') as file:
                shutil.copyfileobj(data_form.avatar.file, file) 
                
            result = General.get_detail_resume_by_id(resume_db.id, db_session) 
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")

            #   If the resume never existed in System => add to Database
            for key, value in dict(data_form).items():
                if value is not None and key not in [
                                                "job_id",
                                                "avatar",
                                                "cv_file",
                                                "education",
                                                "work_experiences",
                                                "awards",
                                                "skills",
                                                "projects",
                                                "language_certificates",
                                                "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
            if data_form.education:
                edus = [model.ResumeEducation(cv_id=resume_db.id, **education) for education in General.json_parse(data_form.education[0])]
                db_session.add_all(edus)
            if data_form.work_experiences:
                expers = [model.ResumeExperience(cv_id=resume_db.id, **exper) for exper in General.json_parse(data_form.work_experiences[0])]
                db_session.add_all(expers)
            if data_form.awards:
                awards = [model.ResumeAward(cv_id=resume_db.id, **award) for award in General.json_parse(data_form.awards[0])]
                db_session.add_all(awards)
            if data_form.projects:
                projects = [model.ResumeProject(cv_id=resume_db.id, **project) for project in General.json_parse(data_form.projects[0])]
                db_session.add_all(projects)
            if data_form.language_certificates:
                lang_certs = [model.LanguageResumeCertificate(cv_id=resume_db.id, **lang_cert) for lang_cert in General.json_parse(data_form.language_certificates[0])]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherResumeCertificate(cv_id=resume_db.id, **other_cert) for other_cert in General.json_parse(data_form.other_certificates[0])]
                db_session.add_all(other_certs)
                
            db.commit_rollback(db_session) 
            return resume_db, version_db
        
        
        @staticmethod
        def update_resume_info(data_form: schema.UpdateResume, db_session: Session):      
            #   Save UploadedFile first
            result = db_session.execute(model.ResumeVersion).where(model.ResumeVersion.cv_id == data_form.cv_id).scalars().first()
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            if data_form.avatar:
                #  Delete old avatar and save the new one\
                if result.avatar:
                    os.remove(result.avatar) 
                result.avatar = os.path.join("static/resume/avatar", data_form.avatar.filename)
                with open(os.path.join("static/resume/avatar",  data_form.avatar.filename), 'w+b') as file:
                    shutil.copyfileobj(data_form.avatar.file, file) 
            if data_form.cv_file:
                cleaned_filename = DatabaseService.clean_filename(data_form.cv_file.filename)
                result.filename = cleaned_filename
                #  Delete old avatar and save the new one
                if result.cv_file:
                    os.remove(result.cv_file)
                result.cv_file = os.path.join(CV_SAVED_DIR, cleaned_filename)
                with open(os.path.join(CV_SAVED_DIR,  cleaned_filename), 'w+b') as file:
                    shutil.copyfileobj(data_form.cv_file.file, file) 
            if data_form.skills:
                result.skills = [skill[1:-1] for skill in data_form.skills[0][1:-1].split(",")]

            #   If the resume never existed in System => add to Database
            for key, value in dict(data_form).items():
                if value is not None and key not in [
                                                "cv_id",
                                                "avatar",
                                                "cv_file",
                                                "education",
                                                "work_experiences",
                                                "awards",
                                                "skills",
                                                "projects",
                                                "language_certificates",
                                                "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
            if data_form.education:
                edus = [model.ResumeEducation(cv_id=data_form.cv_id, **education) for education in General.json_parse(data_form.education[0])]
                db_session.add_all(edus)
            if data_form.work_experiences:
                expers = [model.ResumeExperience(cv_id=data_form.cv_id, **exper) for exper in General.json_parse(data_form.work_experiences[0])]
                db_session.add_all(expers)
            if data_form.awards:
                awards = [model.ResumeAward(cv_id=data_form.cv_id, **award) for award in General.json_parse(data_form.awards[0])]
                db_session.add_all(awards)
            if data_form.projects:
                projects = [model.ResumeProject(cv_id=data_form.cv_id, **project) for project in General.json_parse(data_form.projects[0])]
                db_session.add_all(projects)
            if data_form.language_certificates:
                lang_certs = [model.LanguageResumeCertificate(cv_id=data_form.cv_id, **lang_cert) for lang_cert in General.json_parse(data_form.language_certificates[0])]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherResumeCertificate(cv_id=data_form.cv_id, **other_cert) for other_cert in General.json_parse(data_form.other_certificates[0])]
                db_session.add_all(other_certs)
                
            db.commit_rollback(db_session) 
        

        @staticmethod
        def resume_valuate(data: schema.FillResume, resume_db: model.Resume, db_session: Session):
            #   Add "hard_point" initialization
            hard_point = 0
            for level, point in level_map.items():
                if data.level in levels[int(level)]:
                    hard_point += point

            #   ============================== Soft point ==============================
            #   Degrees
            degree_point = 0
            degrees = []
            if data.education:
                for education in General.json_parse(data.education[0]):
                    if education["degree"] in ["Bachelor", "Master", "Ph.D"]:
                        degrees.append(education["degree"])
                degree_point = 0.5 * len(degrees)
            #   Certificates
            certs_point = 0
            cert_lst = []
            if data.language_certificates:
                for cert in General.json_parse(data.language_certificates[0]):
                    if cert['certificate_language']=='N/A' or cert['certificate_name']=='N/A' or cert['certificate_point_level']=='N/A': 
                        continue
                    if cert['certificate_language'] == "English":
                        if (cert['certificate_name'] == "TOEIC" and float(cert['certificate_point_level']) > 700) or (cert['certificate_name'] == "IELTS" and float(cert['certificate_point_level']) > 7.0):
                            cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Japan" and cert['certificate_point_level'] in ["N1", "N2"]:
                        cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Korean":
                        if cert['certificate_name'] == "Topik_II" and cert['certificate_point_level'] in ["Level 5", "Level 6"]:
                            cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Chinese" and cert['certificate_point_level'] == ["HSK-5", "HSK-6"]:
                        cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                certs_point = 0.5 * len(cert_lst)

            #   Save valuation result to Db
            valuate_db = model.ValuationInfo(
                                    cv_id=resume_db.id,
                                    hard_item=data.level,
                                    hard_point=hard_point,
                                    degrees=degrees,
                                    degree_point=degree_point,
                                    certificates=[str(cert_dict) for cert_dict in cert_lst],
                                    certificates_point=certs_point,
                                    total_point=hard_point + degree_point + certs_point
            )
            db_session.add(valuate_db)
            #   Update Resume valuation status
            resume = General.get_detail_resume_by_id(resume_db.id, db_session)
            resume.ResumeVersion.status = schema.ResumeStatus.pricing_approved
            db.commit_rollback(db_session)
            return {
                "cv_id": valuate_db.cv_id,
                "hard_item": valuate_db.hard_item,
                "hard_point": valuate_db.hard_point,
                "degrees": valuate_db.degrees,
                "degree_point": valuate_db.degree_point,
                "certificates": valuate_db.certificates,
                "certificates_point": valuate_db.certificates_point,
                "total_point": valuate_db.total_point
            }
        
        
        @staticmethod
        def fill_resume_dummy(data_form: schema.FillResume,
                        db_session: Session,
                        user):      
            #   Save UploadedFile first
            cleaned_filename = DatabaseService.clean_filename(data_form.cv_file.filename)
            resume_db = model.Resume(
                                user_id=user.id,
                                job_id=data_form.job_id,
                            )       
            db_session.add(resume_db)
            db.commit_rollback(db_session)
            version_db = model.ResumeVersion(
                                cv_id=resume_db.id,
                                filename=cleaned_filename,
                                avatar=os.path.join("static/resume/avatar", data_form.avatar.filename),
                                cv_file=os.path.join("static/resume/cv/uploaded_cvs", cleaned_filename)
            )
            db_session.add(version_db)
            db.commit_rollback(db_session)
            #   Save CV file
            with open(os.path.join(CV_SAVED_TEMP_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data_form.cv_file.file, file) 
            #   Save avatar image
            with open(os.path.join("static/resume/avatar",  data_form.avatar.filename), 'w+b') as file:
                shutil.copyfileobj(data_form.avatar.file, file) 
                
            result = General.get_detail_resume_by_id(resume_db.id, db_session) 
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")

            #   If the resume never existed in System => add to Database
            for key, value in dict(data_form).items():
                if value is not None and key not in [
                                                "job_id",
                                                "avatar",
                                                "cv_file",
                                                "education",
                                                "work_experiences",
                                                "awards",
                                                "projects",
                                                "language_certificates",
                                                "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
            if data_form.education:
                edus = [model.ResumeEducation(cv_id=resume_db.id, **json.loads(education[1:-1])) for education in data_form.education]
                db_session.add_all(edus)
            if data_form.work_experiences:
                expers = [model.ResumeExperience(cv_id=resume_db.id, **json.loads(exper[1:-1])) for exper in data_form.work_experiences]
                db_session.add_all(expers)
            if data_form.awards:
                awards = [model.ResumeAward(cv_id=resume_db.id, **json.loads(award[1:-1])) for award in data_form.awards]
                db_session.add_all(awards)
            if data_form.projects:
                projects = [model.ResumeProject(cv_id=resume_db.id, **json.loads(project[1:-1])) for project in data_form.projects]
                db_session.add_all(projects)
            if data_form.language_certificates:
                lang_certs = [model.LanguageResumeCertificate(cv_id=resume_db.id, **json.loads(lang_cert[1:-1])) for lang_cert in data_form.language_certificates]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherResumeCertificate(cv_id=resume_db.id, **json.loads(other_cert[1:-1])) for other_cert in data_form.other_certificates]
                db_session.add_all(other_certs)
                
            db.commit_rollback(db_session) 
            return resume_db, version_db
        

        @staticmethod
        def resume_valuate_dummy(data: schema.FillResume, resume_db: model.Resume, db_session: Session):
            #   Add "hard_point" initialization
            hard_point = 0
            for level, point in level_map.items():
                if data.level in levels[int(level)]:
                    hard_point += point

            #   ============================== Soft point ==============================
            #   Degrees
            degree_point = 0
            degrees = []
            if data.education:
                for education in data.education:
                    education = json.loads(education[1:-1])
                    if education["degree"] in ["Bachelor", "Master", "Ph.D"]:
                        degrees.append(education["degree"])
                degree_point = 0.5 * len(degrees)
            #   Certificates
            certs_point = 0
            cert_lst = []
            if data.language_certificates:
                for cert in data.language_certificates:
                    cert = json.loads(cert[1:-1])
                    if cert['certificate_language']=='N/A' or cert['certificate_name']=='N/A' or cert['certificate_point_level']=='N/A': 
                        continue
                    if cert['certificate_language'] == "English":
                        if (cert['certificate_name'] == "TOEIC" and float(cert['certificate_point_level']) > 700) or (cert['certificate_name'] == "IELTS" and float(cert['certificate_point_level']) > 7.0):
                            cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Japan" and cert['certificate_point_level'] in ["N1", "N2"]:
                        cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Korean":
                        if cert['certificate_name'] == "Topik_II" and cert['certificate_point_level'] in ["Level_5", "Level_6"]:
                            cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                    elif cert['certificate_language'] == "Chinese" and cert['certificate_point_level'] == ["HSK-5", "HSK-6"]:
                        cert_lst.append({
                                "certificate_language": cert['certificate_language'],
                                "certificate_name": cert['certificate_name'],
                                "certificate_point_level": cert['certificate_point_level']
                            })
                certs_point = 0.5 * len(cert_lst)

            #   Save valuation result to Db
            valuate_db = model.ValuationInfo(
                                    cv_id=resume_db.id,
                                    hard_item=data.level,
                                    hard_point=hard_point,
                                    degrees=degrees,
                                    degree_point=degree_point,
                                    certificates=[str(cert_dict) for cert_dict in cert_lst],
                                    certificates_point=certs_point,
                                    total_point=hard_point + degree_point + certs_point
            )
            db_session.add(valuate_db)
            #   Update Resume valuation status
            resume = General.get_detail_resume_by_id(resume_db.id, db_session)
            resume.ResumeVersion.status = schema.ResumeStatus.pricing_approved
            db.commit_rollback(db_session)
            return {
                "cv_id": valuate_db.cv_id,
                "hard_item": valuate_db.hard_item,
                "hard_point": valuate_db.hard_point,
                "degrees": valuate_db.degrees,
                "degree_point": valuate_db.degree_point,
                "certificates": valuate_db.certificates,
                "certificates_point": valuate_db.certificates_point,
                "total_point": valuate_db.total_point
            }
        
        
        @staticmethod
        def create_draft_resume(
                        data_form: schema.FillDraftResume,
                        db_session: Session,
                        user):      
            #   Save UploadedFile first
            cleaned_filename = DatabaseService.clean_filename(data_form.cv_file.filename)
            resume_db = model.Resume(
                                user_id=user.id,
                                job_id=data_form.job_id,
                            )       
            db_session.add(resume_db)
            db.commit_rollback(db_session)
            version_db = model.ResumeVersion(
                                cv_id=resume_db.id,
                                filename=cleaned_filename,
                                skills=[skill[1:-1] for skill in data_form.skills[0][1:-1].split(",")],
                                avatar=os.path.join("static/resume/avatar", data_form.avatar.filename),
                                cv_file=os.path.join("static/resume/cv/uploaded_cvs", cleaned_filename)
            )
            db_session.add(version_db)
            db.commit_rollback(db_session)
            #   Save CV file
            with open(os.path.join(CV_SAVED_DIR,  cleaned_filename), 'w+b') as file:
                shutil.copyfileobj(data_form.cv_file.file, file) 
            #   Save avatar image
            with open(os.path.join("static/resume/avatar",  data_form.avatar.filename), 'w+b') as file:
                shutil.copyfileobj(data_form.avatar.file, file) 
                
            result = General.get_detail_resume_by_id(resume_db.id, db_session) 
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")

            #   If the resume never existed in System => add to Database
            for key, value in dict(data_form).items():
                if value is not None and key not in [
                            "job_id",
                            "avatar",
                            "cv_file",
                            "education",
                            "work_experiences",
                            "awards",
                            "skills",
                            "projects",
                            "language_certificates",
                            "other_certificates"]:
                    setattr(result.ResumeVersion, key, value) 
            if data_form.education:
                edus = [model.ResumeEducation(cv_id=resume_db.id, **education) for education in General.json_parse(data_form.education[0])]
                db_session.add_all(edus)
            if data_form.work_experiences:
                expers = [model.ResumeExperience(cv_id=resume_db.id, **exper) for exper in General.json_parse(data_form.work_experiences[0])]
                db_session.add_all(expers)
            if data_form.awards:
                awards = [model.ResumeAward(cv_id=resume_db.id, **award) for award in General.json_parse(data_form.awards[0])]
                db_session.add_all(awards)
            if data_form.projects:
                projects = [model.ResumeProject(cv_id=resume_db.id, **project) for project in General.json_parse(data_form.projects[0])]
                db_session.add_all(projects)
            if data_form.language_certificates:
                lang_certs = [model.LanguageResumeCertificate(cv_id=resume_db.id, **lang_cert) for lang_cert in General.json_parse(data_form.language_certificates[0])]
                db_session.add_all(lang_certs)
            if data_form.other_certificates:
                other_certs = [model.OtherResumeCertificate(cv_id=resume_db.id, **other_cert) for other_cert in General.json_parse(data_form.other_certificates[0])]
                db_session.add_all(other_certs)
                
            db.commit_rollback(db_session) 
            return resume_db, version_db
        
        @staticmethod
        def percent_estimate(filename: str):
            prompt_template = Extraction.resume_percent_estimate(filename)      
            #   Start parsing
            extracted_result = OpenAIService.gpt_api(prompt_template)
            point = extracted_result["point"]
            return point/100
        

        @staticmethod
        def update_valuate(data: schema.UpdateResumeValuation, db_session: Session):
            result = General.get_detail_resume_by_id(data.cv_id, db_session) 
            if not result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == data.cv_id)
            valuate_result = db_session.execute(valuation_query).scalars().first()
            if not valuate_result:
                raise HTTPException(status_code=404, detail="This Resume has not been valuated!")
            
            #   Point initialization
            hard_point = 0
            if data.current_salary is not None:
                percent = Collaborator.Resume.percent_estimate(filename=result.ResumeVersion.filename)
                hard_point = round(percent*data.current_salary / 100000, 1)   # Convert money to point: 100000 (vnđ) => 1đ
                valuate_result.hard_item = data.current_salary
                valuate_result.hard_point = hard_point
                #   Commit to Database
                result.ResumeVersion.status = schema.ResumeStatus.pricing_approved
                db.commit_rollback(db_session)
            elif data.level:
                for level, point in level_map.items():
                    if data.level in levels[int(level)]:
                        hard_point += point
                        valuate_result.hard_item = data.level
                        valuate_result.hard_point = hard_point
                        #   Commit to Database
                        result.ResumeVersion.status = schema.ResumeStatus.pricing_approved
                        db.commit_rollback(db_session)
                        break
            else:
                pass

            #   ================================== Soft point ==================================
            #   Degrees
            degrees = []
            degree_point = 0
            if data.degrees:
                degrees = [degree for degree in data.degrees if degree in ["Bachelor", "Master", "Ph.D"]]
            #   Add "soft_point" to Database
            degree_point = 0.5 * len(degrees)
            valuate_result.degrees = degrees
            valuate_result.degree_point = degree_point
                
            #   Certificates
            certs = []                
            certs_point = 0
            if data.language_certificates:
                for cert in data.language_certificates:
                    if cert.certificate_language == "English":
                        if (cert.certificate_name == "TOEIC" and float(cert.certificate_point_level) > 700) or (cert.certificate_name == "IELTS" and float(cert.certificate_point_level) > 7.0):
                            certs.append(f"certificate_language='{cert.certificate_language}' certificate_name='{cert.certificate_name}' certificate_point_level='{cert.certificate_point_level}'")
                    elif cert.certificate_language == "Japan" and cert.certificate_point_level in ["N1", "N2"]:
                            certs.append(f"certificate_language='{cert.certificate_language}' certificate_name='{cert.certificate_name}' certificate_point_level='{cert.certificate_point_level}'")
                    elif cert.certificate_language == "Korean":
                        if cert.certificate_name == "Topik_II" and cert.certificate_point_level in ["Level_5", "Level_6"]:
                            certs.append(f"certificate_language='{cert.certificate_language}' certificate_name='{cert.certificate_name}' certificate_point_level='{cert.certificate_point_level}'")
                    elif cert.certificate_language == "Chinese" and cert.certificate_point_level == ["HSK-5", "HSK-6"]:
                            certs.append(f"certificate_language='{cert.certificate_language}' certificate_name='{cert.certificate_name}' certificate_point_level='{cert.certificate_point_level}'")
            certs_point = 0.5 * len(certs)
            #   Add "soft_point" to Database
            valuate_result.certificates = [str(cert) for cert in certs]
            valuate_result.certificates_point = certs_point
                    
            #   Update total_point
            valuate_result.total_point = hard_point + degree_point + certs_point
            #   Update Resume valuation status
            result.ResumeVersion.status = schema.ResumeStatus.pricing_approved
            db.commit_rollback(db_session)
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
        def send_email_request(
                            cv_id: int, 
                            mail_contents,
                            db_session: Session,
                            background_tasks: BackgroundTasks,
                            current_user):
            resume_data = General.get_detail_resume_by_id(cv_id, db_session)
            data = {
                "candidate": {
                        "email": resume_data.ResumeVersion.email,
                        "content": mail_contents["candidate"]
                },
                "collaborator": {
                        "email": current_user.email,
                        "content": mail_contents["collaborator"]
                },
            }
            try:                
                background_tasks.add_task(
                                    General.background_send_email,
                                    input_data=data)
            except:
                raise HTTPException(status_code=503, detail="Could not send email!")


        @staticmethod
        def cv_jd_matching(cv_id: int, db_session: Session, background_task: BackgroundTasks, current_user):
            resume_result = General.get_detail_resume_by_id(cv_id, db_session)       
            if not resume_result:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume does not exist")
            
            matched_result = db_session.execute(select(model.ResumeMatching).where(
                                                                                model.ResumeMatching.cv_id == cv_id,
                                                                                model.ResumeMatching.job_id == resume_result.Resume.job_id)).scalars().first()      
            if matched_result:
                raise HTTPException(status_code=409, detail="Resume is already matching evaluation")
            
            #   Get Job by cv_id
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)

            matching_result, saved_dir = Collaborator.Resume.matching_base(cv_filename=resume_result.ResumeVersion.filename, 
                                                            jd_filename=job_result.jd_file.split("/")[-1])
            
            overall_score = int(matching_result["overall"]["score"])
            if overall_score >= 50:
                candidate_content = f"""
                <html>
                    <body>
                        <p> Dear {resume_result.ResumeVersion.name}, <br>
                            Warm greetings from sharecv.vn !
                            Your profile has been recommended on sharecv.vn. However, please be aware that only when we have your permission, the profile will be sent to the employer to review and evaluate. <br>
                            Hence, please CLICK to below: <br>
                            - <a href="http://localhost:3000/accept?id={cv_id}">"Accept"</a> Job referral acceptance letter. <br>
                            - <a href="http://localhost:3000/decline?id={cv_id}">"Decline"</a> Job referral refusal letter. <br>
                            Thank you for your cooperation. Should you need any further information or assistance, please do not hesitate to contact us. <br>
                            Thanks and best regards, <br>
                            Team ShareCV Customer Support <br>
                            Hotline: 0888818006 – 0914171381 <br>
                            Email: info@sharecv.vn <br>
                            THANK YOU <br>
                        </p>
                            <hr>
                        <p>
                            Lời chào nồng nhiệt từ sharecv.vn! Hồ sơ của bạn đã được đề xuất trên nền tảng tuyển dụng sharecv.vn thông qua Cộng đồng Freelancer Headhunter của sharecv. Để đảm bảo tính bảo mật thông tin cá nhân, chỉ khi được sự đồng ý của bạn, hồ sơ của bạn mới được tiến cử đến nhà tuyển dụng để xem xét, đánh giá. <br>
                            Vì vậy, vui lòng BẤM VÀO nút: <br>
                            - <a href="http://localhost:3000/accept?id={cv_id}">"Accept"</a> nếu bạn đồng ý việc sự giới thiệu này. <br>
                            - <a href="http://localhost:3000/decline?id={cv_id}">"Decline"</a> nếu bạn từ chối sự giới thiệu việc làm này. <br>
                            Cảm ơn sự hợp tác của bạn. Nếu bạn cần thêm thông tin hoặc trợ giúp, xin vui lòng liên hệ với chúng tôi. 
                            Xin cảm ơn và trân trọng, Team ShareCV Đường dây hỗ trợ khách hàng: 0888818006 – 0914171381. <br>
                            Email: info@sharecv.vn. <br>
                            CẢM ƠN BẠN 
                        </p>
                    </body>
                </html>
                """
                collab_content = f"""
                <html>
                    <body>
                        <p> 
                            Lời chào nồng nhiệt từ SHARECV VN! <br>
                            Cảm ơn bạn đã giới thiệu/đề cử ứng viên đến nền tảng tuyển dụng SHARECV. Lưu ý quan trọng dành cho Cộng Tác Viên - chỉ khi có sự xác nhận đồng ý từ ứng viên thì hồ sơ do bạn giới thiệu mới được xem là hợp lệ và được chuyển đến Nhà tuyển dụng lựa chọn - đánh giá - phản hồi … <br>
                            Hồ sơ của ứng viên sẽ được lưu trong vòng 48h kể từ thời điểm bạn giới thiệu ứng viên. Vậy nên, bạn vui lòng liên lạc, nhắc nhở ứng viên của mình nhanh chóng check mail / zalo …và nhấn nút "Accept" nếu ứng viên đồng ý ứng tuyển/ kết nối công việc này nhé. <br>
                            Chúc bạn may mắn và thành công ! <br>
                            SHARECV -PLATFORM : Nền tảng dành cho Nhà Tuyển dụng và ứng viên gặp nhau thông qua sự kết nối - giới thiệu từ cộng đồng FREELANCER. 
                            SHARECV - Share cơ hội - Tăng kết nối- Nhân đôi giá trị! <br>
                            Thank you for your cooperation. <br>
                            Team Sharecv.vn <br>
                            Customer support <br>
                            Phone: 0888818006 - 0914171381 <br>
                            Email: info@sharecv.vn <br>
                            THANK YOU 
                        </p>
                    </body>
                </html>
                """
                mail_contents = {"candidate": candidate_content,
                                "collaborator": collab_content}
                #  Send mail
                Collaborator.Resume.send_email_request(cv_id, mail_contents, db_session, background_task, current_user)
                #   Update resume status 
                resume_result.ResumeVersion.status = schema.ResumeStatus.waiting_candidate_accept
                resume_result.ResumeVersion.is_ai_matched = True
            else:
                #   Update resume status 
                resume_result.ResumeVersion.status = schema.ResumeStatus.ai_matching_rejected
                resume_result.ResumeVersion.is_draft = True     #   Update resume as draft if resume is not matched with JD
            
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
            db.commit_rollback(db_session)
            return matching_result, saved_dir, cv_id


        @staticmethod
        def get_candidate_reply(cv_id: int, reply_status: schema.CandidateMailReply, db_session: Session):
            resume_result = General.get_detail_resume_by_id(cv_id, db_session)       
            if not resume_result:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not find resume")            
            #   Update resume status 
            if reply_status == schema.CandidateMailReply.accept:
                resume_result.ResumeVersion.status = schema.ResumeStatus.candidate_accepted_interview
            else:
                resume_result.ResumeVersion.status = schema.ResumeStatus.candidate_rejected_interview                
            db.commit_rollback(db_session)
    
    
        @staticmethod
        def get_matching_result(cv_id: int, db_session: Session):
            #   Get resume information
            resume = General.get_detail_resume_by_id(cv_id, db_session)
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
        def list_candidate(is_draft: bool, db_session: Session, current_user): 
            if is_draft:
                query = select(model.Resume, model.ResumeVersion)    \
                        .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id) \
                        .filter(model.Resume.user_id == current_user.id,
                                model.ResumeVersion.is_draft == True)
                results = db_session.execute(query).all()
                return [{
                    "id": result.ResumeVersion.cv_id,
                    "fullname": result.ResumeVersion.name,
                    "job_title": result.ResumeVersion.current_job,
                    "industry": result.ResumeVersion.industry,
                    "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV"
                    } for result in results]
            else:
                query = select(model.Resume, model.ResumeVersion, model.JobDescription.job_service)    \
                        .join(model.ResumeVersion, model.ResumeVersion.cv_id == model.Resume.id) \
                        .outerjoin(model.JobDescription, and_(model.Resume.job_id == model.JobDescription.id, model.Resume.job_id == None)) \
                        .filter(model.Resume.user_id == current_user.id,
                                model.ResumeVersion.is_draft == False)
                results = db_session.execute(query).all()
                return [{
                    "id": result.ResumeVersion.cv_id,
                    "fullname": result.ResumeVersion.name,
                    "job_title": result.ResumeVersion.current_job,
                    "industry": result.ResumeVersion.industry,
                    "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                    "status": result.ResumeVersion.status,
                    "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            

        @staticmethod
        def get_detail_candidate(request: Request, cv_id: int, db_session: Session):
            
            resume_result = General.get_detail_resume_by_id(cv_id, db_session) 
            if not resume_result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)
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
                    "cv_point": General.get_resume_valuate(cv_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), resume_result.ResumeVersion.avatar),
                    "candidate_name": resume_result.ResumeVersion.name,
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "email": resume_result.ResumeVersion.email,
                    "skills": resume_result.ResumeVersion.skills,
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
                        "job_title": exper.job_title,
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
                        "descriptions": project.descriptions,
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
                            "certificate_level": lang_cert.certificate_point_level
                        } for lang_cert in lang_certs],
                        "other_certificate": [{
                            "certificate_name": other_cert.certificate_name,
                            "certificate_level": other_cert.certificate_point_level
                        } for other_cert in other_certs]
                    },
                    "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)
                }
            
            
        @staticmethod
        def confirm_interview(data: schema.ResumeIndex, db_session: Session):            
            #   Get resume_db
            resume_db = General.get_detail_resume_by_id(data.cv_id, db_session)
            resume_db.ResumeVersion.status = schema.ResumeStatus.candidate_accepted_interview
            db.commit_rollback(db_session)
            
        
        @staticmethod
        def reschedule(data: schema.Reschedule, db_session: Session):
            schedule_result = db_session.execute(select(model.InterviewSchedule)    \
                                        .where(model.InterviewSchedule.candidate_id == data.cv_id)).scalars().first()
            schedule_result.date = data.date
            schedule_result.location = data.location
            schedule_result.start_time = data.start_time
            schedule_result.end_time = data.end_time
            schedule_result.note = data.note
            db.commit_rollback(db_session)
        
        
        @staticmethod
        def get_interview_schedule(data: schema.ResumeIndex, db_session: Session):
            query = select(model.InterviewSchedule).where(model.InterviewSchedule.candidate_id == data.cv_id)
            result = db_session.execute(query).scalars().first()
            if not result:
                raise HTTPException(status_code=404, detail="This resume has not yet been scheduled for an interview")
            return {
                "date": result.date,
                "location": result.location,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "note": result.note,
            } 