from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from api.models.batch import Batch
from api.models.user import User
from bson import ObjectId
import os
from dotenv import load_dotenv
from api.services.s3_service import upload_file_to_s3

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
    batch = Batch.objects.filter(userId = ObjectId(user_id)).first()
    if not batch:
        batch = Batch(userId=ObjectId(user_id))
    uploaded_files = batch.cv_list

    # Upload files to S3 and collect metadata
    uploaded_files_metadata = []
    for content, filename in file_data:
        s3_url, object_key = await upload_file_to_s3(content, filename)
        
        # Append metadata for response
        uploaded_files_metadata.append({"filename": filename, "s3_url": s3_url})
        
        # Update database with S3 object key and URL
        uploaded_files.append({object_key:s3_url})

    # Save the batch with updated file list in the database
    batch.save()

    # Process the files (e.g., extract text, perform OCR, etc.)
    # Assuming the processing uses the S3 URL as the key
    # If processing requires the actual file bytes, adjust accordingly
    # Here, we're passing the file bytes and filenames
    # processed_docs, raw_text, total_tokens, total_cost = await main_process(file_data, vision_model="gpt-4o-mini")

    # response = {
    #     "loaded_docs": processed_docs,
    #     "all_raw_text": raw_text,
    #     "total_tokens": total_tokens,
    #     "total_cost": total_cost
    # }

    # return response
        # Return metadata only, not the file content
    return {"uploaded_files": uploaded_files_metadata}