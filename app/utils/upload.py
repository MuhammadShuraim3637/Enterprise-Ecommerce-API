import os
import uuid
from fastapi import UploadFile

UPLOAD_DIR = "static/uploads/products"

def save_uploaded_file(file: UploadFile) -> str:
    # Ensure directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Unique filename generation taake overrides na hon
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
        
    # Uniform resource locator route path return karega
    return f"/static/uploads/products/{unique_filename}"