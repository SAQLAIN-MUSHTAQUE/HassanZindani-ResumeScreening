from fastapi import APIRouter, HTTPException
from api.schemas.user import UserFullApiResponse
from api.services import user_services as user_service
from api.models.user import User


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/ids/")
async def get_all_user_ids():
    try:
        user_ids = [f"id= {user.id}" for user in User.objects.all()]  
        return user_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@user_router.get("/{id}", response_model=UserFullApiResponse)
async def get_user_by_id(id: str ):
    try:
        # Getting User Document
        user_dict = await user_service.get_user_by_id(id)
        if not user_dict:
            raise HTTPException(status_code=404, detail=f"User with id: {id} not found")
        

        user_dict = user_dict.to_mongo().to_dict()  # Get dictionary
        user_dict['id'] = user_dict.pop('_id')  # Rename _id to id
        return UserFullApiResponse(**user_dict)  # Return the modified dictionary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@user_router.delete("/{id}")
async def delete_user_by_id(id: str):
    try:
        # Attempt to get the user first to confirm existence
        user = await user_service.get_user_by_id(id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User with id: {id} not found")

        # Delete the user
        if user:
            user.delete()
            return {"message": f"User with id: {id} successfully deleted"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete user with id: {id}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))