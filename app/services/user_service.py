from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.models.user import User


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, email: str, name: str) -> User:
        email = email.strip().lower()
        # first statement of the write transaction (BEGIN IMMEDIATE), so the check below is race-free
        if self.db.query(User).filter(User.email == email).first():
            self.db.rollback()
            raise ConflictError("a user with this email already exists")
        user = User(id=str(uuid4()), email=email, name=name.strip())
        self.db.add(user)
        self.db.commit()
        return user
