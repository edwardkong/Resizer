import os
import math
import string
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, request, redirect, url_for, send_file, send_from_directory
from PIL import Image, ImageDraw

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "Plaintext_Secret_Key"
# app.config['APP_ROOT'] = os.path.dirname(os.path.abspath(__file__))

newW=240
newH=240
def squarify(filename):
	inIm = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	im = inIm.resize((newW, newH), Image.ANTIALIAS)
#	pic = inIm.load()
#	
#	inW, inH = inIm.size
#    # print(inW, inH)
#
#	dW = inW/newW
#	dH = inH/newH
#    # print(dW, dH)
#
#	im = Image.new("RGBA", (newW, newH), (255, 255, 255, 0))
#	img = ImageDraw.Draw(im)
#
#	for x in range(0, newW):
#		for y in range(0, newH):
#			pixColor = '%02x%02x%02x%02x' % pic[int(dW * x), int(dH * y)]
#			img.point((x, y), "#"+pixColor)
#
#	print "finish resizing"
	return im

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/loadResult/<filename>')
def loadResult(filename):
	print "Upload Successful"
	print filename
	return render_template("resized.html",imagesrc=filename)

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
	if request.method == 'POST':
		print "POST Request"
		print request.files
		# check if the post request has the file part
		if 'filename' not in request.files:
			print "invailid file"
			flash('No file part')
			return redirect(request.url)
		file = request.files['filename']
		# if user does not select file, browser also
		# submit an empty part without filename
		if file.filename == '':
			print "no selected file"
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			print "accepted image"
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			print "Upload original Successful"
			squarify(filename).save(os.path.join(app.config['UPLOAD_FOLDER'],"new"+filename))
			print "Upload resize Successful"
			return redirect(url_for('loadResult',filename="new"+filename))
	print "GET Request"
	return redirect(url_for('index'))	

@app.route("/")
def index():
	return render_template("upload.html")

@app.route("/hello")
def hello():
    return "Hello World!"
	
if __name__ == '__main__':
    app.run(debug=True)