# import httpx
import jwt
# import logging
from fastapi import HTTPException
from jose import jwk, JWTError
from jose.utils import base64url_decode
# from pydantic import BaseModel
# from datetime import datetime, timezone
from loguru import logger
# import os 
# from dotenv import load_dotenv
# from fastapi import Depends
# from fastapi.security import OAuth2PasswordBearer
# from fastapi import status

# from api.models.user import User

# import requests

# load_dotenv(override=True)

# # Environment configuration (Replace with your actual config)
# COGNITO_REGION = os.getenv("AWS_REGION")
# COGNITO_USER_POOL_ID = os.getenv("AWS_COGNITO_USER_POOL_ID")
# COGNITO_CLIENT_ID = os.getenv("AWS_COGNITO_CLIENT_ID")

# COGNITO_BASE_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
# JWKS_URI = f"{COGNITO_BASE_URL}/.well-known/jwks.json"

class UnauthorizedRequestError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)

# async def validate_jwt_or_throw(token: str, valid_audience_list: list[str]):
#     logger.debug(f"Validating JWT token: {token} for audiences: {valid_audience_list}")

#     payload_verification_response = await verify_jwt_payload(token)
#     if not payload_verification_response["is_valid"]:
#         raise UnauthorizedRequestError("Token is invalid (expired or tampered)")

#     token_claims = decode_jwt(token)
#     logger.debug(f"Authorization header token claims: {token_claims}")
#     if not token_claims:
#         raise UnauthorizedRequestError("Token missing claims: 'aud' and 'exp' to be validated")

#     token_expiration_date = datetime.fromtimestamp(token_claims.exp, timezone.utc)
#     if token_expiration_date < datetime.now(timezone.utc):
#         raise UnauthorizedRequestError("Expiration date ('exp' claim) in token is expired")

#     if token_claims.aud not in valid_audience_list:
#         raise UnauthorizedRequestError("Token audience ('aud' claim) is invalid")

# async def get_signing_key(kid: str):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(JWKS_URI)
#         response.raise_for_status()
#         jwks = response.json()
#         for key in jwks['keys']:
#             if key['kid'] == kid:
#                 return key
#         raise UnauthorizedRequestError("Invalid JWT. No kid found in header.")
    
# async def verify_jwt_payload(token: str):
#     try:
#         unverified_header = jwt.get_unverified_header(token)
#         kid = unverified_header.get('kid')

#         if not kid:
#             raise UnauthorizedRequestError('Invalid JWT. No kid found in header.')

#         signing_key = await get_signing_key(kid)
#         public_key = jwk.construct(signing_key)

#         message, encoded_signature = token.rsplit('.', 1)
#         decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))

#         if not public_key.verify(message.encode('utf-8'), decoded_signature):
#             raise UnauthorizedRequestError('Signature verification failed')

#         jwt.decode(
#             token,
#             public_key.to_pem().decode('utf-8'),
#             audience=COGNITO_CLIENT_ID,
#             issuer=COGNITO_BASE_URL,
#             algorithms=['RS256']
#         )

#         return {"is_valid": True}
#     except JWTError as e:
#         logger.error(f"JWT validation error: {e}")
#         return {"is_valid": False, "error": e}
    
    
async def decode_jwt(token: str):
    try:
        token_claims = jwt.decode(token, options={"verify_signature": False})
        return token_claims
    except JWTError as e:
        logger.error(f"Error decoding JWT: {e}")
        raise UnauthorizedRequestError("Failed to decode JWT")