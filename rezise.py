import os
import math
import string
import hashlib
import random
import pymongo
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, request, redirect, url_for, send_file, send_from_directory, session
from PIL import Image, ImageDraw
# from flask_pymongo import PyMongo

client = MongoClient()
db = client['squarify']
users = db['Users']

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
# app.config["MONGO_URI"] = "mongodb://localhost:27017/squarify"
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
			filename = session.get('uname')+secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			print "Upload original Successful"
			squarify(filename).save(os.path.join(app.config['UPLOAD_FOLDER'],"new"+session.get('uname')+filename))
			print "Upload resize Successful"
			return redirect(url_for('loadResult',filename="new"+session.get('uname')+filename))
	print "GET Request"
	return redirect(url_for('upload'))

@app.route("/")
def index():
	return render_template("login.html")

@app.route("/upload")
def upload():
	if session.get('uname') == None:
		print "not logged in, redirect"
		return redirect(url_for('index'))	
	return render_template("upload.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
	if request.method == "POST":
		salt = str(random.randint(1, 1000))
		checkUname = str(request.form['uname'])
		formatPass = str(request.form['pword'])
		fullStr = checkUname + formatPass + salt
		newhash = hashlib.sha256(fullStr).hexdigest()
		if(users.find_one({"uname": checkUname}) == None):
			tmp = {
				"uname": request.form['uname'],
				"hash": newhash,
				"salt": salt
			}
			users.insert_one(tmp)
			return "Successfully register, please go back to login"
		return "Username already taken, please go back and try again"
	return redirect(url_for('index'))

@app.route("/login", methods=['GET', 'POST'])
def login():
	checkUname = str(request.form['uname'])
	formatPass = str(request.form['pword'])
	toCheck = users.find_one({"uname": checkUname})
	if request.method == "POST":
		if(toCheck == None):
			return "Sorry, login has failed. Please check your credentials."
		fullStr = checkUname + formatPass + toCheck["salt"]
		newhash = hashlib.sha256(fullStr).hexdigest()
		if(newhash == toCheck["hash"]):
			session['uname'] = checkUname;
			return redirect(url_for('upload'))
		return "Sorry, login has failed. Please check your credentials."
	return redirect(url_for('index'))

@app.route('/logout')
def logout():
	if session.get('uname') != True:
		print "logged out"
		session.pop('uname', None)
	return redirect(url_for('index'))	

if __name__ == '__main__':
    app.run(debug=True)