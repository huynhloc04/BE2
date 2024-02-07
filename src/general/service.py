import model
import os, json
from config import db
from general import schema
from sqlmodel import Session, func, and_, or_, not_
from sqlalchemy import select
from fastapi import HTTPException, Request
from postjob.gg_service.gg_service import GoogleService



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
    
    @staticmethod
    def get_package_from_resume(cv_id: int, db_session):
        query = select(model.RecruitResumeJoin).where(model.RecruitResumeJoin.resume_id == cv_id)
        result = db_session.execute(query).scalars().first()
        return result.package if result else None
    
    @staticmethod
    def get_company_from_interview(recruit_id: int, db_session: Session):
        query = select(model.Company).where(model.Company.user_id == recruit_id)
        return db_session.execute(query).scalars().first()
    
    @staticmethod
    def get_valuation_from_resume(cv_id: int, db_session: Session):
        query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        result = db_session.execute(query).scalars().first()
        return result.total_point if result else None
        
            
    @staticmethod
    def get_job_by_id(job_id: int, db_session: Session):
        job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
        
    @staticmethod
    def get_job_from_resume(cv_id: int, db_session: Session):
        resume = db_session.execute(select(model.Resume).where(model.Resume.id == cv_id)).scalars().first()
        job = db_session.execute(select(model.JobDescription).where(model.JobDescription.id == resume.job_id)).scalars().first()
        return job
            
    @staticmethod
    def get_detail_resume_by_id(cv_id: int, db_session: Session):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    @staticmethod
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
    def get_resume_status(data: schema.ResumeIndex, db_session: Session):
        resume = General.get_detail_resume_by_id(data.cv_id, db_session)
        return resume.ResumeVersion.status
    
    @staticmethod
    def get_resume_valuate(cv_id, db_session):
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This resume has not been valuated!")
        return valuate_result

class Recruiter:
        
    class Resume:
        
        @staticmethod
        def list_interview_schedule(db_session: Session, current_user):
            query = select(model.Resume, model.ResumeVersion, model.InterviewSchedule)  \
                        .join(model.Resume, model.Resume.id == model.ResumeVersion.cv_id)   \
                        .outerjoin(model.InterviewSchedule, model.InterviewSchedule.candidate_id == model.ResumeVersion.cv_id)   \
                        .filter(model.InterviewSchedule.user_id == current_user.id)
            results = db_session.execute(query).all()
            return [{
                "candidate_id": result.InterviewSchedule.candidate_id,
                "candidate_name": result.ResumeVersion.name,
                "job_title": result.ResumeVersion.current_job,
                "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                "status": result.ResumeVersion.status,
                "interview_date": result.InterviewSchedule.date,
                "interview_time": f"{result.InterviewSchedule.start_time} - {result.InterviewSchedule.end_time}",
                "interview_location": result.InterviewSchedule.location
            } for result in results]
            
            
        @staticmethod
        def transaction_history(db_sessioin: Session, current_user):
            query = select(model.TransactionHistory).where(model.TransactionHistory.user_id == current_user.id)
            results = db_sessioin.execute(query).scalars().all()
            user_point = db_sessioin.execute(select(model.User).where(model.User.id == current_user.id)).scalars().first()
            return user_point.point, [{
                   "transation_id": result.id,
                   "point_package_name": result.point,
                   "price": result.price,
                   "quantity": result.quantity,
                   "total_price": result.total_price,
                   "transaction_form": result.transaction_form,
                   "transaction_date": result.created_at
            } for result in results]
            
        
        
class Collaborator:
    
    class Resume:
        
        @staticmethod
        def list_interview_schedule(request: Request, db_session: Session, current_user):
            query = select(model.Resume, model.ResumeVersion, model.InterviewSchedule)  \
                        .join(model.Resume, model.Resume.id == model.ResumeVersion.cv_id)   \
                        .outerjoin(model.InterviewSchedule, model.InterviewSchedule.candidate_id == model.ResumeVersion.cv_id)   \
                        .filter(model.InterviewSchedule.collaborator_id == current_user.id)
            results = db_session.execute(query).all()
            return [{
                "candidate_id": result.InterviewSchedule.candidate_id,
                "company_logo": os.path.join(str(request.base_url), General.get_company_from_interview(result.InterviewSchedule.user_id, db_session).logo),
                "company_name": General.get_company_from_interview(result.InterviewSchedule.user_id, db_session).company_name,
                "candidate_name": result.ResumeVersion.name,
                "job_title": result.ResumeVersion.current_job,
                "job_service": General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                "status": result.ResumeVersion.status,
                "interview_date": result.InterviewSchedule.date,
                "interview_time": f"{result.InterviewSchedule.start_time} - {result.InterviewSchedule.end_time}",
                "interview_location": result.InterviewSchedule.location
            } for result in results]
        
        @staticmethod
        def referral_history(db_session: Session, current_user):
            query = select(model.Resume, model.ResumeVersion)  \
                            .join(model.ResumeVersion, model.Resume.id == model.ResumeVersion.cv_id)    \
                            .filter(model.User.id == current_user.id)
            results = db_session.execute(query).all() 
            if not results:
                raise HTTPException(status_code=404, detail="Could not find any referrals!")       
            return [{
                'job_service': General.get_job_from_resume(result.Resume.id, db_session).job_service if result.Resume.job_id else "SearchCV",
                'package_name': General.get_package_from_resume(result.Resume.id, db_session),
                'candidate_name': result.ResumeVersion.name,
                'job_name': result.ResumeVersion.current_job,
                'industry': result.ResumeVersion.industry,
                'point': General.get_valuation_from_resume(result.Resume.id, db_session),
                'point_recieved_time': result.ResumeVersion.point_recieved_time,
            } for result in results]
        
        @staticmethod
        def require_draw_point(data: schema.DrawMoney, db_session: Session, current_user):
            draw_db = model.DrawHistory(
                                    user_id=current_user.id,
                                    point=data.draw_point,
                                    transaction_form='banking'
            )
            db_session.add(draw_db)
            db.commit_rollback(db_session)
            
        @staticmethod
        def draw_history(db_session: Session, current_user):
            draw_results = db_session.execute(select(model.DrawHistory).where(model.DrawHistory.user_id == current_user.id)).scalars().all()
            return [{
                "point": result.point,
                "price": result.point*100000,
                "transaction_form": result.transaction_form,
                "created_at": result.created_at
                
            } for result in draw_results]
            
            
        
        
class Admin:
    
    class Resume:
        
        @staticmethod
        def list_interview_schedule(request: Request, db_session: Session):
            query = select(model.Resume, model.ResumeVersion, model.InterviewSchedule)  \
                        .join(model.Resume, model.Resume.id == model.ResumeVersion.cv_id)   \
                        .filter(model.InterviewSchedule.candidate_id == model.ResumeVersion.cv_id)
            results = db_session.execute(query).all()
            return [{
                "candidate_id": result.InterviewSchedule.candidate_id,
                "company_logo": os.path.join(str(request.base_url), General.get_company_from_interview(result.InterviewSchedule.user_id, db_session).logo),
                "company_name": General.get_company_from_interview(result.InterviewSchedule.user_id, db_session).company_name,
                "collaborator_name": db_session.execute(select(model.User).where(model.User.id==result.Resume.user_id)).scalars().first().fullname,
                "collaborator_phone": db_session.execute(select(model.User).where(model.User.id==result.Resume.user_id)).scalars().first().phone,
                "candidate_name": result.ResumeVersion.name,
                "job_title": result.ResumeVersion.current_job,
                "status": result.ResumeVersion.status,
                "interview_date": result.InterviewSchedule.date,
                "interview_time": f"{result.InterviewSchedule.start_time} - {result.InterviewSchedule.end_time}",
                "interview_location": result.InterviewSchedule.location
            } for result in results]
            
            
        @staticmethod
        def purchase_point_history(request: Request, db_session: Session):
            transactions = db_session.execute(select(model.TransactionHistory)).scalars().all()
            if not transactions:
                raise HTTPException(status_code=404, detail="Could not find any transactions!")        
            return [{
                "transaction_id": result.id,
                "company_logo": os.path.join(str(request.base_url), General.get_company_from_interview(result.user_id, db_session).logo),
                "company_name": General.get_company_from_interview(result.user_id, db_session).company_name,
                "point_package_name": result.point,
                "price": result.price,
                "quantity": result.quantity,
                "total_price": result.total_price,
                "transaction_form": result.transaction_form,
                "transaction_date": result.created_at
            } for result in transactions]
            
            
        @staticmethod
        def required_draw_history(db_session: Session):
            query = select(model.User, model.DrawHistory, model.Bank)   \
                        .join(model.User, model.User.id == model.DrawHistory.user_id)   \
                        .outerjoin(model.Bank, model.User.id == model.Bank.user_id)
            results = db_session.execute(query).all()
            return [{
                "account_info": [result.User.fullname, result.User.email, result.User.phone],
                "bank_info": [result.Bank.bank_name, result.Bank.branch_name, result.Bank.account_owner, result.Bank.account_number],
                "point": result.DrawHistory.point,
                "price": result.DrawHistory.point*100000,
                "created_at": result.DrawHistory.created_at,
                "draw_status": result.DrawHistory.draw_status,
            } for result in results]
            
        
        
        