import model
import os, shutil, json
from config import db
from typing import List
from pydantic import EmailStr
from searchcv import schema
from typing import List, Dict, Any
from sqlmodel import Session, func, and_, or_, not_
from sqlalchemy import select
from fastapi import HTTPException, Request, BackgroundTasks, UploadFile, status
from postjob.api_service.extraction_service import Extraction
from postjob.api_service.openai_service import OpenAIService
from postjob.db_service.db_service import DatabaseService
from config import (
                CV_PARSE_PROMPT, 
                JD_PARSE_PROMPT,
                CV_EXTRACTION_PATH,
                JD_EXTRACTION_PATH, 
                JD_SAVED_TEMP_DIR,
                CV_SAVED_DIR,
                JD_SAVED_DIR,
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
    
    
class General:   
    
    @staticmethod
    def give_user_point(point: float, db_session: Session, current_user):
        user_db = db_session.execute(select(model.User).where(model.User.id == current_user.id)).scalars().first()
        user_db.point = point
        db.commit_rollback(db_session)
            
    def get_job_by_id(job_id: int, db_session: Session):
        job_query = select(model.JobDescription).where(model.JobDescription.id == job_id)
        job_result = db_session.execute(job_query).scalars().first() 
        return job_result
            
    def get_detail_resume_by_id(cv_id: int, db_session: Session):
        cv_query = select(model.Resume, model.ResumeVersion)    \
            .join(model.ResumeVersion, model.ResumeVersion.cv_id == cv_id) \
            .filter(model.Resume.id == cv_id)
        cv_result = db_session.execute(cv_query).first() 
        return cv_result
    
    @staticmethod
    def get_resume_valuate(cv_id, db_session):
        valuation_query = select(model.ValuationInfo).where(model.ValuationInfo.cv_id == cv_id)
        valuate_result = db_session.execute(valuation_query).scalars().first()
        if not valuate_result:
            raise HTTPException(status_code=404, detail="This resume has not been valuated!")
        return valuate_result
        
    @staticmethod
    def get_job_from_resume(cv_id: int, db_session: Session):
        resume = db_session.execute(select(model.Resume).where(model.Resume.id == cv_id)).scalars().first()
        job = db_session.execute(select(model.JobDescription).where(model.JobDescription.id == resume.job_id)).scalars().first()
        return job
        
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
    

class Recruiter:

    class Job:

        @staticmethod
        def save_jd_parsed_result(data, db_session, current_user):
            company_result = db_session.execute(select(model.Company).where(model.Company.user_id == current_user.id)).scalars().first()
            job_db = model.JobDescription(
                                    user_id=current_user.id,
                                    company_id=company_result.id,
                                    jd_file=data['jd_file'],
                                    job_service='Search CV',
                                    job_title=data['job_title'][0],
                                    industries=data['industries'],
                                    gender=data['gender'][0],
                                    job_type=data['job_type'][0],
                                    skills=data['skills'],
                                    received_job_time=data['received_job_time'][0],
                                    working_time=data['working_time'],
                                    descriptions=data['descriptions'],
                                    requirements=data['requirements'],
                                    benefits=data['benefits'],
                                    levels=data['levels'],
                                    roles=data['roles'],
                                    yoe=data['number_year_experience'],
                                    num_recruit=data['number_candidate'][0],
                                    min_salary=data['salary']['min_salary'][0],
                                    max_salary=data['salary']['max_salary'][0],
                                    address=data['location']['address'][0],
                                    city=data['location']['city/province'][0],
                                    country=data['location']['country'][0]
            )
            db_session.add(job_db)
            db.commit_rollback(db_session)
            edu_db = [model.JobEducation(
                                    job_id=job_db.id,
                                    degree=edu['degree'][0],
                                    major=edu['major'][0],
                                    gpa=edu['gpa'][0],
                                    start_time=edu['start_time'][0],
                                    end_time=edu['end_time'[0]]
            ) for edu in data['education']]
            db_session.add_all(edu_db)
            lang_certs = [model.LanguageJobCertificate(
                                    job_id=job_db.id,
                                    certificate_language=lang_cert['certificate_language'],
                                    certificate_name=lang_cert['certificate_name'],
                                    certificate_point_level=lang_cert['certificate_point_level'],
                                    start_time=lang_cert['start_time'],
                                    end_time=lang_cert['end_time']
            ) for lang_cert in data['certificates']['language_certificates']]
            db_session.add_all(lang_certs)
            other_certs = [model.LanguageJobCertificate(
                                    job_id=job_db.id,
                                    certificate_language=other_cert['certificate_language'],
                                    certificate_point_level=other_cert['certificate_point_level'],
                                    start_time=other_cert['start_time'],
                                    end_time=other_cert['end_time']
            ) for other_cert in data['certificates']['other_certificates']]
            db_session.add_all(other_certs)
            db.commit_rollback(db_session) 
            return job_db


        @staticmethod
        def jd_parsing(file: UploadFile, 
                       cleaned_filename: str, 
                       db_session: Session, 
                       current_user):
            #   Check duplicated filename
            if not DatabaseService.check_file_duplicate(cleaned_filename, JD_EXTRACTION_PATH):
                prompt_template = Extraction.jd_parsing_template(store_path=JD_SAVED_DIR, filename=cleaned_filename)
                #   Read parsing requirements
                with open(JD_PARSE_PROMPT, "r") as file:
                    require = file.read()
                prompt_template += require                 
                #   Start parsing
                extracted_result = OpenAIService.gpt_api(prompt_template)
                extracted_result["jd_file"] = os.path.join("static/job/uploaded_jds", cleaned_filename)     
                #   Save extracted result
                saved_path = DatabaseService.store_jd_extraction(extracted_json=extracted_result, jd_file=cleaned_filename)
                #   Save to database
                job_db = Recruiter.Job.save_jd_parsed_result(extracted_result, db_session, current_user)
            else:
                #   Read available extracted result
                saved_path = os.path.join(JD_EXTRACTION_PATH, cleaned_filename.split(".")[0] + ".json")
                with open(saved_path) as file:
                    extracted_result = file.read()
                #   Get existing database
                job_db = db_session.execute(select(model.JobDescription).where(model.JobDescription.jd_file == os.path.join("static/job/uploaded_jds", cleaned_filename)))
            return extracted_result, job_db

    class Resume: 

        @staticmethod
        def save_matching_result(cv_id: int, job_id: int, matching_result: Dict[str, Any], db_session: Session):
            #   Write matching result to Database
            matching_db = model.ResumeMatching(
                                    job_id=job_id,
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
                #   Save matching result to DB

            else:
                #   Read available extracted result
                saved_path = os.path.join(MATCHING_DIR, match_filename.split(".")[0] + ".json")
                with open(saved_path) as file:
                    matching_result = json.loads(file.read())
            return matching_result, saved_path
        

        @staticmethod
        def list_good_match(good_match: List[int], db_session: Session):
            results = []
            for cv_id in good_match:
                result = General.get_detail_resume_by_id(cv_id, db_session)
                education = db_session.execute(select(model.ResumeEducation).where(model.ResumeEducation.cv_id == cv_id)).scalars().first()
                results.append({
                    "current_job": result.Resumeversion.current_job,
                    "degree": education.degree,
                    "major": education.major,
                    "level": result.Resumeversion.level,
                    "skils": result.Resumeversion.skills
                })
            return results
    
    
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
        def get_detail_candidate(request: Request, candidate_id: int, db_session: Session, current_user):
            resume_result = General.get_detail_resume_by_id(candidate_id, db_session) 
            if not resume_result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            #   Get resume information of a specific recruiter
            choosen_result = db_session.execute(select(model.RecruitResumeJoin).where(and_(model.RecruitResumeJoin.user_id == current_user.id,
                                                                                           model.RecruitResumeJoin.resume_id == candidate_id))).scalars().first()
            
            if not choosen_result:
                return {
                    "candidate_id": candidate_id,
                    "job_service": job_result.job_service,
                    "candidate_name": "Họ và tên",
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "status": resume_result.ResumeVersion.status,
                    "cv_point": General.get_resume_valuate(candidate_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), "static/resume/avatar/default_avatar.png"),
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)
                }
            elif (choosen_result.package == schema.ResumePackage.basic) or (choosen_result == schema.ResumePackage.platinum and resume_result.ResumeVersion.status == schema.ResumeStatus.candidate_accepted_interview):
                return {
                    "candidate_id": candidate_id,
                    "job_service": job_result.job_service,
                    "candidate_name": resume_result.ResumeVersion.name,
                    "current_job": resume_result.ResumeVersion.current_job,
                    "industry": resume_result.ResumeVersion.industry,
                    "status": resume_result.ResumeVersion.status,
                    "cv_point": General.get_resume_valuate(candidate_id, db_session).total_point,
                    "avatar": os.path.join(str(request.base_url), "static/resume/avatar/default_avatar.png"),
                    "birthday": resume_result.ResumeVersion.birthday,
                    "gender": resume_result.ResumeVersion.gender,
                    "objectives": resume_result.ResumeVersion.objectives,
                    "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)     #   Show full information
                }
            else:
                pass


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
                        "job_service": General.get_job_from_resume(result.cv_id, db_session).job_service,
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
                        "job_service": General.get_job_from_resume(result.ResumeVersion.cv_id, db_session).job_service,
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
                        "industry": result.ResumeVersion.industry,
                        "job_service": General.get_job_from_resume(result.ResumeVersion.cv_id, db_session).job_service,
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
                        "job_service": General.get_job_from_resume(result.ResumeVersion.cv_id, db_session).job_service,
                        "referred_time": result.ResumeVersion.created_at
                    } for result in results]
            else:
                pass

        
        @staticmethod
        def reject_candidate(data: schema.RecruitRejectCandidate, db_session: Session, current_user):
            reject_db = model.RecruitResumeJoin(
                                        user_id=current_user.id,
                                        resume_id=data.cv_id,
                                        is_rejected=True,
                                        decline_reason=data.decline_reason
            )    
            db_session.add(reject_db)
            db.commit_rollback(db_session)
            
            
        @staticmethod
        def choose_candidate_basic(cv_id: int, db_session: Session, current_user):
            #   Check wheather recruiter's point is available
            valuation_result = General.get_resume_valuate(cv_id, db_session)
            if current_user.point < valuation_result.total_point:
                raise HTTPException(status_code=500, 
                                    detail=f"You are {valuation_result.total_point - current_user.point} points short when using this service. Please add more points")
            basic_resume = model.RecruitResumeJoin(
                                        user_id=current_user.id,    #   Current recruiter's account
                                        resume_id=cv_id,
                                        package="basic"
            )           
            db_session.add(basic_resume) 
            #   Update point of recuiter's account
            current_user.point -=  valuation_result.total_point
            db.commit_rollback(db_session)
            
            
        @staticmethod
        def choose_candidate_platinum(data: schema.ChoosePlatinum, db_session: Session, current_user):
            #   Check wheather recruiter's point is available
            valuation_result = General.get_resume_valuate(data.cv_id, db_session)
            if current_user.point < valuation_result.total_point * 10:
                raise HTTPException(status_code=500, 
                                    detail=f"You are {valuation_result.total_point*10 - current_user.point} points short when using this service. Please add more points")
            platinum_resume = model.RecruitResumeJoin(
                                        user_id=current_user.id,    #   Current recruiter's account
                                        resume_id=data.cv_id,
                                        package="platinum"
            )           
            db_session.add(platinum_resume) 
            #   Update point of recuiter's account
            current_user.point -=  valuation_result.total_point * 10
            
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
            resume.ResumeVersion.sstatus = schema.ResumeStatus.waiting_accept_interview
            db.commit_rollback(db_session)
        
        
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


class Collaborator:

    class Job:
        pass

    class Resume:

        @staticmethod
        def save_cv_parsed_result(extracted_result, industry, db_session, current_user):
            resume_db = model.Resume(user_id=current_user.id)
            db_session.add(resume_db)
            db.commit_rollback(db_session)
            db_session.refresh(resume_db)

            version_db = model.ResumeVersion(
                                        cv_id=resume_db.id,
                                        filename=extracted_result["cv_file"].split('/')[-1],
                                        cv_file=extracted_result["cv_file"],
                                        name=extracted_result['personal_information']['name'],
                                        level=extracted_result['levels'][0],
                                        gender=extracted_result['personal_information']['gender'],
                                        industry=industry if industry else extracted_result['industry'],
                                        current_job=extracted_result['job_title'][0],
                                        skills=extracted_result['skills'],
                                        email=extracted_result['contact_information']['email'],
                                        phone=extracted_result['contact_information']['phone'],
                                        address=extracted_result['contact_information']['address'],
                                        city=extracted_result['contact_information']['city/province'],
                                        country=extracted_result['contact_information']['country'],
                                        birthday=extracted_result['personal_information']['birthday'],
                                        linkedin=extracted_result['personal_information']['linkedin'],
                                        website=extracted_result['personal_information']['website'],
                                        facebook=extracted_result['personal_information']['facebook'],
                                        instagram=extracted_result['personal_information']['instagram'],
                                        objectives=extracted_result['objectives'][0]
            )
            db_session.add(version_db)
            db.commit_rollback(db_session)
            db_session.refresh(version_db)

            education_db = [model.ResumeEducation(
                                        cv_id=version_db.cv_id,
                                        institute_name=result['institution_name'],
                                        major=result['major'],
                                        degree=result['degree'],
                                        gpa=result['gpa'],
                                        start_time=result['start_time'],
                                        end_time=result['end_time']
            ) for result in extracted_result['education']]
            db_session.add_all(education_db)

            experience_db = [model.ResumeExperience(
                                        cv_id=version_db.cv_id,
                                        company_name=result['company_name'],
                                        job_title=result['position'],
                                        role=result['role'],
                                        level=result['level'],
                                        working_industry=result['working_industry'],
                                        start_time=result['start_time'],
                                        end_time=result['end_time']
            ) for result in extracted_result['work_experience']]
            db_session.add_all(experience_db)

            award_db = [model.ResumeAward(
                                        cv_id=version_db.cv_id,
                                        name=result['award_name'],
                                        time=result['time'],
                                        description=result['description']
            ) for result in extracted_result['awards']]
            db_session.add_all(award_db)

            project_db = [model.ResumeProject(
                                        cv_id=version_db.cv_id,
                                        project_name=result['project_name'],
                                        descriptions=result['detailed_descriptions'],
                                        start_time=result['start_time'],
                                        end_time=result['end_time']
            ) for result in extracted_result['projects']]
            db_session.add_all(project_db)

            lang_cert_db = [model.LanguageResumeCertificate(
                                        cv_id=version_db.cv_id,
                                        certificate_language=result['certificate_language'],
                                        certificate_name=result['certificate_name'],
                                        certificate_point_level=result['certificate_point_level'],
                                        start_time=result['start_time'],
                                        end_time=result['end_time']
            ) for result in extracted_result['certificates']['language_certificates']]
            db_session.add_all(lang_cert_db)

            other_cert_db = [model.OtherResumeCertificate(
                                        cv_id=version_db.cv_id,
                                        certificate_name=result['certificate_name'],
                                        certificate_point_level=result['certificate_point_level'],
                                        start_time=result['start_time'],
                                        end_time=result['end_time']
            ) for result in extracted_result['certificates']['other_certificates']]
            db_session.add_all(other_cert_db)

            db.commit_rollback(db_session)
            return resume_db, version_db


        @staticmethod
        def cv_parsing(data: schema.UploadResume, 
                       cleaned_filename: str, 
                       db_session: Session, 
                       current_user):
            #   Check duplicated filename
            if not DatabaseService.check_file_duplicate(cleaned_filename, CV_EXTRACTION_PATH):
                prompt_template = Extraction.cv_parsing_template(store_path=CV_SAVED_DIR, filename=cleaned_filename)
                #   Read parsing requirements
                with open(CV_PARSE_PROMPT, "r") as file:
                    require = file.read()
                prompt_template += require                 
                #   Start parsing
                extracted_result = OpenAIService.gpt_api(prompt_template)
                extracted_result["cv_file"] = os.path.join("static/resume/cv/uploaded_cvs", cleaned_filename)     
                #   Save extracted result
                saved_path = DatabaseService.store_cv_extraction(extracted_json=extracted_result, cv_file=cleaned_filename)
                #   Save to database
                resume_db, version_db = Collaborator.Resume.save_cv_parsed_result(extracted_result, data.industry, db_session, current_user)
            else:
                #   Read available extracted result
                saved_path = os.path.join(CV_EXTRACTION_PATH, cleaned_filename.split(".")[0] + ".json")
                with open(saved_path) as user_file:
                    extracted_result = user_file.read()
                resume_db, version_db = Collaborator.Resume.save_cv_parsed_result(json.loads(extracted_result), data.industry, db_session, current_user)
                #   Get existing database
                version_db = db_session.execute(select(model.ResumeVersion).where(model.ResumeVersion.cv_file == os.path.join("static/resume/cv/uploaded_cvs", cleaned_filename))).scalars().first()
            return extracted_result, version_db
        

        @staticmethod
        def resume_valuate(version_db: model.ResumeVersion, db_session: Session):
            #   Add "hard_point" initialization
            hard_point = 0
            for level_, point_ in level_map.items():
                if version_db.level in levels[int(level_)]:
                    hard_point += point_

            #   ============================== Soft point ==============================
            #   Degrees
            degree_point = 0
            degrees = []
            #   Get education information
            degree_db = db_session.execute(select(model.ResumeEducation.degree).where(model.ResumeEducation.cv_id == version_db.cv_id)).all()
            for degree in degree_db:
                if degree[0] in ["Bachelor", "Master", "Ph.D"]:
                    degrees.append(degree[0])
            degree_point = 0.5 * len(degrees)
            #   Certificates
            certs_point = 0
            cert_lst = []
            #   Get certificate information
            certs = db_session.execute(select(model.LanguageResumeCertificate).where(model.LanguageResumeCertificate.cv_id == version_db.cv_id)).all()
            for cert in certs:
                if cert.LanguageResumeCertificate.certificate_language=='N/A' or cert.LanguageResumeCertificate.certificate_name=="N/A" or cert.LanguageResumeCertificate.certificate_point_level=='N/A':
                    continue
                if cert.LanguageResumeCertificate.certificate_language == "English":
                    if (cert.LanguageResumeCertificate.certificate_name == "TOEIC" and float(cert.LanguageResumeCertificate.certificate_point_level) > 700) or (cert.LanguageResumeCertificate.certificate_name == "IELTS" and float(cert.LanguageResumeCertificate.certificate_point_level) > 7.0):
                        cert_lst.append({
                            "certificate_language": cert.LanguageResumeCertificate.certificate_language,
                            "certificate_name": cert.LanguageResumeCertificate.certificate_name,
                            "certificate_point_level": cert.LanguageResumeCertificate.certificate_point_level
                        })
                elif cert.LanguageResumeCertificate.certificate_language == "Japan" and cert.LanguageResumeCertificate.certificate_point_level in ["N1", "N2"]:
                    cert_lst.append({
                            "certificate_language": cert.LanguageResumeCertificate.certificate_language,
                            "certificate_name": cert.LanguageResumeCertificate.certificate_name,
                            "certificate_point_level": cert.LanguageResumeCertificate.certificate_point_level
                        })
                elif cert.LanguageResumeCertificate.certificate_language == "Korean":
                    if cert.LanguageResumeCertificate.certificate_name == "Topik_II" and cert.LanguageResumeCertificate.certificate_point_level in ["Level 5", "Level 6"]:
                        cert_lst.append({
                            "certificate_language": cert.LanguageResumeCertificate.certificate_language,
                            "certificate_name": cert.LanguageResumeCertificate.certificate_name,
                            "certificate_point_level": cert.LanguageResumeCertificate.certificate_point_level
                        })
                elif cert.LanguageResumeCertificate.certificate_language == "Chinese" and cert.LanguageResumeCertificate.certificate_point_level == ["HSK-5", "HSK-6"]:
                    cert_lst.append({
                            "certificate_language": cert.LanguageResumeCertificate.certificate_language,
                            "certificate_name": cert.LanguageResumeCertificate.certificate_name,
                            "certificate_point_level": cert.LanguageResumeCertificate.certificate_point_level
                        })
                certs_point = 0.5 * len(cert_lst)

            #   Save valuation result to Db
            valuate_db = model.ValuationInfo(
                                    cv_id=version_db.cv_id,
                                    hard_item=version_db.level,
                                    hard_point=hard_point,
                                    degrees=degrees,
                                    degree_point=degree_point,
                                    certificates=[str(cert_dict) for cert_dict in cert_lst],
                                    certificates_point=certs_point,
                                    total_point=hard_point + degree_point + certs_point
            )
            db_session.add(valuate_db)
            #   Update Resume valuation status
            version_db.status = schema.ResumeStatus.pricing_approved
            db.commit_rollback(db_session)
            db_session.refresh(valuate_db)
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
                    "job_service": result.ResumeVersion.created_at
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
        def get_detail_candidate(request: Request, cv_id: int, db_session: Session):
            
            resume_result = General.get_detail_resume_by_id(cv_id, db_session) 
            if not resume_result:
                raise HTTPException(status_code=404, detail="Resume doesn't exist!")
            job_result = General.get_job_by_id(resume_result.Resume.job_id, db_session)
            if not job_result:
                raise HTTPException(status_code=404, detail="Job doesn't exist!")
            
            return {
                "cv_id": cv_id,
                "avatar": os.path.join(str(request.base_url), resume_result.ResumeVersion.avatar),
                "candidate_name": resume_result.ResumeVersion.name,
                "job_service": job_result.job_service,
                "status": resume_result.ResumeVersion.status,                
                "current_job": resume_result.ResumeVersion.current_job,
                "industry": resume_result.ResumeVersion.industry,
                "birthday": resume_result.ResumeVersion.birthday,
                "gender": resume_result.ResumeVersion.gender,
                "objectives": resume_result.ResumeVersion.objectives,
                "linkedin": resume_result.ResumeVersion.linkedin,
                "website": resume_result.ResumeVersion.website,
                "facebook": resume_result.ResumeVersion.facebook,
                "instagram": resume_result.ResumeVersion.instagram,
                "cv_file": os.path.join(str(request.base_url), resume_result.ResumeVersion.cv_file)
            }
    
    
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
        def reschedule(data: schema.ChoosePlatinum, db_session: Session):
            schedule_result = db_session.execute(select(model.InterviewSchedule)    \
                                        .where(model.InterviewSchedule.candidate_id == data.cv_id)).scalars().first()
            schedule_result.date = data.date
            schedule_result.location = data.location
            schedule_result.start_time = data.start_time
            schedule_result.end_time = data.end_time
            schedule_result.note = data.note
            db.commit_rollback(db_session)
            