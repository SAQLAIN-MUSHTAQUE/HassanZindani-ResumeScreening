from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from bson import ObjectId
from dotenv import load_dotenv
from api.schemas.job_post import JobPostRequestSchema
from api.services.cv_anazlyzing_service import analyzing_process
from api.models.batch import Batch
from api.models.job_post import JobPost
from loguru import logger

load_dotenv(override=True)

job_post_router = APIRouter(prefix="/job_post_router", tags=["Job Post Router"])

# Make the body for Job Post query
@job_post_router.post("/upload/")
async def upload_files(payload: JobPostRequestSchema):# Make the body for Job Post query
    
    # Validate Bash
    batch = Batch.objects.filter(id=ObjectId(payload.batch_id), userId=ObjectId(payload.user_id)).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"User with id: {payload.user_id} not found")
    
    # Creating New Job Post Entry
    job_post = JobPost(userId=ObjectId(payload.user_id), batchId=ObjectId(payload.batch_id), job_post=payload.query)
    job_post.save()
    
    result = await analyzing_process(batch, job_post, payload.query)
    
    return result

# Getting all job posts for the given user and batch
@job_post_router.get("/all_post/{user_id}/{batch_id}")
async def get_all_job_post_by_user_batch_id(user_id: str, batch_id: str):
    """
    Get all job posts for a given user and batch.
    """
    try:
        job_posts = JobPost.objects.filter(userId=ObjectId(user_id), batchId=ObjectId(batch_id)).all()
        
        # Convert ObjectId fields to strings
        return [
            {**job.to_mongo().to_dict(), "_id": str(job.id), "userId": str(job.userId), "batchId": str(job.batchId)}
            for job in job_posts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
