import os
from celery import Celery
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import FileRecord
from app.b2_client import b2_client
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)

celery = Celery("file_service", broker=settings.redis_url, backend=settings.redis_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery.task(bind=True, max_retries=3)
def process_file_upload(self, file_record_id: int, temp_file_path: str):
    db = SessionLocal()
    try:
        file_record = (
            db.query(FileRecord).filter(FileRecord.id == file_record_id).first()
        )
        if not file_record:
            logger.error("File record not found", file_record_id=file_record_id)
            return

        file_record.upload_status = "uploading"
        db.commit()

        b2_result = b2_client.upload_file(
            temp_file_path, file_record.filename, file_record.content_type
        )

        file_record.b2_file_id = b2_result["b2_file_id"]
        file_record.b2_file_name = b2_result["b2_file_name"]
        file_record.public_url = b2_result["public_url"]
        file_record.upload_status = "completed"
        db.commit()

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        logger.info("File upload completed", file_record_id=file_record_id)

    except Exception as e:
        logger.error("File upload failed", file_record_id=file_record_id, error=str(e))

        if "file_record" in locals():
            file_record.upload_status = "failed"
            db.commit()

        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2**self.request.retries))

    finally:
        db.close()