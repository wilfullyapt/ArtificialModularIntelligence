import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from markdown_api import app as markdown_app

app = FastAPI(title="AMI API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:52563"],  # React frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the markdown API router
app.mount("/", markdown_app)

if __name__ == "__main__":
    uvicorn.run(
        "ami.api.main:app",
        host="0.0.0.0",
        port=58744,  # Backend port
        reload=True
    )