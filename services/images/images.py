"""Services for Images controller"""

# Retic
from retic import env, App as app

# Requests
import requests

# Pil
from PIL import Image

# Io
import io

# Base64
import base64

# Uuid
import uuid

# Services
from retic.services.responses import success_response_service, error_response_service
import services.imgur.imgur as imgur

# Utils
from services.general.general import isfile, rmfile

# Contants
PUBLIC_WATERMARKS_FOLDER = app.config.get('PUBLIC_WATERMARKS_FOLDER')
PUBLIC_IMAGES_FOLDER = app.config.get('PUBLIC_IMAGES_FOLDER')
PUBLIC_IMG_NOT_FOUND = app.config.get('PUBLIC_IMG_NOT_FOUND')


def upload_from_url_watermark(urls, width, height, watermark_code=None):
    """Upload images from urls and if the watermarks params contains some
    watermark these will add to images, one in each corner

    :param urls: List of images urls to upload
    :param watermark_code: Code of the watermark to add on each image
    """
    """Define all variables"""
    _images = []

    try:
        """For each url do the following"""
        for _url in urls:
            """Download image from url"""
            _downloaded_image = download_img(_url)
            if _downloaded_image:
                """If watermark exists, add to image"""
                if watermark_code:
                    _downloaded_image = img_watermark(
                        _downloaded_image,
                        width,
                        height,
                        watermark_code
                    )
            else:
                """Upload image base"""
                _downloaded_image = open(PUBLIC_IMG_NOT_FOUND, "rb").read()
            """Upload image to storage"""
            _uploaded_image = imgur.upload_image(
                _downloaded_image
            )
            """Check if it has any problem"""
            if _uploaded_image['success'] is False:
                continue
            else:
                """Add image to list"""
                _images.append((_uploaded_image.get('data')))
        return success_response_service(
            data=_images
        )
    except Exception as err:
        return error_response_service(
            msg=str(err)
        )


def download_img(download_url):
    """Download from the url"""
    req_download = requests.get(download_url)
    """Check if the response has any problem"""
    if req_download.status_code != 200:
        return None
    else:
        """Exit from the loop"""
        return req_download.content


def img_watermark(
    bytes_image,
    width,
    height,
    watermark_code,
):
    """Define file paths"""
    _watermark_path = "{0}/{1}".format(
        PUBLIC_WATERMARKS_FOLDER, watermark_code)
    """Check if mark exists"""
    if not isfile(_watermark_path):
        raise Exception("Watermark not found.")

    """Open the watermark if it exists"""
    _watermark = Image.open(_watermark_path)
    """Load the Image from memory"""
    _base_image = Image.open(io.BytesIO(bytes_image))
    """Get size from images"""
    _img_width = width or _base_image.width
    _img_height = height or _base_image.height
    _watermark_width, _watermark_height = _watermark.size
    """Define the size"""
    _img_size = (_img_width, _img_height,)
    """Resize image"""
    _transparent = _base_image.resize(_img_size)
    """Get the watermark position"""
    _position = (
        int((_img_width-_watermark_width)/2),
        _img_height-(_watermark_height+5)
    )
    """Paste watermark into image"""
    _transparent.paste(_watermark, _position, mask=_watermark)
    """Generate id"""
    _img_code = uuid.uuid1().hex
    """Path of the image"""
    _output_image_path = "{0}/{1}.png".format(PUBLIC_IMAGES_FOLDER, _img_code)
    """Save image"""
    _transparent.save(_output_image_path)
    """Open image"""
    with open(_output_image_path, "rb") as image_file:
        _image = base64.b64encode(image_file.read())
    """Delete image"""
    rmfile(_output_image_path)
    """Return Image"""
    return _image
