from datetime import datetime
from flask_webapp import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_webapp import bcrypt


# Specifying a decorator
@login_manager.user_loader
def load_user(user_id):
	# Using the primary key; user_id   
    return User.query.get(int(user_id))

# The following classes creates users and posts and stores them in DBs.
# Can be used in other files by importing: from flask_webapp.models import User, Post
class User(db.Model,UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	firstname= db.Column(db.String(20), nullable=True)
	lastname = db.Column(db.String(20), nullable=True)
	affiliation = db.Column(db.String(20), unique=False, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
	password = db.Column(db.String(60), nullable=False)
	accept_tos = db.Column(db.String(20), nullable=False)
	
	# our post attribute has a relationship to the post model
	# lazy menas when sql alchemy loads the data from the database
	# true means sql alchemy loads the data as necessary in one go
	posts = db.relationship('Post', backref='author', lazy=True)

	def __repr__(self):
		return f"User('{self.username}','{self.email}','{self.image_file}')"

	def verify_password(self, pwd):
		return check_password_hash(self.password, pwd)

	def is_correct_password(self, plaintext):
		if bcrypt.check_password_hash(self.password, plaintext):
			return True
		return False

	def __init__(self, username, password, firstname,lastname, accept_tos, affiliation, email,image_file):
		self.username = username
		self.password = password
		self.firstname = firstname
		self.lastname = lastname
		self.affiliation = affiliation
		self.accept_tos = accept_tos
		self.image_file = image_file
		self.email = email

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	content = db.Column(db.Text, nullable=False)
	# referncing the table name
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f"Post('{self.title}','{self.date_posted}')"

def init_db():
	db.drop_all()
	db.create_all()
	test_memory = User(id=1)
	db.session.add(test_memory)
	db.session.commit()

if __name__ == '__main__':
    a=1
	# init_db()
