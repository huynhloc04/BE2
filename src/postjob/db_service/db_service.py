import os
import json
import model
from config import db
from sqlmodel import select
from typing import Optional, Dict
from fastapi import HTTPException, status
from config import JD_EXTRACTION_PATH, CV_EXTRACTION_PATH


class DatabaseService:

    @staticmethod
    def store_jd_extraction(extracted_json: Dict, jd_file: str):
        try:
            json_file = jd_file.split(".")[0] + ".json"
            save_path = os.path.join(JD_EXTRACTION_PATH, json_file)
            with open(save_path, 'w') as file:
                json.dump(extracted_json, file)
            print(f"===> Saved JD json to: {save_path}")
            return save_path
        
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Can't save JD json {jd_file}")

    @staticmethod
    def store_cv_extraction(extracted_json: Dict, cv_file: str):
        try:
            json_file = cv_file.split(".")[0] + ".json"
            save_path = os.path.join(CV_EXTRACTION_PATH, json_file)
            with open(save_path, 'w') as file:
                json.dump(extracted_json, file)
            print(f"===> Saved CV json to: {save_path}")
            return save_path
        
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Can't save CV json {cv_file}")

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
    def check_db_duplicate(data, db_sesion):
        query = select(model.ResumeVersion).where(
                                        model.ResumeVersion.email == data["email"],
                                        model.ResumeVersion.phone == data["phone"],
                                        model.ResumeVersion.is_lastest == True
                            )
        result = db_sesion.execute(query).scalars().first()
        if result:
            raise HTTPException(status_code=409, detail="This resume already exists in system. Please upload the other!")
    
    @staticmethod
    def check_file_duplicate(file: str, path: str):
        try:
            filename, _  = os.path.splitext(file)
            filenames = [os.path.splitext(file)[0] for file in os.listdir(path)]
            return filename in filenames

        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot check duplicate {filename} - {path}")
