from flask import Flask, request
from flask_login import LoginManager
from dotenv import load_dotenv
from auth_bp import auth_bp
from recette_bp import recette_bp
from flask_mail import Mail
from flask_babel import Babel
from auth_bp import load_user 

app = Flask(__name__)

app.secret_key = "your_secret_key_here"


login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'
login_manager.init_app(app)
login_manager.user_loader(load_user)

LANGUAGES = ['en', 'fr', 'es']

babel = Babel(app)
mail = Mail(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(recette_bp)

@babel.localeselector
def get_locale():
    user_language = request.args.get('lang', 'en')

    if user_language not in LANGUAGES:
        user_language = 'en'
    return user_language

if __name__ == '__main__':
    app.run(debug=True)
