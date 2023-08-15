# A program to recolor images by clustering related colors.
"""
A program to recolor images by clustering related colors.
Use in the following way:
    python3 recolor.py image.png k
image.png defaults to 'bedroom.png'; k defaults to 8.
The result will appear in image-k.png.
"""
from PIL import Image, ImageDraw  # From the 'pillow' extension
from cluster import *
from random import randint

__all__ = ( 'colorDist', 'colorMean', 'Recolor')

def colorMean(colors):
    """Compute the mean of a sequence of colors."""

    n = len(colors)
    # if the color list is empty, return random color
    # triple of 3 random int between 0 and 255, inclusive
    if n == 0:
        return (randint(0, 255), randint(0, 255), randint(0, 255))
    rmean = sum(r for r,_,_ in colors)//n
    gmean = sum(g for _,g,_ in colors)//n
    bmean = sum(b for _,_,b in colors)//n
    return (rmean, gmean, bmean)

def colorDist(c0, c1):
    """Compute the distance between two colors."""
    dr = c0[0] - c1[0]
    dg = c0[1] - c1[1]
    db = c0[2] - c1[2]
    return (dr*dr + dg*dg + db*db)**0.5

# Classic colors:
WHITE = (255,255,255)
BLACK = (0,0,0)

class Smooth(object):
    """Recolor an image replacing k-clustered colors with input colors.
    Makes use of a clustering of 'k' values."""
    __slots__ = ['_width', '_height', '_image', '_px', '_clust', '_k', '_smoothK']

    def __init__(self, img, k=40, smoothK=20):
        self._image = img
        self._width,self._height = img.size
        self._px = img.load()
        # here, we cluster based on unique r-g-b tuples that represent the colors
        pixelSet = { self._px[x,y][:3] for y in range(self.height) for x in range(self.width)}
        self._clust = findClustering(pixelSet, k, colorMean, colorDist)
        self._k = k
        self._smoothK = smoothK

    @property
    def width(self):
        """The width of the image produced by this filter."""
        return self._width

    @property
    def height(self):
        """The height of the image produced by this filter."""
        return self._height

    def image(self, showColors = False):
        """Generate an image from this filter.
        If showColors is True, the palette is drawn below the image."""

        # create a new image.  Includes palette, if showColors is True.
        width, height = self.width, self.height
        palatteHeight = self.height//10 if showColors else 0
        i = Image.new("RGB",(width,height+palatteHeight),WHITE)

        # generate image by classifying all the colors
        clustering = self._clust
        for y in range(height):
            for x in range(width):
                # grab the original color
                c = self._px[x,y][:3]
                # generate the new color
                newC = clustering.label[ clustering.classify(c) ]
                # paint it into the image
                ImageDraw.Draw(i).point((x,y), newC)

        # if showColors, at bottom, build a palette of k color swatches
        k = clustering.k
        # compute the width of the palette bars
        palWid = (width+k-1)//k
        for py in range(palatteHeight):
            y = py + height
            for x in range(i.width):
                swatchIndex = x//palWid
                swatch = clustering.label[swatchIndex]
                ImageDraw.Draw(i).point((x,y),swatch)
        return i
    #!
    def smooth(self):
        """Return clusters from image in a smoothed out way."""
        if (self._k < self._smoothK):
            return self
        else:
            return Smooth(self.image(), (self._k)//2).smooth()
    #!
