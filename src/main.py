import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import db
from auth.router import router as auth_router 
from postjob.router import router as postjob_router 
from money2point.router import router as money2point_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler


def init_app():
    db.init()
    app = FastAPI(
        title="ShareCV",
        description="Demo",
        version="1.0.0"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Start the app
    @app.on_event("startup")
    def on_startup():
        db.create_all()
   
    app.include_router(auth_router)
    app.include_router(postjob_router)
    app.include_router(money2point_router)
    
    return app


app = init_app()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler])  

# import shutil
# import json
# import time
# import uvicorn
# from fastapi import FastAPI, UploadFile, File, status
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.exceptions import HTTPException

# app = FastAPI()

# @app.post('/upload/download')
# def upload_download(uploaded_file: UploadFile = File(...)):
#     filename_path = f"static/{uploaded_file.filename}"
#     with open(filename_path, 'w+b') as file:
#         shutil.copyfileobj(uploaded_file.file, file)
#     return FileResponse(path=filename_path, media_type="application/octet-stream", filename=uploaded_file.filename)

if __name__ == '__main__':    
    uvicorn.run(
            "main:app",
            host="localhost", 
            port=6060, 
            reload=True)