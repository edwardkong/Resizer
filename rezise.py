import os
import math
import string
import hashlib
import random
import pymongo
import datetime
import atexit
import binascii
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, request, redirect, url_for, send_file, send_from_directory, session
from PIL import Image, ImageDraw
# from flask_pymongo import PyMongo

f = open("log.txt", "a")

def logHTTP(status):
	f.write("%s [%s] %s %s %s %s %s \n" %(str(datetime.datetime.now()), request.remote_addr, request.method, request.scheme, request.full_path, status, session.get('uname')))
	f.flush()

def log(toLog):
	f.write(str(datetime.datetime.now()) + " " + toLog + "\n")
	f.flush()
	
def saveLog():
	f.close()

atexit.register(saveLog)

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

def allowed_signature(fileBytes):			 
	#gif
	if fileBytes[:8] == "47494638":
		return True
	# jpg
	if fileBytes[:8] == "FFD8FFDB" or fileBytes[:8] == "FFD8FFEE" or fileBytes[:8] == "FFD8FFE1" or fileBytes[:8] == "FFD8FFE0":
		return True
	# png
	if fileBytes[:16] == "89504E470D0A1A0A":
		return True
	return False
	
@app.route('/loadResult/<filename>')
def loadResult(filename):
	# check if user has access to photo
	tmp = users.find_one({"uname": session.get('uname')})
	if(filename not in tmp['imgs']):
		return redirect(url_for('upload'))

	##
	logHTTP("200 Resized")
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
			logHTTP("400 Not valid file")
			flash('No file part')
			return redirect(request.url)
		file = request.files['filename']
		# if user does not select file, browser also
		# submit an empty part without filename
		if file.filename == '':
			print "no selected file"
			logHTTP("400 Not valid file")
			flash('No selected file')
			return redirect(request.url)
		bytes = binascii.hexlify(file.read()).upper()
		if not allowed_signature(bytes):
			logHTTP("400 Not valid file")
			flash('Incorrect File Format')
			return redirect(request.url)
		file.seek(0)
		if file and allowed_file(file.filename):
			print "accepted image"
			filename = session.get('uname')+secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			print "Upload original Successful"
			squarify(filename).save(os.path.join(app.config['UPLOAD_FOLDER'],"new"+filename))
			tmp = users.find_one({"uname": session.get('uname')})
			tmp['imgs'].append("new"+filename)
			users.update_one({"uname": session.get('uname')}, {"$set": tmp}, upsert=False)
			print "Upload resize Successful"
			logHTTP("200 Upload Successful")
			log("[" + request.remote_addr + "] Upload successful: " + filename)
			return redirect(url_for('loadResult',filename="new"+filename))
	print "GET Request"
	return redirect(url_for('upload'))

@app.route("/")
def index():
	logHTTP("200")
	return render_template("login.html")

@app.route("/upload")
def upload():
	if session.get('uname') == None:
		logHTTP("401 Not authorized")
		log("[" + request.remote_addr + "] Invalid session")
		print "not logged in, redirect"
		return redirect(url_for('index'))	
	logHTTP("200")
	#adds session imgs
	##
	tmp = users.find_one({"uname": session.get('uname')})
	session['images'] = tmp['imgs']
	# session.pop('images', None)
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
				"uname": checkUname,
				"hash": newhash,
				"salt": salt,
				"imgs": []
			}
			users.insert_one(tmp)
			log("[" + request.remote_addr + "] Registration successful: " + checkUname)
			flash("User Successfully registered")
			logHTTP("200 User Registered")
			return redirect(url_for('index'))
		logHTTP("302 Registration Unsuccessful")
		log("[" + request.remote_addr + "] Registration unsuccessful: " + checkUname)
		flash("Username already taken, please select a different username")
		return redirect(url_for('index'))
	return redirect(url_for('index'))

@app.route("/login", methods=['GET', 'POST'])
def login():
	checkUname = str(request.form['uname'])
	formatPass = str(request.form['pword'])
	toCheck = users.find_one({"uname": checkUname})
	if request.method == "POST":
		if(toCheck == None):
			logHTTP("302 Failed Login")
			log("[" + request.remote_addr + "] Login attempt, no username match: " + checkUname)
			flash("Sorry, login has failed. Please check your credentials.")
			return redirect(url_for('index'))
		fullStr = checkUname + formatPass + toCheck["salt"]
		newhash = hashlib.sha256(fullStr).hexdigest()
		if(newhash == toCheck["hash"]):
			session['uname'] = checkUname
			logHTTP("200 Login Successful")
			log("[" + request.remote_addr + "] Login successful: " + checkUname)
			return redirect(url_for('upload'))
		logHTTP("302 Failed Login")
		log("[" +request.remote_addr + "] Login attempt, password mismatch: " + checkUname)
		flash("Sorry, login has failed. Please check your credentials.")
	return redirect(url_for('index'))

@app.route('/logout')
def logout():
	if session.get('uname') != True:
		logHTTP("200 Logged Out")
		print "logged out"
		log("[" +request.remote_addr + "] Logout successful: " + session.get('uname'))
		session.pop('uname', None)
	return redirect(url_for('index'))	

@app.errorhandler(404)
def page_not_found(e):
	logHTTP("404 Not Found")
	return render_template('404.html'), 404	
	
if __name__ == '__main__':
    app.run(debug=True)