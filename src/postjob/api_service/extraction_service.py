from time import time
from config import JD_SAVED_DIR, CV_SAVED_DIR, SAVED_TEMP
import pdftotext
from fastapi import HTTPException, status
import os


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
            print(" >>> Get JD parsing template.")
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
            print(" >>> Get CV parsing template.")
            return prompt_template
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract CV data!")
    
    
    @staticmethod
    def get_base_contact(filename: str):
        try:
            text = Extraction.text_extract(os.path.join(SAVED_TEMP, filename))
            prompt_template = f"""
            [Resume]
            {text}

            [Requirements]
            """  
            print(" >>> Get CV contact information.")
            return prompt_template
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract contact info!")