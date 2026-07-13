from io import BytesIO
from PIL import Image

def compress_image(image_data: bytes, max_size: int = 512, quality: int = 80) -> bytes:
    """
    Resizes and compresses an image to save tokens and bandwidth.
    
    :param image_data: Raw image bytes.
    :param max_size: Maximum width or height of the image.
    :param quality: JPEG quality (1-100).
    :return: Compressed image bytes as JPEG.
    """
    if not image_data:
        return image_data

    try:
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB (required for JPEG and removes alpha channel)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        # Resize if necessary while maintaining aspect ratio
        width, height = img.size
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        # Fallback to original data if processing fails
        print(f"DEBUG: Image compression failed: {e}")
        return image_data
