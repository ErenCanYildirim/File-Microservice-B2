from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    file_size: int
    content_type: str
    upload_status: str
    public_url: Optional[str] = None
    created_at: datetime


class FileInfo(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    file_hash: str
    upload_status: str
    created_at: datetime
    updated_at: Optional[datetime]
    uploaded_by: Optional[str]
    public_url: Optional[str]
    metadata: Optional[Dict[str, Any]] = None


class FileListResponse(BaseModel):
    files: list[FileInfo]
    total: int
    page: int
    size: int


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_id: int
    expires_in: int = 3600
