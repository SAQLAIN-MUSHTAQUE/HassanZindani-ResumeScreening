import logging

import mongoengine
from bson import ObjectId
from fastapi import HTTPException
from api.models.user import User
from api.schemas.user import CreateUserData, UpdateUserData
from api.services.auth_service import CognitoService

# from api.services.notification_service import send_verification_email


logger = logging.getLogger(__name__)


async def get_user_by_id(id: str) -> User:
    logger.debug(f"Getting user by id: {id}")
    try:
        user = User.objects.get(id=ObjectId(id))

    except User.DoesNotExist:
        raise HTTPException(status_code=400, detail=f"User with id {id} does not exist")
    logger.info(f"Found user by id: {id}, user: {user}")
    return user


async def get_by_email(email: str) -> User:
    logger.debug(f"Getting user by email: {email}")
    try:
        user = User.objects.get(email=email)
    except mongoengine.DoesNotExist:
        raise HTTPException(
            status_code=400, detail=f"User with email {email} does not exist"
        )
    logger.info(f"Found user by email: {email}, user: {user}")
    return user


async def create_user(create_user_data: CreateUserData, cognito_username: str = None):
    logger.debug(f"Creating or updating user with data: {create_user_data}")

    existent_user = User.objects.filter(email=create_user_data["email"]).first()

    f_name = create_user_data["first_name"]
    l_name = create_user_data["last_name"]
    user_full_name = f"{f_name} {l_name}"

    # Ensure the username is set or generate it
    if "username" not in create_user_data or not create_user_data["username"]:
        create_user_data["username"] = user_full_name

    if existent_user:
        # Update the existing user's fields
        existent_user.first_name = create_user_data["first_name"]
        existent_user.last_name = create_user_data["last_name"]
        existent_user.user_full_name = user_full_name  
        existent_user.username = create_user_data["username"]  # Update username

        existent_user.save()


        logger.info(f"User updated: {existent_user}")
        return existent_user

    # Create a new user if email does not exist
    user = User(
        **create_user_data,
        user_full_name=user_full_name,  # Set the full name on user creation
    )

    user.save()

    logger.info(f"User created: {user}")
    return user

async def update_user(id: str, user_data: UpdateUserData):
    logger.debug(f"Updating user with id: {id}, data: {user_data}")

    user = await get_user_by_id(id)

    user_data_dict = user_data.model_dump(exclude_unset=True)

    user_dict = user.to_mongo().to_dict()
    user_dict["_id"] = str(user_dict["_id"])

    user.update(**user_data_dict)

    user.save()

    return user_dict
