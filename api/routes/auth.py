from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.user import UserSignup, UserLogin, UserOut, TokenResponse
from services.auth_service import signup_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut)
async def signup(payload: UserSignup):
    return await signup_user(payload)

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    token = await login_user(payload)
    return {"access_token": token}