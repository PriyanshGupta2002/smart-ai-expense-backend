from uuid import uuid4

from imagekitio import ImageKit


class StorageService:

    def __init__(self, imagekit: ImageKit):
        self.imagekit = imagekit

    def upload(
        self,
        *,
        content: bytes,
        filename: str,
        folder: str,
    ) -> dict:

        unique_filename = f"{uuid4()}_{filename}"

        result = self.imagekit.files.upload(
            file=content,
            file_name=unique_filename,
            folder=folder,
        )

        return {
            "file_id": result.file_id,
            "url": result.url,
            "name": filename,
        }
