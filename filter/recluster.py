# A program to cluster colors and replace them with a different kind of cluster.
"""
A program to cluster colors and
replace them with a different kind of cluster.
"""
from PIL import Image, ImageDraw  # From the 'pillow' extension
from cluster import *
from random import randint, randrange

from collections import OrderedDict
import itertools as it

import sys
sys.setrecursionlimit(5000)

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

class Recluster(object):
    """Recolor an image replacing k-clustered colors with input colors.
    Makes use of a clustering of 'k' values."""
    __slots__ = ['_width', '_height', '_image', '_px']

    def __init__(self, img):
        self._image = img
        self._width,self._height = img.size
        self._px = img.load()

    @property
    def width(self):
        """The width of the image produced by this filter."""
        return self._width

    @property
    def height(self):
        """The height of the image produced by this filter."""
        return self._height

    def brightnessRGBDict(self, RGBList):
        """From a list of rgb tuples,
        generate an ordered dictionary between brightness and rgb."""
        # temporary dictonary to hold rgb values
        d = {}
        # get every rgb tuple in list
        for rgb in RGBList:
            # get brightness by averaging r, g, b values
            brightness = 0
            for color in rgb:
                brightness += (color / 3)
            # key is brightness, value is rgb tuple
            d[brightness] = rgb
        # convert ordered dict to keep values sorted by brightness
        brightnessRGBDict = OrderedDict(sorted(d.items()))
        return brightnessRGBDict

class Recolor(Recluster):
    """Takes list of rgb tuples as input.
    Replaces clusters colors with input colors."""
    __slots__ = ['_clust', '_input']

    def __init__(self, img, k, input):
        # create cluster
        super().__init__(img)
        # here, we cluster based on unique r-g-b tuples that represent the colors
        pixelSet = { self._px[x,y][:3] for y in range(self.height) for x in range(self.width)}
        self._clust = findClustering(pixelSet, k, colorMean, colorDist)
        # get input
        self._input = input

    def clusterInputDict(self):
        """Generate a dictonary between cluster colors and input colors in
        order of light to dark."""
        # make dict from light to dark rgb tuples from clusters
        clusters = self._clust.label
        clustersDict = self.brightnessRGBDict(clusters)
        input = self._input
        # make dict from light to dark rgb tuples from input
        inputDict = self.brightnessRGBDict(input)
        # assocaite each cluster color with each input color,
        # both already in light to dark order
        clusterInputDict = {}
        for cluster, input in zip(clustersDict.values(), inputDict.values()):
                clusterInputDict[ cluster ] = input
        return clusterInputDict

    def image(self):
        """Generate an image replacing cluster colors with input colors."""
        # create a new image
        width, height = self.width, self.height
        i = Image.new("RGB",(width,height),WHITE)
        # generate image by classifying all the colors
        clustering = self._clust
        # get dictonary of cluster color to input color
        clusterInputDict = self.clusterInputDict()
        for y in range(height):
            for x in range(width):
                # grab the original color
                c = self._px[x,y][:3]
                # generate clustered color
                clusterC = clustering.label[ clustering.classify(c) ]
                # get associated input color
                inputC = clusterInputDict[ clusterC ]
                # paint it into the image
                ImageDraw.Draw(i).point((x,y), inputC)
        return i

class ReclusterDFS(Recluster):
    """Includes Depth-First Search to find neighboring pixels with same color."""
    __slots__ = ['_visited']

    def __init__(self, map):
        super().__init__(map)
        # keeps track of all the pixels that have been visited by DFS
        self._visited = []

    def dfs(self, color, pixel):
        """Depth-First Search for neighboring pixels with same color.
        Returns list of pixel and neighbors with same color."""
        pixelList = [ pixel ]
        # get x, y points of pixel
        x, y = pixel[0], pixel[1]
        # check that x + 1 is within the bounds of image
        # then get right neighbor
        if (x + 1) < (self.width - 1):
            rightNeighbor = [x+1, y]
            pixelList = self.addNeighbor(color, pixelList, rightNeighbor)
        # repeat for bottom neighbor
        if (y + 1) < (self.height - 1):
            bottomNeighbor = [x, y+1]
            pixelList = self.addNeighbor(color, pixelList, bottomNeighbor)
        # return list of itself and all its neigbors with same color
        return pixelList

    def addNeighbor(self, color, pixelList, neighbor):
        """Adds neighbor to pixel list, if it has the same color and has not
        been visited."""
        # get x, y points of neighbor
        nX, nY = neighbor[0], neighbor[1]
        # get color of neighbor
        mapColor = self._px[ nX, nY ]
        # if this neighbor has not already been visited and
        # is the same color as pixel
        # then add it to visited & search its neighbors
        if ( neighbor not in self._visited ) and ( mapColor == color ):
            self._visited.append( neighbor )
            pixelList.extend( self.dfs(color, neighbor) )
        return pixelList

class Remap(ReclusterDFS):
    """Remaps pixels depending on given map. All white pixels will be
    back image and all other pixels will be front image."""
    slots = ['_front', '_frontPX', '_back', '_backPx']

    def __init__(self, map, front, back):
        super().__init__(map)
        # get front image and then resize
        self._front = self.resizeToMap(front)
        self._frontPx = self._front.load()
        # get back image and then resize
        self._back = self.resizeToMap(back)
        self._backPx = self._back.load()

    def resizeToMap(self, image):
        """Resizes image to fit the map."""
        # get aspect ratio of map and image
        mapAspectRatio = self.width / self.height
        imageAspectRatio = image.width / image.height
        # if image has a greater width apsect,
        # then its height must be resized
        if imageAspectRatio > mapAspectRatio:
            # new image width = ( map height / image height ) * image width
            # new image height = map height
            mapHeight = self.height
            hpercent = (mapHeight/float(image.size[1]))
            wsize = int((float(image.size[0])*float(hpercent)))
            image = image.resize((wsize,mapHeight), Image.ANTIALIAS)
        # otherwise the image has a greater height aspect,
        # then its width must be resized
        # ( or it has the same aspect ratio, in which case it dosen't matter )
        else:
            # new image width = map width
            # new image height = ( map width / image width ) * image height
            mapWidth = self.width
            wpercent = (mapWidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((mapWidth,hsize), Image.ANTIALIAS)
        return image

    def image(self):
        """Creates an image that maps all the back pixels onto
        the white pixels of the map and all the front pixels onto
        the black pixels of the map."""
        # create a new image
        width, height = self.width, self.height
        i = Image.new("RGB",(width,height),WHITE)

        # for the y and x pixels
        for y in range(height):
            for x in range(width):
                # define pixel
                pixel = [x, y]
                # if pixel has already been visited, skip it
                if pixel in self._visited:
                    continue
                self._visited.append(pixel)
                # get the color of pixel
                color = self._px[x,y][:3]
                # get all the neighbors with the same color
                neighborList = self.dfs(color, pixel)
                # if the color is white, then it's the background image
                if color == (255, 255, 255):
                    colorImage = self._backPx
                # otherwise it's the front image
                else:
                    colorImage = self._frontPx
                for neighbor in neighborList:
                    nX, nY = neighbor[0], neighbor[1]
                    newC = colorImage[nX, nY]
                    ImageDraw.Draw(i).point((nX, nY), newC)
        return i

class Rehatch(ReclusterDFS):
    """Overlays a chessboard to create "squares" of value on an image.
    Then replaces every square of value with a corresponding value on
    a value scale."""
    slots=['_square', '_dots', '_start', '_startPx']

    def __init__(self, start, square, style):
        self._square = square
        self._dots = {}
        # get the value scale, based on the style
        for value in range(10):
            dot = Image.open("filter/{}/{}.png".format(style, value))
            self._dots[value] = dot.resize((self._square, self._square), Image.NEAREST)
        self._start = self.cropToSquare(start)
        self._startPx = self._start.load()
        map = self.chessboard( self._start.width, self._start.height )
        super().__init__(map)

    def cropToSquare(self, image):
        """Returns cropped image that can be cut into square pixel tiles.
        Ex.: if square is 10x10: 1813x2013 => 1810x2010."""
        nWidth = image.width - ( image.width % self._square )
        nHeight = image.height - ( image.height % self._square )
        image = image.crop((0, 0, nWidth, nHeight))
        return image

    def chessboard(self, width, height):
        """Creates chessboard with size (width x height) of 5x5 squares"""
        w, h = width//self._square, height//self._square
        img = Image.new("RGB", (w,h))
        pixels = img.load()
        # make pixels white, where row+col is odd
        for i in range(w):
            for j in range(h):
                if (i+j)%2:
                    pixels[i,j] = (255,255,255)
        # then resize back to square-size chess fields
        img = img.resize((self._square*w, self._square *h), Image.NEAREST)
        return img

    def image(self):
        # create a new image
        width, height = self.width, self.height
        i = Image.new("RGBA",(width,height),WHITE)

        # for the y and x pixels
        for y in range(height):
            for x in range(width):
                # define pixel
                pixel = [x, y]
                # if pixel has already been visited, skip it
                if pixel in self._visited:
                    continue
                # get the color of pixel
                color = self._px[x,y][:3]
                # get all the neighbors with the same color
                neighborList = self.dfs(color, pixel)
                colorSet = set()
                for neighbor in neighborList:
                    nX, nY = neighbor[0], neighbor[1]
                    color = self._startPx[nX, nY]
                    colorSet.add(color)
                # get clustering of all the images in square
                clust = findClustering(colorSet, 1, colorMean, colorDist)
                brightness = 0
                for color in clust._label[0]:
                    brightness += (color / 3)
                # convert brightness from 0 (black) - 255 (white)
                # to 0 (black) - 10 (white) brighness
                brightness = int((brightness / 255) * 10)
                if brightness != 10:
                    hatch = self._dots[brightness]
                    i.paste(hatch, (x, y), mask=hatch)
        return i
