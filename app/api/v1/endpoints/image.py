from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_admin_user
from app.utils.upload import save_uploaded_file
from app.services.product_service import ProductService
from app.schemas.product_schema import ImageResponse

router = APIRouter()

@router.post("/{product_id}/upload-image", response_model=ImageResponse)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Query(False),
    db: Session = Depends(get_db),
    admin_user = Depends(get_admin_user)
):
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Content type validate karein
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    image_url = save_uploaded_file(file)
    db_image = product_service.add_image(product_id=product_id, image_url=image_url, is_primary=is_primary)
    return db_image

@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(get_admin_user)
):
    product_service = ProductService(db)
    deleted = product_service.delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    return None

@router.put("/images/{image_id}/set-primary", response_model=ImageResponse)
def set_primary_image(
    image_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(get_admin_user)
):
    product_service = ProductService(db)
    
    # Get image to find product_id
    from app.models.product import ProductImage
    db_image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    updated = product_service.set_primary_image(db_image.product_id, image_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Image not found")
    return updated