from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from os import environ
from flask import flash
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URL')
app.config['SECRET_KEY'] = 'top-secret!'
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
    dan_id = db.Column(db.Integer, db.ForeignKey('datum.id'), nullable=False)
    restoran = db.relationship('Restoran', backref=db.backref('radna_vremena', lazy=True))
    dan = db.relationship('Datum', backref=db.backref('radna_vremena', lazy=True))

class Datum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv_dana = db.Column(db.String(20), nullable=False)
    datum_dana = db.Column(db.Date, nullable=False)

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

class Rezervacija(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    korisnik_id = db.Column(db.Integer, db.ForeignKey('korisnik.id'), nullable=False)
    stol_id = db.Column(db.Integer, db.ForeignKey('stol.id'), nullable=False)
    datum_id = db.Column(db.Integer, db.ForeignKey('datum.id'), nullable=False)
    vrijeme_rezervacije = db.Column(db.Time, nullable=False)
    trajanje_rezervacije = db.Column(db.Interval, nullable=False)
    korisnik = db.relationship('Korisnik', backref=db.backref('rezervacije', lazy=True))
    stol = db.relationship('Stol', backref=db.backref('rezervacije', lazy=True))
    datum = db.relationship('Datum', backref=db.backref('rezervacije', lazy=True))
 

@app.route('/')
def home():
        default_content = render_template('partials/homepage.html')
        return render_template('base.html', content = default_content)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm-password')  # This should match the name attribute in the form
        user_type_id = data.get('user_type')

        if not email or not password or not confirm_password or not user_type_id:
            return 'Email, password, confirm password, and user type are required!', 400

        if password != confirm_password:
            return 'Passwords do not match!', 400

        existing_user = Korisnik.query.filter_by(email=email).first()
        if existing_user:
            return 'User already exists!', 409
        else:
            # Hash the password before storing it in the database
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Create a new user
            new_user = Korisnik(email=email, password=hashed_password, tip_korisnika_id=user_type_id)
            db.session.add(new_user)
            db.session.commit()

            flash("Succefully registered!")
            return redirect(url_for("home"))

    tip_korisnici = TipKorisnika.query.all()
    return render_template('register.html', tip_korisnici=tip_korisnici)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return 'Email and password are required!', 400

        # Retrieve the user from the database based on the provided email
        user = Korisnik.query.filter_by(email=email).first()

        if not user:
            return 'User does not exist!', 404
        else:
            # Check if the provided password matches the stored password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password != user.password:
                return 'Invalid email or password!', 401

            return redirect(url_for("home"))

    # If GET request, render the login form
    return render_template('login.html')


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        tip_guest = TipKorisnika(naziv_tipa_korisnika='Guest')
        tip_restaurant_owner = TipKorisnika(naziv_tipa_korisnika='Restaurant Owner')

        db.session.add_all([tip_guest, tip_restaurant_owner])
        db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=4000)