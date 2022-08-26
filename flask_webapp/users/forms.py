from flask_wtf import FlaskForm, RecaptchaField
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_webapp.models import User
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, validators
from wtforms.validators import DataRequired, ValidationError

class RegistrationForm(FlaskForm):
    # adding some requirements for the usernames
    # using validators
    # DataRequired means they cant input empty username field
    recaptcha = RecaptchaField()

    firstname = StringField('First Name',
                            validators=[DataRequired(), Length(min=2, max=20)]
                            )
    lastname = StringField('Last Name',
                           validators=[DataRequired(), Length(min=2, max=20)]
                           )
    affiliation = StringField('Affiliation',
                              validators=[DataRequired(), Length(min=2, max=20)]
                              )
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])

    confirm_pass = PasswordField('Confirm Password',
                                 validators=[DataRequired(), EqualTo('password')])

    accept_tos = BooleanField('I accept the terms and conditions:',
                              [validators.Required()])

    subscribe = BooleanField('Subscribe to the VEPC newsletter:')

    submit = SubmitField('Sign Up')

    # creating a custom validations for duplicate user registrations (e.g. user/email exists)
    def validate_username(self, username):
        if username.data != current_user.username:
            # grab username entered in our registration form
            user = User.query.filter_by(username=username.data).first()

            # if user exists, send a validation error
            if user:
                raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, email):
        # grab email entered in our registration form
        user = User.query.filter_by(email=email.data).first()

        # if email exists, send a validation error
        if user:
            raise ValidationError('Email already exists. Please choose a different email.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EmailList(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    first_name = StringField('Full name',
                        validators=[DataRequired(), Length(min=2, max=30)])
    remember = BooleanField('Remember Me')
    recaptcha = RecaptchaField()

    submit = SubmitField('Submit')

# allow user to update their credentials
class UpdateAccountForm(FlaskForm):
    firstname = StringField('First Name',
                            validators=[DataRequired(), Length(min=2, max=20)]
                            )
    lastname = StringField('Last Name',
                           validators=[DataRequired(), Length(min=2, max=20)]
                           )
    affiliation = StringField('Affiliation',
                              validators=[DataRequired(), Length(min=2, max=20)]
                              )

    email = StringField('Email',
                        validators=[DataRequired(), Email()])

    submit = SubmitField('Update')

    # these checks will be different than the above
    # bc the user should still be able to enter their existing username
    # e.g. keeping their details as-is
    def validate_username(self, username):
        if username.data != current_user.username:
            # grab username entered in our registration form
            user = User.query.filter_by(username=username.data).first()

            # if user exists, send a validation error
            if user:
                raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, email):
        if email.data != current_user.email:
            # grab email entered in our registration form
            user = User.query.filter_by(email=email.data).first()

            # if email exists, send a validation error
            if user:
                raise ValidationError('Email already exists. Please choose a different email.')

class ContactForm(FlaskForm):
    subject = StringField('Subject',validators=[DataRequired(), Length(min=2, max=50)])
    message = TextAreaField("Message",validators=[DataRequired(), Length(min=10, max=2000)])
    recaptcha = RecaptchaField()
    submit = SubmitField("Send")