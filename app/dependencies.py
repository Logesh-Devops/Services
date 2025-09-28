from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
import requests
import uuid
from jose import jwt, JWTError
from typing import List

from . import schemas
from dotenv import load_dotenv

import os

load_dotenv()

LOGIN_SERVICE_URL = os.getenv("API_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

http_bearer = HTTPBearer()

def get_current_user(token: str = Depends(http_bearer)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role_scope: str = payload.get("role_scope")
        if email is None or role_scope is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"email": email, "role": role_scope, "id": email}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "").upper()
        if user_role not in [role.upper() for role in allowed_roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
    return role_checker

def get_current_agency(
    x_agency_id: uuid.UUID = Header(...),
    current_user: dict = Depends(get_current_user),
):
    return {"id": x_agency_id}
