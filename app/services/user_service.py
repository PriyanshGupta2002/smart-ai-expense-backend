from sqlalchemy.orm import Session

from app.models.user import User
from app.services.imagekit_service import ImageKitService
from fastapi import (
    UploadFile,
)


class UserService:

    def __init__(self, db: Session):
        self.db = db
        self.imagekit = ImageKitService()

    def update_user_details(
        self, user: User, email: str, first_name: str, last_name: str
    ):
        self.db.query(User).filter(user.id == User.id).update(
            {User.email: email, User.first_name: first_name, User.last_name: last_name}
        )
        self.db.commit()
        return self.db.query(User).filter(User.id == user.id).first()

    def upload_profile_image(
        self,
        user: User,
        file: UploadFile,
    ):

        imagekit_result = self.imagekit.upload_profile_image(
            file=file,
            user_id=user.id,
        )

        if user.profile_image_file_id:
            try:
                self.imagekit.delete_file(user.profile_image_file_id)
            except Exception:
                pass

        user.profile_image_url = imagekit_result.url
        user.profile_image_file_id = imagekit_result.file_id
        user.profile_image_path = imagekit_result.file_path

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_profile_image(
        self,
        user: User,
    ):

        if user.profile_image_file_id:
            try:
                self.imagekit.delete_file(user.profile_image_file_id)
            except Exception:
                pass

        user.profile_image_url = None
        user.profile_image_file_id = None
        user.profile_image_path = None

        self.db.commit()
        self.db.refresh(user)

        return user
