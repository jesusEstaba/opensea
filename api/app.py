from flask import Flask, render_template, redirect, session, request, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import random
import os
from twilio.rest import Client

from dotenv import dotenv_values
env = dotenv_values(".env")
print(env)

app = Flask(__name__, static_url_path='', static_folder='public')
app.secret_key = env['FLASK_SECRET_KEY']
client = MongoClient(env['MONGO_DB_URI'])
db = client.opensea


@app.route("/")
def home_view():
    return render_template("home.html")


@app.route("/signin")
def signin_view():
    mensaje = request.args.get('mensaje')
    return render_template("signin.html", mensaje=mensaje)


@app.route("/signin/new_user")
def signin_user():
    newEmail = request.args.get('email')
    newPassword = request.args.get('password')
    new_user_name = request.args.get('user')

    if newEmail == "":
        return redirect('/signin?mensaje=Ingresa el Email')

    if newPassword == "":
        return redirect('/signin?mensaje=Ingresa una Contraseña')

    if len(newPassword) < 8:
        return redirect('/signin?mensaje=La contraseña debe contener 8 o más carácteres')

    if new_user_name == "":
        return redirect('/signin?mensaje=Ingresa un nombre de usuario')

    emailSplitted = newEmail.split('@')

    if len(emailSplitted) != 2 or emailSplitted[1] != 'gmail.com' != 'hotmail.com':

        return redirect('/signin?mensaje=la dirección de correo no es válida, debe contener @gmail.com ó @hotmail.com')

    newUser = {
        'email': newEmail,
        'password': newPassword,
        'user': new_user_name,
        'NFTS': 0,
        'user_created_at': datetime.now()
    }
    user = db.users.insert_one(newUser).inserted_id
    session.pop('user_id', None)

    return redirect('/finished/' + str(user))


@app.route("/finished/<id>")
def registration_finished_view(id):
    user = db.users.find_one({'_id': ObjectId(id)})
    return render_template("finished.html", user=user)


@app.route("/login")
def login_view():
    mensaje = request.args.get('mensaje')
    return render_template("login.html", mensaje=mensaje)


@app.route("/login/users")
def login_users():
    userEmail = request.args.get('email')
    userName = request.args.get('userName')
    userPassword = request.args.get('password')

    if userEmail == "" or userName == "":
        return redirect('/login?mensaje=Ingresa el mail o nombre de usuario')

    if userPassword == "":
        return redirect('/login?mensaje=Ingresa la contraseña')

    userDocument = db.users.find_one(
        {'$or': [{'email': userEmail}, {'user': userEmail}]})

    if not userDocument:
        return redirect('/login?mensaje=El usuario no existe')

    if userDocument['password'] != userPassword or userDocument['email'] != userEmail or userDocument['user'] != userName:
        return redirect('/login?mensaje=La contraseña o el usuario es inválido')

    session['user_id'] = str(userDocument['_id'])

    return redirect('/profile')


@app.route("/profile")
def profile_view():

    if not session.get('user_id'):
        return redirect('/')

    userId = session.get('user_id')

    user = db.users.find_one({'_id': ObjectId(userId)})
    if not user:
        return abort(404)

    userImages = db.profile_images.find_one({'user_id': userId})
   # if not userImages:
    #    return abort(404)
    return render_template("profile.html", user=user, userImages=userImages)


@app.route("/upload/image")
def upload_img():
    if not session.get('user_id'):
        return redirect('/')

    imageUrl = request.args.get('image')
    userId = session.get('user_id')
    user_name = db.users.find_one({'_id': ObjectId(userId)})

# En esta condición decimos "si el mensaje de texto no esta vacío o el mensaje
# reservado del anunciante existe crea el mensaje".

    if imageUrl != "":

        imageUploaded = {}
        imageUploaded['image_url'] = imageUrl
        imageUploaded['user_id'] = userId
        imageUploaded['user'] = user_name

    else:
        return abort(404)

    db.profile_images.insert_one(imageUploaded)
    return redirect('/profile')
