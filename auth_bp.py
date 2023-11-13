from flask import *
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, current_user 
from flask_babel import Babel, _
import sqlite3
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFS
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

auth_bp = Blueprint('auth', __name__)
babel = Babel()

 

LANGUAGES = ['en', 'fr', 'es']

@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(auth_bp)





load_dotenv()
import os




MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB = os.environ.get("MONGODB_DB")
MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION")
SQLITE_URI = os.environ.get('SQLITE_URI', 'ratatouille.db')
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')














# conn to MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
recette_col = db['recette']
fs = GridFS(db)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

conn = sqlite3.connect(SQLITE_URI)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  email TEXT NOT NULL,
                  password TEXT NOT NULL)''')

conn.commit()
conn.close()



login_manager = LoginManager()
login_manager.login_view = 'suth_bp.login'
login_manager.init_app(auth_bp)



class User(UserMixin):
    def __init__(self, id,  username, email, password):
         self.id = id
         self.username = username
         self.email = email
         self.password = password       
         
    def is_active(self):
         return self.authenticated
    def is_anonymous(self):
         return False
    def is_authenticated(self):
         return self.authenticated

    def get_id(self):
         return str(self.email)


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(SQLITE_URI)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        return user

    return None



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('username alr taken')


    def validate_email(self, field):
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (field.data,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            raise ValidationError('email alr taken')
        










@auth_bp.route('/', methods=['GET'])
def display_welcome():
    return render_template('welcome.html', get_locale=get_locale)





@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
   
        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
        else:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
            conn.commit()
            conn.close()

            user_doc = {
                '_id': email,
                'username': username   
            }
            db.users.insert_one(user_doc)



            flash("Successfully registered. You can now log in.")
            return redirect(url_for('login'))

    return render_template('register.html', form=form, get_locale=get_locale)




@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.is_submitted():
        print('form validated')
        username = form.username.data
        password = form.password.data

        conn = sqlite3.connect(SQLITE_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])
            login_user(user)
            current_user.email = user_data[2] 
            flash("Successfully logged in")
            print("Login email:", current_user.email)

            return redirect(url_for('recette_bp.home'))
    
        else:
            flash(_('Login Failed. Invalid Credentials'))

    return render_template('login.html', form=form, get_locale=get_locale)





@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.display_welcome'))