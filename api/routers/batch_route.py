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

from api.services.user_services import get_user_by_id

load_dotenv(override=True)

# AWS Bucket
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

batch_router = APIRouter(prefix="/batch", tags=["Batch"])

@batch_router.post("/upload/{user_id}")
async def upload_files(user_id: str, files: List[UploadFile] = File(...)):
    """
    Upload multiple files (.pdf or .docx) to AWS S3, process them, and return the extracted data.
    """
    # Validate and read all files into memory
    file_data = []
    for file in files:
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        content = await file.read()
        file_data.append((content, file.filename))
        
    # Check if user exists in the database
    user_db = User.objects.get(id=ObjectId(user_id))
    if not user_db:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} not found")
    
    # Initialize a new batch for the user
    batch = Batch(userId=ObjectId(user_id), cv_data = {})

    batch.save() 
    logger.debug(f"Batch data before save: {batch.to_mongo()}")

    uploaded_files = batch.cv_data

    # Upload files to S3 and replace filename with object_key in file_data
    uploaded_files_metadata = []
    for i, (content, filename) in enumerate(file_data):
        s3_url, object_key = await upload_file_to_s3(content, filename)
        
        # Replace filename in file_data with object_key
        file_data[i] = (content, object_key)
        
        # Append metadata for response
        uploaded_files_metadata.append({"object_key": object_key, "s3_url": s3_url})
        
        # Update database with S3 object key and URL
        uploaded_files[object_key] = {"url_link": s3_url}

    # Save the batch with updated file list in the database
    Batch.objects(id=batch.id).update(set__cv_data=uploaded_files)
    batch.reload()

    # Process the files (e.g., extract text, perform OCR, etc.)
    # Assuming the processing uses the S3 URL as the key
    # If processing requires the actual file bytes, adjust accordingly
    # Here, we're passing the file bytes and filenames
    splitted_docs, raw_text, total_tokens, total_cost = await main_process(file_data, batch, vision_model="gpt-4o-mini")

    cvs_dictionary = batch.cv_data
    for key, value in cvs_dictionary.items():
        if key in raw_text:
            # Assign the raw_text content to the cv
            value["cv_text"] = raw_text[key]
            logger.debug(f"Updated {key} with cv_text.")
        else:
            logger.warning(f"No raw text found for CV: {key}")

    # # Update database
    Batch.objects(id=batch.id).update(set__cv_data=cvs_dictionary)

    # Reload batch to ensure changes are reflected
    batch.reload()

    # Upload to Pinecone
    pinecone_upload= await upload_to_pinecone(batch_id= str(batch.id),
                              splitted_docs= splitted_docs)

    response = {
        "pinecone_upload": pinecone_upload,
        "all_raw_text": raw_text,
        "total_tokens": total_tokens,
        "total_cost": total_cost
    }

    return response


# Getting all the batch for the given user
@batch_router.get("/{user_id}")
async def get_batches_by_user_id(user_id: str):
    """
    Get all batches for a given user.
    """
    try:
        # Getting User Document
        user_dict = await get_user_by_id(user_id)
        if not user_dict:
            raise HTTPException(status_code=404, detail=f"User with id: {user_id} not found")

        # Getting all batches for the user
        batches = Batch.objects.filter(userId=ObjectId(user_id)).all()

        # Convert ObjectIds to strings
        return [
            {**batch.to_mongo().to_dict(), "_id": str(batch.id), "userId": str(batch.userId)}
            for batch in batches
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))