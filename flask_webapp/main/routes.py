from flask import render_template, Blueprint
from flask_webapp.dashapp import dash_app
from flask import send_from_directory
from flask import Flask
from flask_sitemap import Sitemap
main = Blueprint('main', __name__)
app=Flask(__name__)
ext = Sitemap(app=app)

# dummy data
posts = []

@main.route('/about')
def home():
	# the content of the route is in a render_template html file which we create
	return render_template('home.html', posts=posts)

@main.route('/about')
def about():
	return render_template('about.html')

@main.route('/Terms_and_Conditions')
def downloadFile ():
	path=app.template_folder
	return send_from_directory(path, filename='Terms, conditions and privacy.pdf')

@main.route('/')
@main.route('/regional')
def regional():
	return render_template('regional.html', dash_url=dash_app.regional_url_base, title='Regional NEM')

@main.route('/widget')
def widget():
	return render_template('widget',dash_url='/widget/')

@main.route('/renewables')
def renewables():
	return render_template('renewables.html', renew_dash_url='/renewables/',title='Renewable Summary')

@main.route('/generator')
def generators():
	return render_template('generators.html', g_dash_url='generators', title='NEM Generators')

@main.route('/interconnectors')
def interconnectors():
	return render_template('interconnectors.html', inter_dash_url='/interconnectors/',title='Interconnectors')

@main.route('/google3eea4a26e057dadc.html')
def temp():
	return render_template('google3eea4a26e057dadc.html')

@main.route("/robots.txt")
def robots_txt():
	return send_from_directory(app.template_folder,"robots.txt")

@main.route("/sitemap.xml")
def sitemap():
	return send_from_directory(app.template_folder,"sitemap.xml")