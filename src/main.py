import uvicorn
from config import settings, app_configs
from database import sessionmanager
from fastapi import FastAPI
from contextlib import asynccontextmanager
# from auth.router import router as auth_router
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if settings.debug_logs else logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(**app_configs, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {"message": "ShareCV Manager!!!"}


app.mount("/static", StaticFiles(directory="static"), name="static")
# Routers
app.include_router(auth_router)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8888, reload=True)