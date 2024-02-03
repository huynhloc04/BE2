import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import db
from auth.router import router as auth_router 
from postjob.router import router as postjob_router 
from money2point.router import router as money2point_router
from searchcv.router import router as searchcv_router
from company.router import router as company_router
# from headhunt.router import router as headhunt_router
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
    app.include_router(company_router)
    app.include_router(postjob_router)
    app.include_router(searchcv_router)
    # app.include_router(headhunt_router)
    app.include_router(money2point_router)
    
    return app


app = init_app()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler])  

if __name__ == '__main__':    
    uvicorn.run(
            "main:app",
            host="localhost", 
            port=8000, 
            reload=True)
