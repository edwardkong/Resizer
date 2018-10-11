import math
import string
from PIL import Image, ImageDraw

inIm = Image.open("input.png")
#im = inIm.resize((newW, newH), Image.ANTIALIAS)

# input image, width, height
def squarify(inIm, newW=240, newH=240):
    pic = inIm.load()

    inW, inH = inIm.size
    # print(inW, inH)

    dW = inW/newW
    dH = inH/newH
    # print(dW, dH)

    im = Image.new("RGBA", (newW, newH), (255, 255, 255, 0))
    img = ImageDraw.Draw(im)

    for x in range(0, newW):
        for y in range(0, newH):
            pixColor = '%02x%02x%02x%02x' % pic[int(dW * x), int(dH * y)]
            img.point((x, y), "#"+pixColor)

    return im

squarify(inIm).save("output.png")
