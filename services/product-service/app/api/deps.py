# app/api/deps.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
from sqlmodel import Session
from app.core.config import settings
from app.core.db import engine
from collections.abc import Generator
# OAuth2 token bearer
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token")

# Minimal payload for other services
class TokenPayload(BaseModel):
    sub: str  # user_id
    is_superuser: bool = False

# Dependency
TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]

def get_current_user(token: TokenDep) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return token_data

CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
