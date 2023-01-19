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
    session.pop('user_id', None)
    users = list(db.users.find())
    userProfilesImages = list(db.profile_images.find(
        {'user': ObjectId(users)}))
   # for x in users:
    #    x = len(users)

    return render_template("home.html", userProfilesImages=userProfilesImages, users=users)


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

    if len(new_user_name) < 5:
        return redirect('/signin?mensaje=El nombre de usuario no debe contener menos de 5 carácteres')

    if len(new_user_name) > 23:
        return redirect('/signin?mensaje=El nombre de usuario no debe contener  más de 23 carácteres')

    emailSplitted = newEmail.split('@')

    if len(emailSplitted) != 2 or emailSplitted[1] != 'gmail.com' != 'hotmail.com':

        return redirect('/signin?mensaje=la dirección de correo no es válida, debe contener @gmail.com ó @hotmail.com')

    newUser = {
        'email': newEmail,
        'password': newPassword,
        'user': new_user_name,
        'nfts': 0,
        'user_created_at': datetime.now()
    }
    userId = db.users.insert_one(newUser).inserted_id

    newWallet = {
        'name': "Mafiance Coin",
        'currency': "MFC",
        'balance': float(0),
        'user_id': userId,
    }
    db.wallets.insert_one(newWallet)

    session.pop('user_id', None)

    return redirect('/finished/' + str(userId))


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

    return redirect('/profile/' + str(userDocument['_id']))


@app.route("/profile/<id>")
def profile_view(id):

    userId = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(id)})
    userImage = db.profile_images.find_one({'user_id': str(user['_id'])})
    userWallet = db.wallets.find_one({'user_id': ObjectId(id)})
    if not userWallet:
        return abort(404)

    name = request.args.get('name')
    maxamount = request.args.get('max')
    minamount = request.args.get('min')

    if name != None:
        # i: insentive case (no importan mayusculas o minusculas)

        # DISCLAIMER PARA DANIEL DEL FUTURO:
        # este uso de busqueda regex es una forma poco optima en
        # GRAN ESCALA con MUCHOS DATOS (>100GB)
        nfts = list(db.nfts.find(
            {'owner': str(user['_id']), 'name': {'$regex': name, '$options': 'i'}}))
    elif maxamount != None and minamount != None:
        # $lt: Less than
        # $lte: Less than or equal
        # $gt: Greater than
        # $gte: Greater than or equal
        nfts = list(db.nfts.find(
            {'owner': str(user['_id']), 'nft_value': {'$gte': float(minamount), '$lte': float(maxamount)}}))
    else:
        nfts = list(db.nfts.find({'owner': str(user['_id'])}))

    return render_template("profile.html", user=user, userImage=userImage, nfts=nfts, userWallet=userWallet, userId=userId)


@app.route("/logout")
def logout():
    exit = request.args.get('logout')
    if exit:
        session.pop('user_id', None)
    return redirect('/')


@app.route("/upload/image")
def upload_img():
    if not session.get('user_id'):
        return redirect('/')

    imageUrl = request.args.get('image')
    userId = session.get('user_id')
    user_name = db.users.find_one({'_id': ObjectId(userId)})

    if imageUrl != "":

        imageUploaded = {}
        imageUploaded['image_url'] = imageUrl
        imageUploaded['user_id'] = userId
        imageUploaded['user'] = user_name

    else:
        return abort(404)

    db.profile_images.insert_one(imageUploaded)
    return redirect('/profile/' + str(userId))


@app.route("/creation")
def creation_view():
    if not session.get('user_id'):
        return redirect('/login')

    userId = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(userId)})
    nftImagePreview = db.nftsImagePreview.find_one({'user_id': userId})
    mensaje = request.args.get('mensaje')

    return render_template("creation.html", nftImagePreview=nftImagePreview, mensaje=mensaje, user=user)


@app.route("/nft/preview")
def preview():
    if not session.get('user_id'):
        return redirect('/login')

    imageUrl = request.args.get('image')
    userId = session.get('user_id')
    previewNft = {}
    previewNft['image_preview'] = imageUrl
    previewNft['user_id'] = userId
    db.nftsImagePreview.insert_one(previewNft)
    return redirect('/creation')


@app.route("/nft/creation")
def create():
    if not session.get('user_id'):
        return redirect('/login')

    imageUrl = request.args.get('image')
    nameNFT = request.args.get('name')
    externalLink = request.args.get('external_link')
    description = request.args.get('description')
    quantity = request.args.get('quantity')
    currency = request.args.get('currency')
    nftValue = request.args.get('value')
    userId = session.get('user_id')
    user_object = db.users.find_one({'_id': ObjectId(userId)})

    if quantity == None:
        quantity = int(0)
    if nftValue == None:
        nftValue = float(0)

    if imageUrl != "" or nameNFT != "" or description != "" or quantity != 0 or currency != "" or nftValue != 0:

        newNft = {}
        newNft['image_url'] = imageUrl
        newNft['name'] = nameNFT
        newNft['external_link'] = externalLink
        newNft['description'] = description
        newNft['quantity'] = int(quantity)
        newNft['currency'] = currency
        newNft['nft_value'] = float(nftValue)
        newNft['owner'] = userId
        newNft['creator'] = user_object
        newNft['creation_date'] = datetime.now()

    else:
        return redirect('/creation?mensaje=Completa los campos obligatorios')

    db.nfts.insert_one(newNft)

    db.users.update_one(
        {'_id': user_object['_id']},
        {'$set': {'nfts': user_object['nfts'] + quantity}
         }
    )

    return redirect('/profile/' + str(userId))


@app.route("/blockchains")
def coins_view():
    if not session.get('user_id'):
        return redirect('/login')

    userId = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(userId)})
    coins = list(db.blockchains.find())

    return render_template("blockchains.html", coins=coins, user=user)


@app.route("/add/blockchain")
def add_currency():
    if not session.get('user_id'):
        return redirect('/login')

    quantity = float(request.args.get('quantity'))
    userId = session.get('user_id')

    wallet = db.wallets.find_one({'user_id': ObjectId(userId)})
    if not wallet:
        return abort(404)

    newTransaction = {
        'wallet_sender_id': 0,
        'wallet_receiver_id': str(wallet['_id']),
        'quantity': quantity,
        'currency': "MFC",
        'created_at': datetime.now()
    }

    db.transactions.insert_one(newTransaction)
    if wallet:
        db.wallets.update_one(
            {'user_id': ObjectId(userId), 'currency': "MFC"},
            {
                '$set': {'balance': wallet['balance'] + newTransaction['quantity']}
            }
        )
    else:
        return abort(404)

    return redirect('/profile/' + str(userId))


@app.route("/nft/details/<id>")
def nft_details_view(id):
    if not session.get('user_id'):
        return redirect('/login')
    nft = db.nfts.find_one({'_id': ObjectId(id)})
    listNfts = list(db.nfts.find({'owner': nft['owner']}))
    return render_template("nft_details.html", nft=nft, listNfts=listNfts)


@app.route("/nft/listForSale/<id>")
def list_nft_view(id):
    if not session.get('user_id'):
        return redirect('/login')
    nft = db.nfts.find_one({'_id': ObjectId(id)})
    mensaje = request.args.get('mensaje')
    return render_template("nft_list_item.html", nft=nft, mensaje=mensaje)


@app.route("/nft/list/action/<id>")
def listed(id):
    if not session.get('user_id'):
        return redirect('/login')

    check_fixed = request.args.get('fixed')
    fixed_amount = request.args.get('fixed_amount')
    high_auction = request.args.get('high_price')
    low_auction = request.args.get('low_price')
    auction_amount = request.args.get('auction_amount')
    set_time = request.args.get('time')
    category = request.args.get('category')
    check_reserved_item = request.args.get('reserved_item')
    reserved_wallet_id = request.args.get('reserved_buyer_id')

    if fixed_amount == "":
        fixed_amount = float(0)
    if auction_amount == "":
        auction_amount = float(0)

    if fixed_amount != float(0) or auction_amount != float(0) or set_time != "Duración" or category != "Categoría del artículo":

        newNftListed = {}
        newNftListed['check_fixed'] = check_fixed
        newNftListed['fixed_amount'] = float(fixed_amount)
        newNftListed['high_auction'] = high_auction
        newNftListed['low_auction'] = low_auction
        newNftListed['auction_amount'] = float(auction_amount)
        newNftListed['set_time'] = set_time
        newNftListed['category'] = category
        newNftListed['check_reserved_item'] = check_reserved_item
        newNftListed['reserved_wallet_id'] = reserved_wallet_id
    else:
        return redirect('/nft/listForSale/' + str(id) + '?mensaje=Tienes campos vacíos')

    nft = db.nfts.find_one({'_id': ObjectId(id)})

    db.nfts.update_one(
        {'_id': ObjectId(nft['_id'])},
        {
            '$set': {'listed': newNftListed}
        }
    )

    return redirect('/nft/details/' + str(id))
