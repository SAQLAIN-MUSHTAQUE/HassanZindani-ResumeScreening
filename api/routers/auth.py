from fastapi import HTTPException, APIRouter, Form
from api.schemas.auth import ConfirmRequest, RefreshTokenRequest, SigninRequest, SignupRequest, InitiateResetPasswordRequest, ConfirmResetPasswordRequest
from api.schemas.user import UserFullApiResponse
from api.services.auth_service import CognitoService
from api.services.user_services import create_user, get_user_by_id
from api.models.user import User
from api.utils.jwt_token import decode_jwt
from loguru import logger

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/signup")
async def signup(
    first_name: str = Form(...),
    last_name: str = Form(None),  # Make last_name optional
    email: str = Form(...),
    password: str = Form(...)
):
    request = SignupRequest(first_name=first_name, last_name=last_name, email=email, password=password)
    
    srv = CognitoService()
    user_param = request.model_dump(exclude={"password"})
    logger.info(user_param)

    created_user = await create_user(user_param)
    name = f"{request.first_name} {request.last_name}"

    cognito_user_res = srv.signup(request.email, request.password, name, request.email, str(created_user.id))
    logger.info(cognito_user_res)

    if cognito_user_res == 200:
        user_id = created_user.id
        return f"The user: {user_id} has registered but needs to confirm their account."
    else:
        user = User.objects(id=created_user.id)
        user.delete()
        raise HTTPException(status_code=500, detail=str(cognito_user_res))

@auth_router.post("/signin")
async def signin(
    email: str = Form(...),
    password: str = Form(...)
):
    request = SigninRequest(email=email, password=password)

    try:
        srv = CognitoService()
        signin_response = srv.sign_in(request.email, request.password)
        token_claims = await decode_jwt(signin_response["AuthenticationResult"]["IdToken"])
        user_data = await get_user_by_id(token_claims['custom:user_id'])
        if user_data is None:
            raise ValueError("User not found")
        return {"signinResponse": signin_response, "userData": UserFullApiResponse.model_validate(user_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.post("/confirm")
async def confirm(
    email: str = Form(...),
    code: str = Form(...)
):
    request = ConfirmRequest(email=email, code=code)

    try:
        srv = CognitoService()
        confirm_response = srv.confirm_sign_up(request.email, request.code)
        return confirm_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.post("/initiate-reset-password")
async def initiate_reset_password(
    email: str = Form(...)
):
    request = InitiateResetPasswordRequest(email=email)

    try:
        srv = CognitoService()
        response = srv.initiate_reset_password(request.email)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.post("/confirm-reset-password")
async def confirm_reset_password(
    email: str = Form(...),
    code: str = Form(...),
    new_password: str = Form(...)
):
    request = ConfirmResetPasswordRequest(email=email, code=code, new_password=new_password)

    try:
        srv = CognitoService()
        response = srv.confirm_reset_password(request.email, request.code, request.new_password)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.post("/refreshToken")
async def refresh_token(
    email: str = Form(...),
    refresh_token: str = Form(...)
):
    request = RefreshTokenRequest(email=email, refreshToken=refresh_token)

    try:
        srv = CognitoService()
        refresh_token_response = srv.refresh_token(request.email, request.refreshToken)
        return refresh_token_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
