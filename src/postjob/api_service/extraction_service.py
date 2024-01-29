import pdftotext
from fastapi import HTTPException, status
import os, json
from config import (JD_SAVED_DIR, 
                    CV_SAVED_DIR, 
                    CV_SAVED_TEMP_DIR, 
                    JD_SAVED_TEMP_DIR, 
                    CV_EXTRACTION_PATH, 
                    JD_EXTRACTION_PATH)


class Extraction:
    
    def text_extract(filepath):
        with open(filepath, 'rb') as f:
            pdf = pdftotext.PDF(f)
        text = ''.join(pdf)
        return text
    
    
    @staticmethod
    def jd_parsing_template(store_path: str, filename: str):
        try:
            text = Extraction.text_extract(os.path.join(store_path, filename))
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
                text = Extraction.text_extract(os.path.join(CV_SAVED_TEMP_DIR, filename))
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
        # cv_text = Extraction.text_extract(os.path.join(CV_SAVED_DIR, cv_file))
        # jd_text = Extraction.text_extract(os.path.join(JD_SAVED_DIR, jd_file))
        #   Extracted JSON 
        with open(os.path.join(os.path.join(JD_EXTRACTION_PATH, jd_file.split(".")[0] + ".json")), "r") as jd:
            jd_data = json.load(jd)
        with open(os.path.join(os.path.join(CV_EXTRACTION_PATH, cv_file.split(".")[0] + ".json")), "r") as cv:
            cv_data = json.load(cv)

        cv_exper = ""
        for idx, data in enumerate(cv_data["work_experience"]):
            cv_exper += f"""\t
            Company {idx}:
            - Company_name: {data['company_name']} 
            - Position: {data['position']} 
            - Time: {data['start_time']} to {data['end_time']}\n"""
        jd_edu = ""
        for data in jd_data["education"]:
            jd_edu += f" - Degree: {data['degree'][0]} - Major: {data['major'][0]} - GPA: {data['gpa'][0]}\n"
        cv_edu = ""
        for data in cv_data["education"]:
            cv_edu += f""" 
            - Institution_name: {data['institution_name']} - Degree: {data['degree']} - Major: {data['major']} - GPA: {data['gpa']} - Time: {data['start_time']} to {data['end_time']}\n"""
        
        template = f"""
            [JOB DESCRIPTION - Job Title]
            - Position: {jd_data['job_title'][0]}
            - Level: {jd_data['levels'][0]}
            [RESUME - Job Title]
            - {cv_data['job_title'][0]}
            
            [JOB DESCRIPTION - Experience]
            - Descriptions: {jd_data["descriptions"]}        
            - Work requirements: {jd_data["requirements"]}    
            [RESUME - Experience]
            - {cv_exper}    

            [JOB DESCRIPTION - Skills]
            - {jd_data["skills"]}
            [RESUME - Skills]
            - Programming Language
            {cv_data['skills']['programming_language']}
            - Soft skill
            {cv_data['skills']['soft_skill']}
            - Hard skill
            {cv_data['skills']['hard_skill']}  

            [JOB DESCRIPTION - Orientation]
            - {jd_data["orientation"][0]}
            [RESUME - Orientation]
            - {cv_data["orientation"][0]}

            [JOB DESCRIPTION - Education]
            {jd_edu}
            [RESUME - Education]
            {cv_edu}
        """
        print(" >>> Getting matching template.")
        return template
    
    
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
            }}
        """  
        print(" >>> Estimating resume percentage.")
        return prompt_template