from typing import List, Optional, Annotated, Any, Callable ,Dict
from datetime import date
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, GetJsonSchemaHandler, EmailStr, HttpUrl
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:
    # Based on https://docs.pydantic.dev/latest/usage/types/custom/#handling-third-party-types.

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            return ObjectId(input_value)

        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )


PydanticObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]



class CreateUserData(BaseModel):
    name: str
    type: str
    country: str
    email: str
    company: Optional[str] = None
    
    model_config = {'from_attributes': True}
    


class UpdateUserData(BaseModel):
    first_name: Optional[str] = None  
    last_name: Optional[str] = None
    profile_image_url: Optional[str] = None  
    email: Optional[EmailStr] = None  


    model_config = {'from_attributes': True}

class SearchUsersOptionsData(BaseModel):
    name: str
    type: str
    
    model_config = {'from_attributes': True}

    model_config = {'from_attributes': True}
    
class UserProfileData(BaseModel):
    id: str
    
    model_config = {'from_attributes': True}


class UserFullApiResponse(BaseModel):
    id: Optional[PydanticObjectId] = Field(alias='id')
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    email: EmailStr = Field(..., description="User's email, must be unique")
    user_full_name: Optional[str] = Field(None, description="User's full name")
    confirmed: bool = Field(default=False, description="Whether the user is confirmed")
    created_at: datetime = Field(default_factory=datetime.now, description="Account creation timestamp")

    model_config = {'from_attributes': True}

from typing_extensions import Annotated
from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator
from bson import ObjectId as _ObjectId

