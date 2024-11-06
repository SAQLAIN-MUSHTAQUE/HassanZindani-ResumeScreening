from pydantic import BaseModel, Field
from bson import ObjectId

class JobPostRequestSchema(BaseModel):
    user_id: str = Field(..., description="ID of the user uploading the files")
    batch_id: str = Field(..., description="ID of the batch associated with the upload")
    query: str = Field(..., description="Query string for the job post")