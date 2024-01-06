import os
import json
from typing import Optional, Dict
from fastapi import HTTPException, status
from config import JD_EXTRACTION_PATH


class DatabaseService:

    @staticmethod
    def store_jd_extraction(extracted_json: Dict, jd_file: str):
        try:
            json_file = jd_file.split(".")[0] + ".json"
            save_path = os.path.join(JD_EXTRACTION_PATH, json_file)
            with open(save_path, 'w') as file:
                json.dump(extracted_json, file)
            print(f"===> Save jd json to file: {save_path}")
            return save_path
        
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Can't save DJ json {jd_file}")