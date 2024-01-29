from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/hello-world")
def read_root():
    return {"Hello": "World"}

            
    
    #   Check_dep=True => CV_SAVED_TEMP_DIR