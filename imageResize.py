import os
import math
import string
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, request, redirect, url_for, send_file, send_from_directory
from PIL import Image, ImageDraw

#inIm = Image.open("input.png")
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

#squarify(inIm).save("output.png")

UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#print(app.config)

@app.route('/', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            inIm = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            squarify(inIm).save("output.png")
            return send_file('output.png')

    return send_from_directory(app.config['UPLOAD_FOLDER'], 'upload.html')
		
if __name__ == '__main__':
    app.run()