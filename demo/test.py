from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Enable CORS
origins = ["*"]  # You might want to specify your allowed origins here
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and use your routes
# Replace "your_routes_module" with the actual module name containing your routes
app.include_router(your_routes_module.router)

# Endpoint not found handler
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"code": 404, "message": "Endpoint not found"},
    )

# Server-side error handler
@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "error": "Something went wrong, please try again!"},
    )

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=4300, reload=True)
