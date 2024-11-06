from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from api.models.batch import Batch
from api.models.user import User
from bson import ObjectId
import os
from dotenv import load_dotenv
from api.services.main_process import main_process
from api.services.pinecone_service import upload_to_pinecone
from api.services.s3_service import upload_file_to_s3
from loguru import logger

load_dotenv(override=True)

job_post_router = APIRouter(prefix="/job_post_router", tags=["Job Post Router"])

@job_post_router.post("/upload/{user_id}/{batch_id}")
async def upload_files(user_id: str, batch_id):
    return ""