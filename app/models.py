from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100))
    file_hash = Column(String(64), unique=True, index=True)
    b2_file_id = Column(String(255), unique=True)
    b2_file_name = Column(String(255))
    upload_status = Column(String(20), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    uploaded_by = Column(String(100))
    file_metadata = Column(Text)  # store additional json metadata here
    public_url = Column(String(500))
    is_deleted = Column(Boolean, default=False)
