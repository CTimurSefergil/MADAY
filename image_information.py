from PIL import Image, ExifTags
from datetime import datetime

def get_capture_time(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        exif_data = img._getexif() if hasattr(img, '_getexif') else None

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    return dt.isoformat()
    except Exception as e:
        print(f"Error reading EXIF time: {e}")

    return datetime.now().isoformat()