# services/s3_service.py

import boto3
from botocore.exceptions import ClientError
from typing import Tuple
import uuid
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# AWS configuration
AWS_S3_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

async def upload_file_to_s3(file: bytes, filename: str) -> Tuple[str, str]:
    """
    Uploads a file to AWS S3 and returns the S3 URL and the object key.
    """
    # Create a boto3 S3 client
    s3_client = boto3.client(
        's3',
        region_name=AWS_S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    # Generate a unique key for the file in S3
    unique_id = str(uuid.uuid4().hex[:8])
    object_key = f"{unique_id}_{filename}"

    try:
        # Upload the file
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=object_key,
            Body=file,
            ContentType='application/octet-stream'
        )
        # Generate the S3 URL
        s3_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{object_key}"
        return s3_url, object_key

    except ClientError as e:
        print(e)
        raise e
