from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import ValidationError
from app.models.user import User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, email: str, name: str) -> User:
        if not email or not name:
            raise ValidationError("email and name are required")

        user = User(id=str(uuid4()), email=email, name=name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
