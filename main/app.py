from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
db = SQLAlchemy(app)

@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == '__main__':
    #with app.app_context():
        #db.drop_all()
        #db.create_all()
    app.run(debug=True, host='0.0.0.0', port=4000)