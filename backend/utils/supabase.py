import asyncio
from supabase import create_client, Client
from config import settings
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def upload_complaint_photo(file_path: str, file_name: str):
    """Upload complaint photo to Supabase storage"""
    try:
        with open(file_path, 'rb') as f:
            response = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                file=f,
                path=f"complaints/{file_name}",
                file_options={"content-type": "image/jpeg"}
            )
        
        public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(
            f"complaints/{file_name}"
        )
        
        logger.info(f"Photo uploaded: {file_name}")
        return public_url
    except Exception as e:
        logger.error(f"Photo upload failed: {str(e)}")
        return None

async def delete_complaint_photo(file_name: str):
    """Delete complaint photo from Supabase storage"""
    try:
        supabase.storage.from_(settings.SUPABASE_BUCKET).remove([f"complaints/{file_name}"])
        logger.info(f"Photo deleted: {file_name}")
        return True
    except Exception as e:
        logger.error(f"Photo deletion failed: {str(e)}")
        return False
