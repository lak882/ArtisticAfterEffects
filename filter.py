import os
import sys
from random import randrange

from wand.image import Image as wandImage
from PIL import Image, ImageFilter, ImageEnhance, ImageOps

import re
from filter.recluster import Recolor, Rehatch, Remap

# other commands to feed to filters
commands = []
filters = ['noir', 'sepia', 'vignette', 'vintage', 'recolor', 'remap', 'pixelate', 'dots', 'pencil']

def noir(image):
    """Noir filter emulating black-and-white films.
    Usage: filter.py noir {image path}"""
    # make image greyscale
    image.modulate(100,0,100)
    # adjust levels
    image.level(0.3,0.7,1.0)

def sepia(image):
    """Sepia filter emulating early tinted photography.
    Usage: filter.py sepia {image path}"""
    # add sepia tone to image and vignette
    image.sepia_tone(threshold=0.8)

def vignette(image):
    """Create vignette around image.
    Usage: filter.py vignette {image path}"""
    # create vignette
    image.vignette(sigma=50, x=1, y=1)

def vintage(image):
    """Vintage filter emulating 70s, 80s photography.
    Usage: filter.py vintage {image path}"""
    # motion blur along image
    # random angle for blur between -90, -45, 0, 45, 90
    v = randrange(-90, 90, 45)
    image.motion_blur(radius=4, sigma=8, angle=v)

    # composite dirt for grain effect
    with wandImage(filename = "filter/dirt.png") as dirt:
        # make size of image
        dirt.resize(image.width, image.height)
        image.composite(dirt)

    # composite faded sepia image on top of orignal as blend
    with image.clone() as converted:
        converted.sepia_tone(1.0)
        image.composite_channel(channel='all_channels', image=converted,
                                    operator='blend')

def isValidHex(hex):
    """Helper method for hexToRGB.
    Check if the hexcode is valid."""
    # regex to check valid hexadecimal color code
    regex = "[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3}"
    # compile the regex
    p = re.compile(regex)
    # check that hex is not empty
    # check that hex agrees with the regex
    return hex != None and re.search(p, hex)

def hexToRGB(hex):
    """Helper method for moasic.
    Convert hash to tuple representing rgb values."""
    # check if it's a valid hex input
    if not isValidHex(hex):
        print("{} is an invalid hexcode.".format(hex))
        exit()
    # create tuple representing rgb
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

def recolor(image):
    """Recolor filter recoloring reduced colors for striking effect.
    One example is the Obama "Change" image from 2008.
    Takes 2 or more hex commands from user.
    Usage: filter.py noir {image path} {2+ hex codes}"""
    # check that user inputed at least to hexcodes
    if len(commands) <= 2:
        print("At least 2 hex codes are required for the mosaic filter")
        exit()
    # convert hexcodes to rgb and into list
    rgbInput = []
    for c in commands:
        rgbInput.append(hexToRGB(c))
    # blur image to smooth out edges
    result = image.filter(ImageFilter.GaussianBlur(2))
    # recolor clusters of color as input colors
    result = Recolor(result, len(rgbInput), rgbInput).image()
    return result

def remap(image):
    """Remaps based on map. White parts become back image; everything
    else becomes front image.
    Usage: filter.py noir {map image path} {front image path} {back image path}"""
    if len(commands) < 2:
        print("Need 3 images: Map, Front Image, Back Image")
        exit()
    map = image
    front = Image.open(commands[0])
    back = Image.open(commands[1])
    result = Remap(map, front, back).image()
    return result

def square(image, style):
    """Changes the image based on a square size and style."""
    # increase contrast, s.t image reads better
    image = ImageEnhance.Contrast(image).enhance(2.0)
    # default size of square is 5x5 pixels
    if len(commands) == 0:
        square = 5
    else: square = int(commands[0])
    result = Rehatch(image, square, '{}'.format(style)).image()
    return result

def pixelate(image):
    """Pixelates image.
    Usage: filter.py pixelate {image path} {optional square size}"""
    return square(image, 'bucket')

def pencil(image):
    """Replaces value squares with pencil marking to emulate a pencil
    value drawing.
    Usage: filter.py pencil {image path} {optional square size}"""
    return square(image, 'pencil')

def dots(image):
    """Replaces values square with stippling emulating a "hatched" look
    similar to the Wall Street Journal Portraits.
    Usage: filter.py dots {image path} {optional square size}"""
    return square(image, 'dots')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: filter.py {image} {filter} {other commands}.")
        exit()

    # get filter name & other commands for filter to use
    filterName = sys.argv[1]
    # check if this is actually function
    if filterName not in filters:
        print("The filter {} does not exsist.".format(filterName))
        quit()

    # get image path and then convert to image object
    imagePath = sys.argv[2]
    # check if this path actually contains an image
    try:
        with open(imagePath) as _:
            pass
    except:
        print("The image at {} does not exsist".format(imagePath))
        exit()

    # find the filter that user inputed and apply to image
    commands = sys.argv[3:]
    # get imageName to save it
    imageName = os.path.basename(imagePath)
    #ImageMagick filters
    if (filterName == 'noir' or filterName == 'sepia' or
        filterName == 'vintage'):
        # get image
        image = wandImage(filename = imagePath)
        # do effects
        locals()[filterName](image)
        # get base name of image; ex: images/boris.jpeg => brois.jpeg
        # then save filterd image in folder  "results" as "filterName_imageName"
        image.save(filename = 'results/{}_{}'.format(filterName, imageName))

    #K-Means(PIL) filters
    else:
        # get image
        image = Image.open(imagePath)
        # get result from applying effects
        result = locals()[filterName](image)
        # get base name of image; ex: images/boris.jpeg => brois.jpeg
        # then save filterd image in folder  "results" as "filterName_imageName"
        result.save('results/{}_{}'.format(filterName, imageName), format='png')
