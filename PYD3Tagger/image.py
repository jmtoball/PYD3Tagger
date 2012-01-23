from PIL import Image, ImageOps
from tempfile import mkstemp

def overlay(fg, bg, mask):
    """Overlays one image with another one using an alphamask."""
    bgimg = Image.open(bg)
    fgimg = Image.open(fg)
    mask = Image.open(mask)
    # The background is cropped to fit the masksize.
    bgimg = ImageOps.fit(bgimg, fgimg.size, method=Image.ANTIALIAS)
    mergedimg = bgimg.convert("RGBA")
    mergedimg.paste(fgimg, mask)
    # Create a temporary file for the image, we won't store it.
    handle, mergedpath = mkstemp(suffix='.png')
    mergedimg.save(mergedpath)
    return mergedpath
