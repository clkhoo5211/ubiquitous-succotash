import asyncio
import io
from PIL import Image
from tests.unit.test_media_service import MockUploadFile
from src.services.media_service import MediaService

async def test():
    # Create media service
    media_service = MediaService()
    
    # Create mock file
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    
    upload_file = MockUploadFile(
        file=img_bytes,
        filename="test_image.jpg",
        content_type="image/jpeg",
    )
    
    # Try to read the file
    content = await upload_file.read()
    print(f"File read successfully: {len(content)} bytes")
    
    # Reset for service
    img_bytes.seek(0)
    
asyncio.run(test())
