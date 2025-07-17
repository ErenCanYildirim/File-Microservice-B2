from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.database import get_db, engine
from app.models import Base
from app.schemas import FileUploadResponse, FileInfo, FileListResponse
from app.services import FileService
from app.config import settings

Base.metadata.create_all(bind=engine)

structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

app = FastAPI(
    title="File Upload Microservice",
    description="File Microservice with Backblaze B2",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this depending on the environemnt you use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "file-upload-service"}


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        file_record = await FileService.upload_file_async(db, file, uploaded_by)

        return FileUploadResponse(
            file_id=file_record.id,
            filename=file_record.filename,
            file_size=file_record.file_size,
            content_type=file_record.content_type,
            upload_status=file_record.upload_status,
            public_url=file_record.public_url,
            created_at=file_record.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_id}", response_model=FileInfo)
async def get_file(file_id: int, db: Session = Depends(get_db)):
    file_record = FileService.get_file_by_id(db, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return FileInfo(
        id=file_record.id,
        filename=file_record.filename,
        original_filename=file_record.original_filename,
        file_size=file_record.file_size,
        content_type=file_record.content_type,
        file_hash=file_record.file_hash,
        upload_status=file_record.upload_status,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at,
        uploaded_by=file_record.uploaded_by,
        public_url=file_record.public_url,
    )


@app.get("/files", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    uploaded_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    files, total = FileService.list_files(db, skip, size, uploaded_by)

    file_infos = [
        FileInfo(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_size=f.file_size,
            content_type=f.content_type,
            file_hash=f.file_hash,
            upload_status=f.upload_status,
            created_at=f.created_at,
            updated_at=f.updated_at,
            uploaded_by=f.uploaded_by,
            public_url=f.public_url,
        )
        for f in files
    ]

    return FileListResponse(files=file_infos, total=total, page=page, size=size)


@app.delete("/files/{file_id}")
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    success = FileService.delete_file(db, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"message": "File deleted successfully"}


@app.get("/files/{file_id}/download")
async def get_download_url(file_id: int, db: Session = Depends(get_db)):

    file_record = FileService.get_file_by_id(db, file_id)
    if not file_record or not file_record.public_url:
        raise HTTPException(status_code=404, detail="File not found or not uploaded")

    return {"download_url": file_record.public_url}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
