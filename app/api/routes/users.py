from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_write_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/v1", tags=["users"])


@router.post("/users", response_model=UserRead, status_code=201, summary="Create a user")
def create_user(payload: UserCreate, db: Session = Depends(get_write_db)):
    return UserService(db).create_user(payload.email, payload.name)
