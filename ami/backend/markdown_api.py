from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from datetime import datetime
import yaml

# Set base paths
FILESPACE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "filespace")
MARKDOWN_DIR = os.path.join(FILESPACE_DIR, "headspaces", "markdown")
RESOURCES_DIR = os.path.join(FILESPACE_DIR, "resources")
ATTACHMENTS_DIR = os.path.join(RESOURCES_DIR, "markdown_attachments")

# Create directories if they don't exist
os.makedirs(MARKDOWN_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

app = FastAPI(title="AMI Markdown API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:52563"],  # React frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MarkdownContent(BaseModel):
    content: str
    title: Optional[str] = None

class MarkdownMetadata(BaseModel):
    title: str
    last_modified: str
    file_path: str

def get_safe_filename(title: str) -> str:
    """Convert title to safe filename"""
    safe_chars = "-_"
    filename = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title.lower())
    return f"{filename}.md"

@app.get("/api/markdown/files", response_model=List[MarkdownMetadata])
async def list_markdown_files():
    """List all markdown files with metadata"""
    files = []
    for filename in os.listdir(MARKDOWN_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(MARKDOWN_DIR, filename)
            files.append(
                MarkdownMetadata(
                    title=filename[:-3],  # Remove .md extension
                    last_modified=datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat(),
                    file_path=filename,
                )
            )
    return files

@app.get("/api/markdown/{filename}")
async def get_markdown_file(filename: str):
    """Get content of a specific markdown file"""
    file_path = os.path.join(MARKDOWN_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, "r") as f:
        content = f.read()
    
    return {"content": content}

@app.post("/api/markdown")
async def create_markdown_file(markdown: MarkdownContent):
    """Create a new markdown file"""
    if not markdown.title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    filename = get_safe_filename(markdown.title)
    file_path = os.path.join(MARKDOWN_DIR, filename)
    
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File already exists")
    
    with open(file_path, "w") as f:
        f.write(markdown.content)
    
    return {"filename": filename}

@app.put("/api/markdown/{filename}")
async def update_markdown_file(filename: str, markdown: MarkdownContent):
    """Update an existing markdown file"""
    file_path = os.path.join(MARKDOWN_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, "w") as f:
        f.write(markdown.content)
    
    return {"status": "updated"}

@app.delete("/api/markdown/{filename}")
async def delete_markdown_file(filename: str):
    """Delete a markdown file"""
    file_path = os.path.join(MARKDOWN_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    os.remove(file_path)
    return {"status": "deleted"}

@app.post("/api/markdown/upload")
async def upload_attachment(file: UploadFile = File(...)):
    """Upload an attachment (image or other file)"""
    # Create a unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(ATTACHMENTS_DIR, filename)
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception:
        raise HTTPException(status_code=500, detail="Could not upload file")
    
    return {
        "filename": filename,
        "url": f"/api/markdown/attachments/{filename}"
    }

@app.get("/api/markdown/attachments/{filename}")
async def get_attachment(filename: str):
    """Get an attachment file"""
    file_path = os.path.join(ATTACHMENTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)