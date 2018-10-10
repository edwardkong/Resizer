import math
import string
from PIL import Image, ImageDraw

newW = 240
newH = 240

inIm = Image.open("input.png")
#im = inIm.resize((newW, newH), Image.ANTIALIAS)

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

# im.show()
im.save("output.png")
