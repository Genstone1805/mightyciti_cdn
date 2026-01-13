import hashlib
from django.views.decorators.cache import cache_page
from PIL import ImageOps


from django.http import HttpResponse, Http404
from django.conf import settings
from PIL import Image
import os
from io import BytesIO



CACHE_DIR = os.path.join(settings.MEDIA_ROOT, "cdn_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def make_cache_key(path, width, height):
    raw = f"{path}:{width}:{height}"
    return hashlib.md5(raw.encode()).hexdigest() + ".webp"

def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
    

def get_optimal_quality(width):
    if not width:
        return 80  # default fallback
    
    width = int(width)
    if width <= 240:
        return 50
    elif width <= 480:
        return 60
    elif width <= 960:
        return 70
    else:
        return 80
    

@cache_page(1800)
def cdn_image(request, path):
    # path = path.rstrip('/')
    try:
        width = safe_int(request.GET.get("w"))
        height = safe_int(request.GET.get("h"))

        if width: width = int(width)
        if height: height = int(height)

        cache_key = make_cache_key(path, width, height)
        cache_path = os.path.join(CACHE_DIR, cache_key)

        # Serve cached version if exists
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return HttpResponse(f.read(), content_type="image/webp")
            
        try:
            img = Image.open(path)
        except FileNotFoundError:
            raise Http404("Image not found")

        # Resize using fast algorithm
        if width or height:
            img = ImageOps.fit(img, (width or img.width, height or img.height), Image.LANCZOS)

        
        buffer = BytesIO()
        if width:
            quality = get_optimal_quality(width)
            img.save(buffer, "WEBP", quality=quality)
        else:
            img.save(buffer, "WEBP", quality=85)

        # Save to cache
        with open(cache_path, "wb") as f:
            f.write(buffer.getvalue())

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="image/webp")
        response["Cache-Control"] = "public, max-age=31536000"
        return response
    except BrokenPipeError:
       return HttpResponse(status=499)
    except Exception as e:
        return HttpResponse(f"Image processing error: {str(e)}", status=500)