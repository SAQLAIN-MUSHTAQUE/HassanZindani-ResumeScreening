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

    # Upload files to S3 and replace filename with object_key in file_data
    uploaded_files_metadata = []
    for i, (content, filename) in enumerate(file_data):
        s3_url, object_key = await upload_file_to_s3(content, filename)
        
        # Replace filename in file_data with object_key
        file_data[i] = (content, object_key)
        
        # Append metadata for response
        uploaded_files_metadata.append({"object_key": object_key, "s3_url": s3_url})
        
        # Update database with S3 object key and URL
        uploaded_files.append({object_key:{"url_link": s3_url}})

    # Save the batch with updated file list in the database
    batch.save()

    # Process the files (e.g., extract text, perform OCR, etc.)
    # Assuming the processing uses the S3 URL as the key
    # If processing requires the actual file bytes, adjust accordingly
    # Here, we're passing the file bytes and filenames
    splitted_docs, raw_text, total_tokens, total_cost = await main_process(file_data, batch, vision_model="gpt-4o-mini")

    cv_list = batch.cv_list
    for cv in cv_list:
        cv_name = list(cv.keys())[0]
        if cv_name in raw_text:
            # Assign the raw_text content to the cv
            cv[cv_name]["cv_text"] = raw_text[cv_name]
            logger.debug(f"Updated {cv_name} with cv_text.")
        else:
            logger.warning(f"No raw text found for CV: {cv_name}")

    # Log the updated list to ensure changes were applied
    # logger.debug(f"batch.cv_list after update: {cv_list}")

    # Ensure the batch is saved after updates
    batch.cv_list = cv_list
    # Update the cv_list field in the batch document
    Batch.objects(id=batch.id).update(set__cv_list=cv_list)

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
    #     # Return metadata only, not the file content
    # return {"uploaded_files": uploaded_files_metadata}