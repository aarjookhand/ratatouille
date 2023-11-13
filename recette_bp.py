from flask import *
import sqlite3
from pymongo import MongoClient
from gridfs import GridFS
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required

from flask_login import current_user
from flask import flash, redirect, url_for, jsonify
from dotenv import load_dotenv
from flask_babel import Babel, _

import base64
from flask_mail import Message, Mail
from elasticsearch import Elasticsearch


load_dotenv()
import os


recette_bp = Blueprint('recette_bp', __name__)
babel = Babel()
mail = Mail()
 

LANGUAGES = ['en', 'fr', 'es']

@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language



recette_bp.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")


MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB = os.environ.get("MONGODB_DB")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION")

MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')



# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

# Elasticsearch Configuration
es = Elasticsearch([{
    'host': os.environ.get('ELASTICSEARCH_HOST', 'localhost'),
    'port': int(os.environ.get('ELASTICSEARCH_PORT', 9200)),
    'scheme': os.environ.get('ELASTICSEARCH_SCHEME', 'http')
}])




@recette_bp.route('/home')
def home():
    recette = collection.find({})
    return render_template('home.html', recette=recette, get_locale=get_locale)



@recette_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        recipe_name = request.form['recipeName']
        cuisine = request.form['cuisine']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image = request.files['image'].read()
        encoded_image = base64.b64encode(image).decode('utf-8')

        recipe_data = {
            'user_id': current_user.get_id(),
            'recipe_name': recipe_name,
            'cuisine': cuisine,
            'ingredients': ingredients,
            'instructions': instructions,
            "image": encoded_image

        }

        collection.insert_one(recipe_data)

        try:

            send_upload_confirmation_email(current_user.get_id(), recipe_name)

            flash('Recipe uploaded successfully')

        except Exception as e:
            flash(_('Error sending confirmation email: {error}').format(error=str(e)))
        return redirect(url_for('recette_bp.home'))

    return render_template('upload.html', get_locale=get_locale)


def send_upload_confirmation_email(recipient, recipe_name):
    subject = _('Recipe Upload Confirmation')
    body = _('Thank you for uploading the recipe for {recipe_name}!').format(recipe_name=recipe_name)
    sender = 'aarjookhand@gmail.com' 
    message = Message(subject, recipients=[recipient], body=body, sender=sender)
    mail.send(message)


