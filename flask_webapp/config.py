import os

class Config:
	# adding secret key for security
	# grabbed from "secrets" python module
	SECRET_KEY = os.environ.get('SECRET_KEY')
	SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.sqlite')  # 'sqlite:///site.db'
	
	with open("flask_webapp/templates/sitemap_template.xml", 'r') as file:
		filedata = file.read()
	from datetime import datetime,timedelta

	date = datetime.now() - timedelta(hours=0) # current date and time
	date = date.isoformat()
	sitemap=filedata.replace('######',date)

	# Write the file out again
	with open("flask_webapp/templates/sitemap.xml", 'w') as file:
		file.write(sitemap)
	
	SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI

	# To silence SQL warning
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# RECAPTCHA:
	RECAPTCHA_ENABLED = True
	RECAPTCHA_PUBLIC_KEY = '6Lf-d8gZAAAAAA-FLGCKgqvkx-BuAW0PiQ9nZg3t'
	RECAPTCHA_PRIVATE_KEY = '6Lf-d8gZAAAAAG6xMK-ccQC_Cy0t7apGeWAZe4LX'
	RECAPTCHA_THEME = "light"
	RECAPTCHA_TYPE = "image"
	RECAPTCHA_SIZE = "normal"
	RECAPTCHA_RTABINDEX = 10
	SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
	SITEMAP_BLUEPRINT='main'