import boto3
import hashlib
import hmac
import base64
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from api.models.user import User
from loguru import logger
import requests

load_dotenv(override=True)

AWS_COGNITO_USER_POOL_ID=os.getenv('AWS_COGNITO_USER_POOL_ID')
AWS_COGNITO_CLIENT_ID = os.getenv('AWS_COGNITO_CLIENT_ID')
AWS_COGNITO_SECRET_HASH= os.getenv('AWS_COGNITO_SECRET_HASH')


class CognitoService:
    def __init__(self):
        self.config = {
            'region_name': os.getenv("AWS_REGION")
        }
        self.user_pool_id = AWS_COGNITO_USER_POOL_ID
        self.client_id = AWS_COGNITO_CLIENT_ID
        self.secret_hash = AWS_COGNITO_SECRET_HASH
        self.client = boto3.client('cognito-idp', **self.config)

    def hash_secret(self, username):
        message = username + self.client_id
        dig = hmac.new(self.secret_hash.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    def signup(self, username, password, name, email, user_id):
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                SecretHash=self.hash_secret(username),
                Username=username,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'name',
                        'Value': name,
                    },
                    {
                        'Name': 'email',
                        'Value': email,
                    },
                    {
                        'Name': 'custom:user_id',
                        'Value': user_id,
                    },
                ],
            )
            print(response)
            if (response['ResponseMetadata']['HTTPStatusCode']):
                return 200

        except ClientError as e:
            error_message = f"Error during signup: {e}"
            logger.error(error_message)  
            return error_message
    
    def resend_confirmation_code(self, username):
        try:
            response = self.client.resend_confirmation_code(
                ClientId=self.client_id,
                Username=username,
                SecretHash=self.hash_secret(username)
            )
            logger.info(f"Confirmation code resent for {username}: {response}")
            return response
        except ClientError as e:
            logger.error(f"Error resending confirmation code: {e}")
            raise ValueError(e.response['Error']['Message'])
        

    def sign_in(self, username, password):
        try:
            response = self.client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                ClientId=self.client_id,
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': self.hash_secret(username)
                }
            )
            return response
        except ClientError as e:
            logger.error(f"Error during sign in: {e}")
            raise ValueError(e.response['Error']['Message'])

    def confirm_sign_up(self, username, code):
        
        response = self.client.confirm_sign_up(
            ClientId=self.client_id,
            Username=username,
            ConfirmationCode=code,
            SecretHash=self.hash_secret(username)
        )
        logger.info(f"AWS Response: {response}")
        if response:
            user = User.objects(email=username).first()

            # Update the confirmed field to True
            user.confirmed = True
            user.save()
            return response
        
    def initiate_reset_password(self, username):
        try:
            response = self.client.forgot_password(
                ClientId=self.client_id,
                Username=username,
                SecretHash=self.hash_secret(username)
            )
            return response
        except ClientError as e:
            logger.error(f"Error initiating password reset: {e}")
            raise ValueError(e.response['Error']['Message'])

    def confirm_reset_password(self, username, code, new_password):
        try:
            response = self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=code,
                Password=new_password,
                SecretHash=self.hash_secret(username)
            )
            return response
        except ClientError as e:
            logger.error(f"Error confirming password reset: {e}")
            raise ValueError(e.response['Error']['Message'])

    def refresh_token(self, username, refresh_token):
        try:
            response = self.client.initiate_auth(
                AuthFlow='REFRESH_TOKEN_AUTH',
                ClientId=self.client_id,
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token,
                    'SECRET_HASH': self.hash_secret(username)
                }
            )
            return response
        except ClientError as e:
            logger.error(f"Error refreshing token: {e}")
            raise ValueError(e.response['Error']['Message'])

    async def get_tokens(self, code: str):    
        saml_code = code
        cognito_client_id = os.getenv('AWS_COGNITO_CLIENT_ID')
        sso_auth_domain = self.sso_auth_domain
        sso_redirect_uri = os.getenv('SSO_REDIRECT_URI')
        cognito_secret = os.getenv('AWS_COGNITO_SECRET_HASH')
        sso_host = self.sso_host

        try:
            token_response = requests.post(
                url = f"{sso_auth_domain}/oauth2/token",
                headers = {
                        'Host': sso_host,
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                data = {
                        'grant_type': 'authorization_code',
                        'client_id': cognito_client_id,
                        'client_secret': cognito_secret,
                        'code': saml_code,
                        'redirect_uri': sso_redirect_uri
                    }
                )
            token_response.raise_for_status()  # Raise an error for bad responses
        except requests.RequestException as token_error:
            logger.error(f"Error getting tokens: {token_error}")
            raise

        token_body = token_response.json()
        
        return token_body

    async def get_user_info(self, token_body):
        sso_auth_domain = self.sso_auth_domain
        sso_host = self.sso_host

        access_token = token_body.get('access_token')

        pascal_case_token_body = {
            "AccessToken": token_body.get('access_token'),
            "ExpiresIn": token_body.get('expires_in'),
            "TokenType": token_body.get('token_type'),
            "RefreshToken": token_body.get('refresh_token'),
            "IdToken": token_body.get('id_token')
        }

        try:
            user_response = requests.get(
                url = f"{sso_auth_domain}/oauth2/userInfo",
                headers = {
                    'Host': sso_host,
                    'Authorization': f"Bearer {access_token}"
                }
            )
            user_response.raise_for_status()  # Raise an error for bad responses
        except requests.RequestException as user_error:
            logger.error("Error getting user info: %s", user_error)
            raise

        user_body = user_response.json()
        pascal_case_token_body["CognitoUsername"] = user_body.get('username')
        return user_body, pascal_case_token_body

    def update_cognito_user_id(self, user: User, cognito_username: str):
        try:
            # Update the custom attribute for the user
            response = self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=cognito_username,
                UserAttributes=[
                    {
                        'Name': 'custom:user_id',
                        'Value': str(user.id)
                    }
                ]
            )
            return {"message": "User ID updated successfully", "response": response}
        except ClientError as e:
            logger.error(f"Error refreshing token: {e}")
            raise ValueError(e.response['Error']['Message'])
