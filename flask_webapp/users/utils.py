import os
import secrets
from PIL import Image
from flask import url_for, current_app

def save_picture(form_picture):
	pic_hex = secrets.token_hex(8)
	# get the file extension of the uploaded profile pic
	_, f_ext = os.path.splitext(form_picture.filename)
	# creating the filename of pic
	pic_fn = pic_hex + f_ext
	# put pic in profile pics root
	pic_path = os.path.join(current_app.root_path, 'static/profile_pics', pic_fn)
	# resizing picture to avoid it taking up too much space
	output_size = (125, 125)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(pic_path)
	form_picture.save(pic_path)
	
	return pic_fn