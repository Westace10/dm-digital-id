import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, send_file, send_from_directory, session, abort
from flask_sqlalchemy import SQLAlchemy
import pyqrcode
import sqlite3
import base64
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
import png

app=Flask(__name__)

UPLOAD_FOLDER = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/'
UPLOAD_FOLDER_QR = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/qrimg/'
UPLOAD_FOLDER_QRV = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/qrimgv/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_QRV'] = UPLOAD_FOLDER_QRV 

@app.route('/')
def home():
    return render_template("index.html", title='Home')

def full_format(num, d=3):
    digit = num % (10**d-1) + 1
    return "{:0{}d}".format(digit, d)

@app.route("/confirmation/", methods=["GET", "POST"])
def upload_image():
    if request.method == 'POST':
        if request.files:
            image = request.files["image"]
            sign = request.files["sign"]
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            sign.save(os.path.join(app.config['UPLOAD_FOLDER'], sign.filename))
            imagepathfull = UPLOAD_FOLDER + image.filename
            signpathfull = UPLOAD_FOLDER + sign.filename
            imagepathspec = imagepathfull[61:]
            signpathspec = signpathfull[61:]
            initial_f = request.form['fname']
            initial_l = request.form['lname']
            fullname = initial_f + ' ' + initial_l
            date = request.form['doe']
            phone = request.form['phone']
            email = request.form['email']
            position = request.form['position']
            # staffid = initial_f[0]+initial_l[0]+date
            picFile = open(f'{imagepathfull}', 'rb')
            signFile = open(f'{signpathfull}', 'rb')
            pix = picFile.read()
            signPix = signFile.read()
            pixData = sqlite3.Binary(pix)
            signPixData = sqlite3.Binary(signPix)
            con = sqlite3.connect('test.db')
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS customer (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                fullName TEXT,
                firstName TEXT,
                lastName TEXT,
                staffId CHAR,
                position TEXT,
                dateOfEmployment INTEGER,
                phone INTEGER,
                email CHAR,
                profilePic BLOB,
                signPic BLOB,
                qrPic BLOB)""")
            cur.execute("""INSERT INTO customer (
                fullName,
                firstName,
                lastName,
                position,
                phone,
                email,
                dateOfEmployment,
                profilePic,
                signPic)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (f'{fullname}', f'{initial_f}', f'{initial_l}',
                f'{position}', f'{phone}', f'{email}', f'{date}',
                pixData, signPixData,))
            con.commit()
            cur.execute("SELECT id FROM customer")
            rows = cur.fetchall()
            myindex = rows[-1]
            for i in myindex:
                inDex = i
            qrpathfull = UPLOAD_FOLDER_QR + 'myqr' + f'{inDex}' + '.png'
            qr = pyqrcode.create(fullname)
            qr.png(f'{qrpathfull}', scale=8)
            qrFile = open(f'{qrpathfull}', 'rb')
            qrPathSpec = qrpathfull[61:]
            qrPix = qrFile.read()
            qrData = sqlite3.Binary(qrPix)
            serial = inDex - 1
            serialnum = full_format(serial)
            serialNumb = initial_f[0]+initial_l[0]+date+serialnum
            cur.execute("UPDATE customer SET qrPic =?, staffId=? WHERE id =?", (qrData, serialNumb, inDex,))
            con.commit()
    
    return render_template('confirmation.html', title='Confirmation' , fname=initial_f, lname=initial_l, phone=phone, email=email, position=position, qrpath=qrPathSpec, imagepath=imagepathspec, signpath=signpathspec, staffid=serialNumb)

@app.route('/registration/', methods=['GET', 'POST'])
def registration():
    return render_template("registration.html", title='Registration')

@app.route('/verification-reg/', methods=['GET', 'POST'])
def verificationReg():
    return render_template("verification-reg.html", title='Upload Verification')

@app.route('/upload-for-verification/', methods=['GET', 'POST'])
def verificationUpload():
    if request.method == 'POST':
        if request.files:
            qrimage = request.files["qrimage"]
            qrimage.save(os.path.join(app.config['UPLOAD_FOLDER_QRV'], qrimage.filename))
            qrimagepathfull = UPLOAD_FOLDER_QRV + qrimage.filename
            qrimagepathspec = qrimagepathfull[61:]
            img = cv2.imread(f'{qrimagepathfull}')
            decoded = pyzbar.decode(img)
            for i in decoded:
                qrdataver = i[0]
                mybyte = qrdataver.decode('utf-8')
                print(mybyte)
                con = sqlite3.connect('test.db')
                cur = con.cursor()
                cur.execute("SELECT id, firstName, lastName, staffId, phone, email, position, dateOfEmployment, profilePic, signPic FROM customer WHERE fullName=?", (f'{mybyte}',))
                info = cur.fetchall()
                if info:
                    for i in info:
                        vid = i[0]
                        vfname = i[1]
                        vlname = i[2]
                        vstaffid = i[3]
                        vphone = i[4]
                        vemail = i[5]
                        vposition = i[6]
                        vdate = i[7]
                        print(vid, vfname, vlname, vstaffid)
                        vprofilepic = i[8]
                        vsignpic = i[9]
                        myvpathprof = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/verifiedimg/' + str(vid) + '.jpg'
                        myvpathprofspec = myvpathprof[61:]
                        with open(myvpathprof, 'wb') as file:
                            verifprof = file.write(vprofilepic)
                        myvpathsign = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/verifiedimg/' + str(vid) + '.png'
                        myvpathsignspec = myvpathsign[61:]
                        with open(myvpathsign, 'wb') as file:
                            verifsign = file.write(vsignpic)
                    return render_template("verification-conf.html", title='Upload Verification', verifiedDate=vdate, verifiedPhone=vphone, verifiedEmail=vemail, verifiedPosition=vposition, verifiedId=vid, verifiedFname=vfname, verifiedLname=vlname, verifiedStaffid=vstaffid, verifiedProfpic=myvpathprofspec, verifiedSignpic=myvpathsignspec)
                else:
                    errmsg = "Staff details not found, kindly report to HR!"
                    print(errmsg)
                    return render_template("not-found.html")

                    
@app.route('/upload-for-verification/', methods=['GET', 'POST'])
def verificationConf():
    return render_template("verification-conf.html")

@app.route('/upload-for-verification-scan/', methods=['GET', 'POST'])
def scanQR():
    cap = cv2.VideoCapture(0)
    while cap:
        _, frame = cap.read()
        decodedObjects = pyzbar.decode(frame)
        for i in decodedObjects:
            mydata = i.data
            myvalue = mydata.decode('utf-8')
            print (myvalue)
        if decodedObjects:
            print('I scaled', myvalue)
            break
        else:
            continue
    con = sqlite3.connect('test.db')
    cur = con.cursor()
    cur.execute("SELECT id, firstName, lastName, staffId, phone, email, position, dateOfEmployment, profilePic, signPic FROM customer WHERE fullName=?", (f'{myvalue}',))
    info = cur.fetchall()
    if info:
        for i in info:
            vid = i[0]
            vfname = i[1]
            vlname = i[2]
            vstaffid = i[3]
            vphone = i[4]
            vemail = i[5]
            vposition = i[6]
            vdate = i[7]
            print(vid, vfname, vlname, vstaffid, vphone, vemail, vposition, vdate)
            vprofilepic = i[8]
            vsignpic = i[9]
            myvpathprof = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/verifiedimg/' + str(vid) + '.jpg'
            myvpathprofspec = myvpathprof[61:]
            with open(myvpathprof, 'wb') as file:
                verifprof = file.write(vprofilepic)
            myvpathsign = '/Users/akeemashaolu/CodeDocuments/myWeb/Pearl-Codes/dm-web-id/static/img/verifiedimg/' + str(vid) + '.png'
            myvpathsignspec = myvpathsign[61:]
            with open(myvpathsign, 'wb') as file:
                verifsign = file.write(vsignpic)
        # return render_template("verification-conf.html", title='Upload Verification', verifiedId=vid, verifiedFname=vfname, verifiedLname=vlname, verifiedStaffid=vstaffid, verifiedProfpic=myvpathprofspec, verifiedSignpic=myvpathsignspec)
        return render_template("verification-conf.html", title='Upload Verification', verifiedDate=vdate, verifiedPhone=vphone, verifiedEmail=vemail, verifiedPosition=vposition, verifiedId=vid, verifiedFname=vfname, verifiedLname=vlname, verifiedStaffid=vstaffid, verifiedProfpic=myvpathprofspec, verifiedSignpic=myvpathsignspec)
    else:
        errmsg = "Staff details not found, kindly report to HR!"
        print(errmsg)
        return render_template("not-found.html")

@app.route('/renew/')
def renew():
    return render_template("renew.html", title='Renewal')

@app.route('/confirmation/', methods=['GET', 'POST'])
def confirmation():
    return render_template("confirmation.html")

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html")

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html")

if __name__=="__main__":
    app.run(debug=True)