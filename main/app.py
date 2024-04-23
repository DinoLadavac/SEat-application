from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
db = SQLAlchemy(app)

class Korisnik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tip_korisnika_id = db.Column(db.Integer, db.ForeignKey('tip_korisnika.id'), nullable=False)
    tip_korisnika = db.relationship('TipKorisnika', backref=db.backref('korisnici', lazy=True))

class TipKorisnika(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv_tipa_korisnika = db.Column(db.String(50), nullable=False)

class Restoran(db.Model):
    id = db.Column(db.String(12), primary_key=True)  # OIB
    naziv_restorana = db.Column(db.String(100), nullable=False)

class RadnoVrijeme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pocetak_radnog_vremena = db.Column(db.Time, nullable=False)
    kraj_radnog_vremena = db.Column(db.Time, nullable=False)
    restoran_id = db.Column(db.String(12), db.ForeignKey('restoran.id'), nullable=False)
    dan_id = db.Column(db.Integer, db.ForeignKey('dan.id'), nullable=False)
    restoran = db.relationship('Restoran', backref=db.backref('radna_vremena', lazy=True))
    dan = db.relationship('Dan', backref=db.backref('radna_vremena', lazy=True))

class Dan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv_dana = db.Column(db.String(20), nullable=False)

class Prostorija(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv_prostorije = db.Column(db.String(100), nullable=False)
    restoran_id = db.Column(db.String(12), db.ForeignKey('restoran.id'), nullable=False)
    restoran = db.relationship('Restoran', backref=db.backref('prostorije', lazy=True))

class Stol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    broj_stola = db.Column(db.Integer, nullable=False)
    broj_mjesta = db.Column(db.Integer, nullable=False)
    prostorija_id = db.Column(db.Integer, db.ForeignKey('prostorija.id'), nullable=False)
    prostorija = db.relationship('Prostorija', backref=db.backref('stolovi', lazy=True))
  


@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=4000)