from flask_webapp import create_app

app = create_app(__name__)

if __name__ == "__main__":
    app.run(port=8081, debug=False, host='0.0.0.0')