import os
import hashlib
import uuid
from typing import Optional, BinaryIO
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models import FileRecord
from app.b2_client import b2_client
from app.config import settings
from app.tasks import process_file_upload
import structlog

logger = structlog.get_logger(__name__)


class FileService:

    @staticmethod
    def validate_file(file: UploadFile) -> None:

        if hasattr(file.file, "seek") and hasattr(file.file, "tell"):
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)

            if size > settings.max_file_size:
                raise HTTPException(status_code=413, detail="File too large")

        if file.filename:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in settings.allowed_extensions:
                raise HTTPException(status_code=400, detail="File type not allowed")

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        ext = os.path.splitext(original_filename)[1]
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"

    @staticmethod
    async def create_file_record(
        db: Session, file: UploadFile, uploaded_by: Optional[str] = None
    ) -> FileRecord:

        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        await file.seek(0)

        existing_file = (
            db.query(FileRecord)
            .filter(FileRecord.file_hash == file_hash, FileRecord.is_deleted == False)
            .first()
        )

        if existing_file:
            logger.info(f"Duplicate file detected", file_hash=file_hash)
            return existing_file

        unique_filename = FileService.generate_unique_filename(file.filename)

        file_record = FileRecord(
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
            upload_status="pending",
        )

        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        return file_record

    @staticmethod
    async def upload_file_async(
        db: Session, file: UploadFile, uploaded_by: Optional[str] = None
    ) -> FileRecord:
        FileService.validate_file(file)

        file_record = await FileService.create_file_record(db, file, uploaded_by)

        if file_record.upload_status == "completed":
            return file_record

        temp_path = os.path.join(settings.temp_upload_dir, file_record.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        process_file_upload.delay(file_record.id, temp_path)

        return file_record

    @staticmethod
    def get_file_by_id(db: Session, file_id: int) -> Optional[FileRecord]:
        return (
            db.query(FileRecord)
            .filter(FileRecord.id == file_id, FileRecord.is_deleted == False)
            .first()
        )

    @staticmethod
    def list_files(
        db: Session, skip: int = 0, limit: int = 100, uploaded_by: Optional[str] = None
    ) -> tuple[list[FileRecord], int]:
        query = db.query(FileRecord).filter(FileRecord.is_deleted == False)

        if uploaded_by:
            query = query.filter(FileRecord.uploaded_by == uploaded_by)

        total = query.count()
        files = query.offset(skip).limit(limit).all()

        return files, total

    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        file_record = FileService.get_file_by_id(db, file_id)
        if not file_record:
            return False

        file_record.is_deleted = True
        db.commit()

        if file_record.b2_file_id:
            b2_client.delete_file(file_record.b2_file_id, file_record.b2_file_name)

        return True
