from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/hello-world")
def read_root():
    return {"Hello": "World"}
