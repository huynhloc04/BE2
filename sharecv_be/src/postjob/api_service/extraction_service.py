from time import time
from config import JD_SAVED_DIR, CV_SAVED_DIR, SAVED_TEMP, CV_EXTRACTION_PATH, JD_EXTRACTION_PATH
import pdftotext
from fastapi import HTTPException, status
import os, json


class Extraction:
    
    def text_extract(filepath):
        with open(filepath, 'rb') as f:
            pdf = pdftotext.PDF(f)
        text = ''.join(pdf)
        return text
    
    
    @staticmethod
    def jd_parsing_template(filename: str):
        try:
            text = Extraction.text_extract(os.path.join(JD_SAVED_DIR, filename))

            prompt_template = f"""
            [Job Description]
            {text}

            [Requirements]
            """  
            print(" >>> Getting JD parsing template.")
            return prompt_template
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract JD data!")
    
    
    @staticmethod
    def cv_parsing_template(filename: str, check_dup: bool):
        try:
            if check_dup:
                text = Extraction.text_extract(os.path.join(SAVED_TEMP, filename))
            else:
                text = Extraction.text_extract(os.path.join(CV_SAVED_DIR, filename))
            prompt_template = f"""
            [Resume]
            {text}

            [Requirements]
            """  
            print(" >>> Getting CV parsing template.")
            return prompt_template
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract CV data!")
    
    
    # @staticmethod
    # def matching_template(cv_file: str, jd_file: str):
    #     # try:
    #     cv_text = Extraction.text_extract(os.path.join(CV_SAVED_DIR, cv_file))
    #     jd_text = Extraction.text_extract(os.path.join(JD_SAVED_DIR, jd_file))
    #     prompt_template = f"""
    #     [Job Description]
    #     {jd_text}
    #     [Resume]
    #     {cv_text}
    #     [Requirements]
    #     """  
    #     print(" >>> Getting matching template.")
    #     return prompt_template
    #     # except:
    #     #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract CV-JD data!")
    
    
    @staticmethod
    def matching_template(cv_file: str, jd_file: str):
        #   Get text file
        cv_text = Extraction.text_extract(os.path.join(CV_SAVED_DIR, cv_file))
        jd_text = Extraction.text_extract(os.path.join(JD_SAVED_DIR, jd_file))
        #   Extracted JSON 
        with open(os.path.join(os.path.join(JD_EXTRACTION_PATH, jd_file.split(".")[0] + ".json")), "r") as jd:
            jd_data = json.load(jd)
        with open(os.path.join(os.path.join(CV_EXTRACTION_PATH, cv_file.split(".")[0] + ".json")), "r") as cv:
            cv_data = json.load(cv)
        
        job_template = f"""
        [JOB DESCRIPTION]
          [Original Job Description]
            {jd_text}
          [Extracted Job Description]
            1. Job Title: {jd_data['job_title'][0]}

            2. Experience
            - {jd_data["descriptions"]}        
            - {jd_data["requirements"]}    

            3. Skills
            {jd_data["skills"]}

            4. Orientation
            {jd_data["orientation"]}
            
            5. Education
        """
        for data in jd_data["education"]:
            job_template += f" - Degree: {data['degree'][0]} - Major: {data['major'][0]} - GPA: {data['gpa'][0]}\n"

        resume_template = f"""
        [RESUME]
          [Original Resume]
            {cv_text}
          [Extracted Resume]
            1. Job Title: {cv_data['job_title'][0]}

            2. Experience:
                Work experience
        """
        for data in cv_data["work_experience"]:
            resume_template += f"""\t- Company_name: {data['company_name'][0]} 
                                     - Position: {data['position'][0]} 
                                     - Time: {data['start_time'][0]} to {data['end_time'][0]}\n"""
        resume_template += "\n\tProject"
        for data in cv_data["project"]:
            resume_template += f"""
                - Project_name: {data["project_name"][0]}
                - Description: {data["detailed_descriptions"]}
                - Time: {data['start_time'][0]} to {data['end_time'][0]}\n"""
        resume_template += ""
        resume_template += f"""
            3. Skill
                - Programming Language
                {cv_data['skills']['programming_language']}
                - Soft skill
                {cv_data['skills']['soft_skill']}
                - Hard skill
                {cv_data['skills']['hard_skill']}
            
            4. Orientation
                {cv_data["orientation"][0]}
            
            5 . Education
        """
        for data in cv_data["education"]:
            resume_template += f"\t - Institution_name: {data['institution_name'][0]} - Degree: {data['degree'][0]} - Major: {data['major'][0]} - GPA: {data['gpa'][0]} - Time: {data['start_time'][0]} to {data['end_time'][0]}\n"

        matching_template = job_template + resume_template
        
        print(" >>> Getting matching template.")
        return matching_template
    
    
    @staticmethod
    def resume_percent_estimate(filename: str):
        text = Extraction.text_extract(os.path.join(CV_SAVED_DIR, filename))
        prompt_template = f"""
        [Resume]
        {text}

        [Requirements]
        - Based on main information provided in the Resume above (Skill, Education, Work experience, Project, and other relevant information), please evaluate and estimate the quality (by giving "point") of Resume on the scale of 1.5 to 2. The higher value, the higher quality of the Resume is. 
        - Beside, give the detailed explanation for "point" you just give.
        The response must strictly follow JSON format as below:
            {{
                "point": 
                "explanation":
            }}
        """  
        print(" >>> Estimating resume percentage.")
        return prompt_template