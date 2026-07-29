import uuid

from pathlib import Path

from imagekitio import ImageKit

from app.core.config import settings


class ImageKitService:

    def __init__(self):
        self.client = ImageKit(
            private_key=settings.IMAGEKIT_PRIVATE_KEY,
        )

    def upload_receipt(
        self,
        file_path: str,
        user_id: uuid.UUID,
        original_filename: str,
    ):
        path = Path(file_path)

        extension = (
            Path(original_filename).suffix.lower() or path.suffix.lower() or ".jpg"
        )

        filename = f"{uuid.uuid4()}{extension}"

        result = self.client.files.upload(
            file=path,
            file_name=filename,
            folder=f"/receipts/{user_id}",
            tags=[
                "receipt",
                f"user_{user_id}",
            ],
        )

        return result

    def delete_file(
        self,
        file_id: str,
    ):
        return self.client.files.delete(file_id)
