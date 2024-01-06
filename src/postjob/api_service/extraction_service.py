from time import time
from config import JD_SAVED_DIR
import pdftotext
from fastapi import HTTPException, status
import os


class CvExtraction:
    
    def text_extract(filepath):
        with open(filepath, 'rb') as f:
            pdf = pdftotext.PDF(f)
        text = ''.join(pdf)
        return text
    
    
    @staticmethod
    def jd_parsing_template(jd_filename: str):
        # try:
        text = CvExtraction.text_extract(os.path.join(JD_SAVED_DIR, jd_filename))
        
        prompt_template = f"""
        [Job Description]
        {text}
        
        [Requirements]
        """  
        print(" >> Get JD parsing template.")
        return prompt_template
        # except:
            # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract CV data!")