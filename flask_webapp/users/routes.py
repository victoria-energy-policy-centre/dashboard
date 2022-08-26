from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_webapp import db, bcrypt
from flask_webapp.users.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_webapp.models import User
from flask_login import login_user, current_user, logout_user, login_required
from flask_webapp.users.forms import (ContactForm,RegistrationForm, LoginForm, UpdateAccountForm, EmailList)
from werkzeug.security import generate_password_hash
from flask_webapp.dashapp import dash_app
from flask import Flask, render_template, request, flash
from flask_mail import Message

users = Blueprint('users', __name__)

from flask_webapp.__init__ import mail
from flask_recaptcha import ReCaptcha

app=Flask(__name__)
recaptcha = ReCaptcha(app=app)

@users.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.about'))
	form = RegistrationForm()

	if request.method == "POST":
		if form.validate_on_submit():
			hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
			user = User(username=form.email.data ,email=form.email.data,  password=hashed_pw,affiliation=form.affiliation.data, firstname=form.firstname.data, lastname=form.lastname.data,accept_tos=form.accept_tos.data,image_file=None)

			# add the created user to the db
			db.session.add(user)
			db.session.commit()
			if form.subscribe.data==True:
				body='You have a new subscription from '+form.firstname.data+' '+form.lastname.data+' from '+form.affiliation.data+ '. Email is: '+ form.email.data
				msg = Message('New mailing list subscription through VEPC Data', sender='VEPC Data', recipients=['vepcentre@gmail.com'],
								body=body)
				mail.send(msg)
			flash('Account created successfully.', 'success')
			return redirect(url_for('users.login'))
		else:
			flash('Registration failed.', 'danger')
	return render_template('register.html', title='Register', form = form)


@users.route('/about', methods=['GET', 'POST'])
def email_signup():
	form = EmailList()
	if form.validate_on_submit():
		if recaptcha.verify():
			body = 'You have a new subscription from ' + form.first_name.data + '. Email is: ' + form.email.data
			msg = Message('New mailing list subscription through VEPC Data', sender='VEPC Data',
							recipients=['vepcentre@gmail.com'],
							body=body)
			mail.send(msg)
			flash('Thank you for subscribing.', 'info')
		else:
			flash('Please confirm humanity.', 'danger')
	return render_template('home.html',
		title='', form = form)

@users.route('/regional', methods=['GET', 'POST'])
@users.route('/', methods=['GET', 'POST'])
def email_signup_regional():
	form = EmailList()
	if form.validate_on_submit():
		if recaptcha.verify():
			body = 'You have a new subscription from ' + form.first_name.data + '. Email is: ' + form.email.data
			msg = Message('New mailing list subscription through VEPC Data', sender='VEPC Data',
							recipients=['vepcentre@gmail.com'],
							body=body)
			mail.send(msg)
			flash('Thank you for subscribing.', 'info')

		else:
			flash('Please confirm humanity.', 'danger')

	return render_template('regional.html',form = form, dash_url=dash_app.regional_url_base, title='Regional NEM')

@users.route('/generator', methods=['GET', 'POST'])
def email_signup_generators():
	form = EmailList()
	if form.validate_on_submit():
		if recaptcha.verify():
			body = 'You have a new subscription from ' + form.first_name.data + '. Email is: ' + form.email.data
			msg = Message('New mailing list subscription through VEPC Data', sender='VEPC Data',
							recipients=['vepcentre@gmail.com'],
							body=body)
			mail.send(msg)
			flash('Thank you for subscribing.', 'info')
		else:
			flash('Please confirm humanity.', 'danger')

	return render_template('generators.html',
		 form = form, g_dash_url='generators', title='NEM Generators')

@users.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.about'))
	form = LoginForm()
	if form.validate_on_submit():  
		# check what username (email) was entered during the singin
		user = User.query.filter_by(email=form.email.data).first()

		# if it exists
		if user and user.is_correct_password(form.password.data):
			# use the login_user function and enter the user from above
			login_user(user, remember=form.remember.data)
			# redirecting the user to the page they were trying to access after signing in
			next_page = request.args.get('next')

			# if successful, redirect to home
			return redirect(next_page) if next_page else redirect(url_for('main.regional'))
		else:
			flash('Sign in failed. Please check details again.','danger')

	return render_template('login.html', 
		title='Sign In', form = form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.about'))

@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		# profile picture upload

		#current_user.username = form.username.data
		current_user.firstname = form.firstname.data
		current_user.lastname = form.lastname.data
		current_user.affiliation = form.affiliation.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Account updated.', 'success')
		return redirect(url_for('users.account'))
	elif request.method == 'GET':
		form.affiliation.data = current_user.affiliation
		form.lastname.data = current_user.lastname
		form.firstname.data = current_user.firstname
		form.email.data = current_user.email

	image_file = url_for('static',
		filename='profile_pics/'+current_user.image_file)
	return render_template('account.html', title='Account',
		image_file = image_file, form=form)

## Contact form
@users.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
	form = ContactForm()

	if request.method == 'POST':
		print(form.message.data)
		print(form.subject.data)
		if form.validate_on_submit():
			if recaptcha.verify():
				body='[From: %s %s, %s (%s)]\n %s' % (current_user.firstname, current_user.lastname, current_user.affiliation, current_user.email, form.message.data)
				print(body)
				msg = Message(form.subject.data, sender=current_user.email, recipients=['vepc.app@gmail.com'],body=body)

				mail.send(msg)
				flash('Message sucessfully send! Thank you.', 'success')
				return render_template('contact.html', success=True,form=form)
			else:
				flash('Contact failed.', 'danger')

		else:
			flash('All fields are required.', 'danger')
			return render_template('contact.html', form=form)

	elif request.method == 'GET':
		return render_template('contact.html', form=form)






