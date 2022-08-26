from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_webapp.config import Config
from flask_mail import Mail
from flask_analytics import Analytics
import os
from flask_webapp.dashapp.VEPC_data_app import get_dash_tab

# This file initialises our app.

# Creating a DB instance
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

mail= Mail()

# def setup_mail_server(app):

# 	app.config["MAIL_SERVER"] = "smtp.gmail.com"
# 	app.config["MAIL_PORT"] = 465
# 	app.config["MAIL_USE_SSL"] = True

# 	app.config["MAIL_USERNAME"] = os.environ.get('G_Mail_login')
# 	app.config["MAIL_PASSWORD"] = os.environ.get('G_Mail')
# 	mail.init_app(app)

def create_app(config_class=Config):
	# Set an instance of the flask app passing in "__name__"
	app = Flask(__name__)
	
	SECRET_KEY = os.urandom(32)

	app.config.from_object(Config)
	app.config['SECRET_KEY'] = SECRET_KEY
	db.init_app(app)
	Analytics(app)
	bcrypt.init_app(app)
	login_manager.init_app(app)
	# setup_mail_server(app)
	
	# These imports need to be here for some reason
	from flask_webapp.users.routes import users
	from flask_webapp.main.routes import main
	app.register_blueprint(users)
	app.register_blueprint(main)
	app.config['ANALYTICS']['GOOGLE_CLASSIC_ANALYTICS']['ACCOUNT'] = 'UA-178389437-1'

	@app.before_first_request
	def create_tables():
		db.create_all()

	app = get_dash_tab(app, tab='Renewable Summary', url='/renewables/')
	app = get_dash_tab(app, tab='Regional NEM', url='/regional/')
	app = get_dash_tab(app, tab='NEM Generators', url='/generators/')
	app = get_dash_tab(app, tab='interconnector', url='/interconnectors/')
	#app = get_dash_tab(app, tab='widget', url='/widget/')

	return app