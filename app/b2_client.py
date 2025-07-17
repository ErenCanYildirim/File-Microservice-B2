import hashlib
import os
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)


class B2Client:
    def __init__(self):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.bucket = None
        self._authenticate()

    def _authenticate(self):
        try:
            self.api.authorize_account(
                "production",
                settings.b2_application_key_id,
                settings.b2_application_key,
            )
            self.bucket = self.api.get_bucket_by_name(settings.b2_bucket_name)
            logger.info("B2 authentication successful")
        except Exception as e:
            logger.error("B2 authentication failed", error=str(e))
            raise

    def upload_file(
        self, file_path: str, file_name: str, content_type: str = None
    ) -> dict:
        try:
            file_hash = self._calculate_file_hash(file_path)

            file_info = self.bucket.upload_local_file(
                local_file=file_path, file_name=file_name, content_type=content_type
            )

            download_url = self.api.get_download_url_for_fileid(file_info.id_)

            return {
                "b2_file_id": file_info.id_,
                "b2_file_name": file_info.file_name,
                "file_hash": file_hash,
                "public_url": download_url,
                "content_type": file_info.content_type,
            }
        except Exception as e:
            logger.error("File upload to B2 failed", error=str(e), file_name=file_name)
            raise

    def delete_file(self, file_id: str, file_name: str) -> bool:
        try:
            file_version = self.api.get_file_info(file_id)
            file_version.delete()
            logger.info("File deleted from B2", file_id=file_id)
            return True
        except Exception as e:
            logger.error("File deletion from B2 failed", error=str(e), file_id=file_id)
            return False

    def get_download_url(self, file_id: str) -> str:
        return self.api.get_download_url_for_fileid(file_id)

    def _calculate_file_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


b2_client = B2Client()
