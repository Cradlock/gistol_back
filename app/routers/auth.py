from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service, get_current_refresh_user, get_current_teacher
from app.models.user import User
from app.schemas.auth import (
    AdminCodeUpdateRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminPasswordUpdateRequest,
    AdminProfileResponse,
    RefreshTokenResponse,
    TelegramAuthRequest,
    TelegramAuthResponse,
    UserResponse,
)
from app.services.auth import AuthService



router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)



# Telegram Auth 
@router.post("/telegram",response_model=TelegramAuthResponse)
async def telegram_auth(
    data : TelegramAuthRequest,
    service: AuthService = Depends(get_auth_service)
):
    result = await service.get_telegram_user(data.id_token)
    return TelegramAuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=UserResponse.model_validate(result["user"]),
    ) 


# обновление токена 
@router.post("/refresh",response_model=RefreshTokenResponse)
async def refresh_token(
    user: User = Depends(get_current_refresh_user),
    service: AuthService = Depends(get_auth_service)
):
    return await service.refresh_token({"sub":user.id}) 



# Логин админа 
@router.post("/admin",response_model=AdminLoginResponse)
async def admin_login(
    data: AdminLoginRequest,
    service: AuthService = Depends(get_auth_service) 
):
    return await service.login_by_code(data.code,data.password)


@router.get("/admin/me", response_model=AdminProfileResponse)
async def admin_me(user: User = Depends(get_current_teacher)):
    return AdminProfileResponse.model_validate(user)


@router.patch("/admin/code", response_model=AdminProfileResponse)
async def update_admin_code(
    data: AdminCodeUpdateRequest,
    user: User = Depends(get_current_teacher),
    service: AuthService = Depends(get_auth_service),
):
    updated = await service.update_admin_code(user, data)
    return AdminProfileResponse.model_validate(updated)


@router.patch("/admin/password", response_model=AdminProfileResponse)
async def update_admin_password(
    data: AdminPasswordUpdateRequest,
    user: User = Depends(get_current_teacher),
    service: AuthService = Depends(get_auth_service),
):
    updated = await service.update_admin_password(user, data)
    return AdminProfileResponse.model_validate(updated)








