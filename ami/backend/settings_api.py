from typing import Dict, Any, Optional, List

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AMI Settings API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:52563"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None

class SettingInfo(BaseModel):
    value: Any
    description: str
    type: str
    editable: bool

@app.get("/api/settings")
async def get_all_settings():
    """Get all available settings"""
    # TODO: Implement settings retrieval
    return {}

@app.get("/api/settings/{category}")
async def get_category_settings(category: str):
    """Get settings for a specific category"""
    # TODO: Implement category settings retrieval
    return {}

@app.get("/api/settings/{category}/{setting_name}")
async def get_setting(category: str, setting_name: str):
    """Get specific setting value and metadata"""
    # TODO: Implement single setting retrieval
    return {}

@app.put("/api/settings/{category}/{setting_name}")
async def update_setting(
    category: str,
    setting_name: str,
    setting: SettingUpdate
):
    """Update a specific setting"""
    # TODO: Implement setting update
    return {"status": "updated"}

@app.get("/api/settings/categories")
async def get_categories():
    """Get available setting categories"""
    # TODO: Implement category listing
    return []

@app.post("/api/settings/export")
async def export_settings(categories: Optional[List[str]] = None):
    """Export settings to file"""
    # TODO: Implement settings export
    return {"status": "not implemented"}

@app.post("/api/settings/import")
async def import_settings(settings_data: Dict[str, Any]):
    """Import settings from file"""
    # TODO: Implement settings import
    return {"status": "not implemented"}
