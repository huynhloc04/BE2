import model
import os, shutil, json
from config import db
from company import schema
from sqlmodel import Session
from sqlalchemy import select
from fastapi import HTTPException
from postjob.gg_service.gg_service import GoogleService



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
        token = (db_session.execute(select(model.JWTModel).where(model.JWTModel.token == token))).scalar_one_or_none()
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
            "logo": company_result.logo,
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
    def check_company_exist(db_session: Session, current_user):
        query = select(model.Company).where(model.Company.user_id == current_user.id)
        result = db_session.execute(query).scalars().first()
        return True if result else False
    
    
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
    
    
class Bank:
    
    @staticmethod
    def add_bank_info(data: schema.BankBase, db_session: Session, current_user):
        bank_db = model.Bank(
                        user_id=current_user.id,
                        bank_name=data.bank_name,
                        branch_name=data.branch_name,
                        account_owner=data.account_owner,
                        account_number=data.account_number
        )
        db_session.add(bank_db)
        db.commit_rollback(db_session)
    
    
class General:   

    @staticmethod
    def give_user_point(point: float, db_session: Session, current_user):
        user_db = db_session.execute(select(model.User).where(model.User.id == current_user.id)).scalars().first()
        user_db.point = point
        db.commit_rollback(db_session)

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