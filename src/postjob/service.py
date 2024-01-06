import model
from fastapi import HTTPException, Request
from sqlalchemy import select
from fastapi import UploadFile, status
import os, shutil
from config import db
from config import JD_SAVED_DIR, CV_PARSE_PROMPT, JD_PARSE_PROMPT
from postjob import schema
from sqlmodel import Session
from postjob.api_service.extraction_service import CvExtraction
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
        
        with open(os.path.join(os.getenv("COMPANY_DIR"), "logo",  data.logo.filename), 'w+b') as file:
            shutil.copyfileobj(data.logo.file, file)
        with open(os.path.join(os.getenv("COMPANY_DIR"), "cover_image",  data.cover_image.filename), 'w+b') as file:
            shutil.copyfileobj(data.cover_image.file, file)
        with open(os.path.join(os.getenv("COMPANY_DIR"), "company_video",  data.company_video.filename), 'w+b') as file:
            shutil.copyfileobj(data.company_video.file, file)
        return db_company
    
    
    @staticmethod
    def get_company(db_session: Session, user):
        query = select(model.Company).where(model.Company.user_id == user.id)
        results = db_session.execute(query).scalars().first()
        return results
    

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
    def list_industry(db_session: Session):
        results = db_session.execute(select(model.Industry.name)).scalars().all()
        return results
    

class Job:

    @staticmethod
    def clean_filename(filename):
        # Split the filename and file extension
        name, extension = os.path.splitext(filename)
        # Replace spaces with underscores in the filename
        name = name.replace(" ", "_")
        # Remove dots from the filename
        name = name.replace(".", "")
        # Concatenate the cleaned filename with the file extension
        cleaned_filename = name + extension
        return cleaned_filename
    

    @staticmethod
    def upload_jd(request: Request, 
                  uploaded_file: UploadFile, 
                  db_session: Session, 
                  user):
        if uploaded_file.content_type != 'application/pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
        
        cleaned_filename = Job.clean_filename(uploaded_file.filename)
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
    def upload_jd_again(request: Request, 
                        uploaded_file: UploadFile, 
                        db_session: Session, 
                        user):
        if uploaded_file.content_type != 'application/pdf':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must be PDF file")
        
        query = select(model.JobDescription).where(model.JobDescription.user_id == user.id)
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
        query = select(model.JobDescription).where(
                                            model.JobDescription.user_id == user.id,
                                            model.JobDescription.id == job_id)
        result = db_session.execute(query).scalars().first()        
        if not result.jd_file:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload at least 1 CV_PDF")

        filename = result.jd_file.split("/")[-1]
        prompt_template = CvExtraction.jd_parsing_template(filename)

        #   Read parsig requirements
        with open(JD_PARSE_PROMPT, "r") as file:
            require = file.read()
        prompt_template += require 
        
        #   Start parsing
        extracted_result = OpenAIService.gpt_api(prompt_template)
        
        #   Save extracted result
        saved_path = DatabaseService.store_jd_extraction(extracted_json=extracted_result, jd_file=filename)
        return extracted_result, saved_path
        
        
    @staticmethod
    def fill_job(data_form: schema.JobUpdate,
                 db_session: Session,
                 user):
        query = select(model.JobDescription).where(
                                            model.JobDescription.user_id == user.id,
                                            model.JobDescription.id == data_form.job_id)
        result = db_session.execute(query).scalars().first() 
        
        for key, value in dict(data_form).items():
            if key != "job_id":
                if value is not None and (key != "education" and key != "language_certificates" and key != "other_certificates"):
                    setattr(result, key, value)  
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
    def update_job(data_form: schema.JobUpdate,
                 db_session: Session,
                 user):
        job_query = select(model.JobDescription).where(
                                            model.JobDescription.user_id == user.id,
                                            model.JobDescription.id == data_form.job_id)
        result = db_session.execute(job_query).scalars().first() 
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
        job_query = select(model.JobDescription).where(
                                            model.JobDescription.user_id == user.id,
                                            model.JobDescription.id == job_id)
        result = db_session.execute(job_query).scalars().first() 
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
        
        if is_draft:
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngành nghề": result.industries,
                "Loại dịch vụ": result.job_form,
                "Ngày tạo": result.created_at
            } for result in results]
            
        else:
            return [{
                "ID": result.id,
                "Tên vị trí": result.job_title,
                "Ngày đăng tuyển": result.created_at,
                "Loại dịch vụ": result.job_form,
                "Trạng thái": result.status,
                "CVs": None
            } for result in results]
        
        
    @staticmethod
    def get_job(job_id, db_session, user):
        job_query = select(model.JobDescription).where(model.JobDescription.user_id == user.id,
                                                        model.JobDescription.id == job_id)
        results = db_session.execute(job_query).scalars().first() 
        if not results:
            raise HTTPException(status_code=404, detail="Job doesn't exist!")
        
        