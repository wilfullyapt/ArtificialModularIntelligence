from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import shutil
from datetime import datetime
import yaml
import asyncio

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

class MarkdownAPI:
    """API for markdown file operations with IPC support."""
    
    def __init__(self):
        """Initialize the markdown API."""
        self.markdown_dir = MARKDOWN_DIR
        self.attachments_dir = ATTACHMENTS_DIR

    def get_safe_filename(self, title: str) -> str:
        """Convert title to safe filename"""
        safe_chars = "-_"
        filename = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title.lower())
        return f"{filename}.md"

    async def process_markdown(self, content: str) -> str:
        """Process markdown content with AI assistance."""
        # This would typically involve sending the content to the AI for processing
        # For now, we'll just return the content as-is
        return content

    async def save_markdown(self, filename: str, content: str) -> bool:
        """Save markdown content to file."""
        try:
            file_path = os.path.join(self.markdown_dir, filename)
            with open(file_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving markdown: {e}")
            return False

    async def load_markdown(self, filename: str) -> str:
        """Load markdown content from file."""
        try:
            file_path = os.path.join(self.markdown_dir, filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {filename}")
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading markdown: {e}")
            return ""

    async def list_files(self) -> List[Dict[str, Any]]:
        """List all markdown files with metadata."""
        files = []
        for filename in os.listdir(self.markdown_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.markdown_dir, filename)
                files.append({
                    "title": filename[:-3],  # Remove .md extension
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat(),
                    "file_path": filename,
                })
        return files

def get_safe_filename(title: str) -> str:
    """Convert title to safe filename"""
    safe_chars = "-_"
    filename = "".join(c if c.isalnum() or c in safe_chars else "_" for c in title.lower())
    return f"{filename}.md"

# Initialize MarkdownAPI instance
markdown_api = MarkdownAPI()

@app.get("/api/markdown/files", response_model=List[MarkdownMetadata])
async def list_markdown_files():
    """List all markdown files with metadata"""
    files = await markdown_api.list_files()
    return [MarkdownMetadata(**file) for file in files]

@app.get("/api/markdown/{filename}")
async def get_markdown_file(filename: str):
    """Get content of a specific markdown file"""
    try:
        content = await markdown_api.load_markdown(filename)
        if not content:
            raise HTTPException(status_code=404, detail="File not found")
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/markdown")
async def create_markdown_file(markdown: MarkdownContent):
    """Create a new markdown file"""
    if not markdown.title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    filename = markdown_api.get_safe_filename(markdown.title)
    
    # Process content with AI assistance
    processed_content = await markdown_api.process_markdown(markdown.content)
    
    if await markdown_api.save_markdown(filename, processed_content):
        return {"filename": filename}
    else:
        raise HTTPException(status_code=500, detail="Failed to save file")

@app.put("/api/markdown/{filename}")
async def update_markdown_file(filename: str, markdown: MarkdownContent):
    """Update an existing markdown file"""
    try:
        # Process content with AI assistance
        processed_content = await markdown_api.process_markdown(markdown.content)
        
        if await markdown_api.save_markdown(filename, processed_content):
            return {"status": "updated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update file")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/markdown/{filename}")
async def delete_markdown_file(filename: str):
    """Delete a markdown file"""
    try:
        file_path = os.path.join(MARKDOWN_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        os.remove(file_path)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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