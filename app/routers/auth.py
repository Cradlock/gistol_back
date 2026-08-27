from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service, get_current_refresh_user, get_current_user
from app.models.user import User
from app.schemas.auth import AdminLoginRequest, AdminLoginResponse, CompleteUserRequest, RefreshTokenRequest, RefreshTokenResponse,TelegramAuthRequest, TelegramAuthResponse,UserResponse
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
    return await service.get_telegram_user(data.id_token) 



# Дополнение данных (для новых пользователей)
@router.post("/complete",response_model=UserResponse)
async def complete_auth(
    data: CompleteUserRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service)
):
    return await service.complete_student_profile(user,data.model_dump(exclude_unset=True))  

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








