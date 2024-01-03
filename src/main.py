import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import db
from routers import auth, post_job
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
   
    app.include_router(auth.router)
    app.include_router(post_job.router)
    
    return app


app = init_app()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(EventHandlerASGIMiddleware, 
                   handlers=[local_handler])  

if __name__ == '__main__':    
    uvicorn.run(
            "main:app",
            host="localhost", 
            port=6060, 
            reload=True)