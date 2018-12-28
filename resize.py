import os
import math
import string
import hashlib
import random
import pymongo
import logging
import logging.config
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask import Flask, render_template, flash, request, redirect, url_for, send_file, send_from_directory, session
from PIL import Image, ImageDraw

client = MongoClient()
db = client['squarify']
users = db['Users']
posts = db['Posts']

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "Plaintext_Secret_Key"


newW=400
newH=400
def squarify(filename):
        inIm = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        im = inIm.resize((newW, newH), Image.ANTIALIAS)
        return im

def allowed_file(filename):
        return '.' in filename and \
                        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/loadResult/<filename>')
def loadResult(filename):
        print("Upload Successful")
        print(filename)
        return render_template("resized.html",imagesrc=filename)

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
        if request.method == 'POST':
                print("POST Request")
                print(request.files)
                if 'filename' not in request.files:
                        app.logger.error(session.get('uname') + ' // Invalid file/File not found')
                        print("invailid file")
                        flash('No file part')
                        return redirect(request.url)
                file = request.files['filename']
                if file.filename == '':
                        app.logger.error(session.get('uname') + ' // No file submitted')
                        print("no selected file")
                        flash('No selected file')
                        return redirect(request.url)
                if file and allowed_file(file.filename):
                        print("accepted image")
                        filename = session.get('uname')+secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        print("Upload original Successful")
                        squarefilename = "new"+filename
                        squarify(filename).save(os.path.join(app.config['UPLOAD_FOLDER'],squarefilename))
                        posts.insert_one({
                                                                "uname": session.get('uname'),
                                                                "squareimg": squarefilename
                                                                })
                        print("Upload resize Successful")
                        app.logger.info(session.get('uname') + ' // Resize Successful')
                        return redirect(url_for('loadResult',filename="new"+filename))
        print("GET Request")
        return redirect(url_for('upload'))

@app.route("/history")
def history():
                checkUname = session.get('uname')
                firstList = list(posts.find({'uname': checkUname},{"_id": 0, "squareimg": 1}))
                print("getting history")
                myList = []
                for item in firstList:
                                myList.append(item.get('squareimg'))
                app.logger.info(session.get('uname') + ' // history retrieved')        
                return render_template("history.html", myList=myList)
                                

@app.route("/")
def index():
        return render_template("login.html")

@app.route("/upload")
def upload():
        if session.get('uname') == None:
                print("not logged in, redirecting")
                app.logger.error(session.get('uname') + ' // User not logged in')
                return redirect(url_for('index'))
        return render_template("upload.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
        if request.method == "POST":
                salt = str(random.randint(1, 1000))
                checkUname = str(request.form['uname'])
                formatPass = str(request.form['pword'])
                fullStr = checkUname + formatPass + salt
                newhash = hashlib.sha256(fullStr.encode("utf8")).hexdigest()
                if(users.find_one({"uname": checkUname}) == None):
                        tmp = {
                                "uname": request.form['uname'],
                                "hash": newhash,
                                "salt": salt
                        }
                        users.insert_one(tmp)
                        app.logger.info(session.get('uname') + ' // User registered. Username: ' + checkUname)
                        return "Successfully register, please go back to login"
                app.logger.info(session.get('uname') + ' // Username: ' + checkUname + ' is already taken.')
                return "Username already taken, please go back and try again"
        return redirect(url_for('index'))

@app.route("/login", methods=['GET', 'POST'])
def login():
        checkUname = str(request.form['uname'])
        formatPass = str(request.form['pword'])
        toCheck = users.find_one({"uname": checkUname})
        if request.method == "POST":
                if(toCheck == None):
                        app.logger.error(session.get('uname') + ' // User does not exist')
                        return "Sorry, login has failed. Please check your credentials."
                fullStr = checkUname + formatPass + toCheck["salt"]
                newhash = hashlib.sha256(fullStr.encode("utf8")).hexdigest()
                if(newhash == toCheck["hash"]):
                        session['uname'] = checkUname;
                        app.logger.info(session.get('uname') + ' // ' + checkUname + ' has logged in.')
                        return redirect(url_for('upload'))
                app.logger.error(session.get('uname') + ' // Invalid Password.')
                return "Sorry, login has failed. Please check your credentials."
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
        if session.get('uname') != True:
                print("logged out")
                session.pop('uname', None)
                app.logger.info(session.get('uname') + ' // Logged out.')
        return redirect(url_for('index'))

@app.after_request
def apply_caching(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

if __name__ == '__main__':

        logger = logging.getLogger('werkzeug')
        handler = logging.FileHandler('access.log')
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        handler.setFormatter(formatter) 
        logger.addHandler(handler)
        app.logger.addHandler(handler)

        
        app.run(debug=True)
