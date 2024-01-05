from time import time
from config import CVPDF_PATH
import pdftotext
from fastapi import HTTPException, status
from typing import Any
import os


class CvExtraction:
    
    def text_extract(filename):
        with open(filename, 'rb') as f:
            pdf = pdftotext.PDF(f)
        text = ''.join(pdf)
        return text
    
    
    @staticmethod
    def jd_parsing_template(jd_path: str):
        try:
            text = CvExtraction.text_extract(jd_path)
            prompt_template = f"""
            [Job Description]
            {text}
            
            [Requirements]
            """  
            print(" >> Get JD parsing template.")
            return prompt_template
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot extract CV data!")
    
