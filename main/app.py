from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from os import environ
from flask import flash
import hashlib
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms import StringField, TimeField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import TextInput
from wtforms.validators import ValidationError
from datetime import timedelta
from wtforms import Field

app = Flask(__name__)

# Ensure the DB_URL environment variable is set, else use a default
db_url = environ.get('DB_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SECRET_KEY'] = 'top-secret!'

db = SQLAlchemy(app)
admin = Admin(app, name='Admin', template_mode='bootstrap3')
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
    id = db.Column(db.Integer, primary_key=True)
    naziv_restorana = db.Column(db.String(100), nullable=False)

class RadnoVrijeme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pocetak_radnog_vremena = db.Column(db.Time, nullable=False)
    kraj_radnog_vremena = db.Column(db.Time, nullable=False)
    restoran_id = db.Column(db.Integer, db.ForeignKey('restoran.id'), nullable=False)
    dan_id = db.Column(db.Integer, db.ForeignKey('datum.id'), nullable=False)
    restoran = db.relationship('Restoran', backref=db.backref('radna_vremena', lazy=True))
    dan = db.relationship('Datum', backref=db.backref('radna_vremena', lazy=True))

class Datum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv_dana = db.Column(db.String(20), nullable=False)
    datum_dana = db.Column(db.Date, nullable=False)

class Prostorija(db.Model):
    __tablename__ = 'prostorija'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    naziv_prostorije = db.Column(db.String(100), nullable=False)
    restoran_id = db.Column(db.Integer, db.ForeignKey('restoran.id'), nullable=False)
    restoran = db.relationship('Restoran', backref=db.backref('prostorije', lazy=True))

class Stol(db.Model):
    __tablename__ = 'stol'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    broj_stola = db.Column(db.Integer, nullable=False)
    broj_mjesta = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Boolean, default=True)
    x = db.Column(db.Integer, nullable=False, default=0)
    y = db.Column(db.Integer, nullable=False, default=0)
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

class KorisnikForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    tip_korisnika = QuerySelectField('Tip Korisnika', query_factory=lambda: TipKorisnika.query.all(), get_label='naziv_tipa_korisnika')

# Custom Admin View for Korisnik
class KorisnikAdmin(ModelView):
    form = KorisnikForm

    def on_model_change(self, form, model, is_created):
        model.tip_korisnika_id = form.tip_korisnika.data.id


class RadnoVrijemeForm(FlaskForm):
    pocetak_radnog_vremena = TimeField('Početak Radnog Vremena', validators=[DataRequired()])
    kraj_radnog_vremena = TimeField('Kraj Radnog Vremena', validators=[DataRequired()])
    restoran = QuerySelectField('Restoran', query_factory=lambda: Restoran.query.all(), get_label='naziv_restorana')
    dan = QuerySelectField('Dan', query_factory=lambda: Datum.query.all(), get_label='naziv_dana')


# Custom Admin View for RadnoVrijeme
class RadnoVrijemeAdmin(ModelView):
    form = RadnoVrijemeForm

    def on_model_change(self, form, model, is_created):
        model.restoran_id = form.restoran.data.id
        model.dan_id = form.dan.data.id

class ProstorijaForm(FlaskForm):
    naziv_prostorije = StringField('Naziv Prostorije', validators=[DataRequired()])
    restoran = QuerySelectField('Restoran', query_factory=lambda: Restoran.query.all(), get_label='naziv_restorana')

# Custom Admin View for Prostorija
class ProstorijaAdmin(ModelView):
    form = ProstorijaForm
    def on_model_change(self, form, model, is_created):
        model.restoran_id = form.restoran.data.id

class StolForm(FlaskForm):
    broj_stola = IntegerField('Broj Stola', validators=[DataRequired()])
    broj_mjesta = IntegerField('Broj Mjesta', validators=[DataRequired()])
    prostorija = QuerySelectField('Prostorija', query_factory=lambda: Prostorija.query.all(), get_label='naziv_prostorije')

# Custom Admin View for Stol
class StolAdmin(ModelView):
    form = StolForm

    def on_model_change(self, form, model, is_created):
        model.prostorija_id = form.prostorija.data.id

class TimeDeltaField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return str(self.data)
        else:
            return '0:00:00'

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                h, m, s = map(int, valuelist[0].split(':'))
                self.data = timedelta(hours=h, minutes=m, seconds=s)
            except ValueError:
                self.data = None
                raise ValidationError('Invalid time delta format')
            
class RezervacijaForm(FlaskForm):
    korisnik = QuerySelectField('Korisnik', query_factory=lambda: Korisnik.query.all(), get_label='email')
    stol = QuerySelectField('Stol', query_factory=lambda: Stol.query.all(), get_label='broj_stola')
    datum = QuerySelectField('Datum', query_factory=lambda: Datum.query.all(), get_label='naziv_dana')
    vrijeme_rezervacije = TimeField('Vrijeme Rezervacije', validators=[DataRequired()])
    trajanje_rezervacije = TimeDeltaField('Trajanje Rezervacije', validators=[DataRequired()])

# Custom Admin View for Rezervacija
class RezervacijaAdmin(ModelView):
    form = RezervacijaForm

    def on_model_change(self, form, model, is_created):
        model.korisnik_id = form.korisnik.data.id
        model.stol_id = form.stol.data.id
        model.datum_id = form.datum.data.id


# Add views
admin.add_view(KorisnikAdmin(Korisnik, db.session))
admin.add_view(ModelView(TipKorisnika, db.session))
admin.add_view(ModelView(Restoran, db.session))
admin.add_view(RadnoVrijemeAdmin(RadnoVrijeme, db.session))
admin.add_view(ModelView(Datum, db.session))
admin.add_view(ProstorijaAdmin(Prostorija, db.session))
admin.add_view(StolAdmin(Stol, db.session))
admin.add_view(RezervacijaAdmin(Rezervacija, db.session))


current_prostorija_id = None  # Declare current_prostorija_id as a global variable with initial value None

# @app.route('/')
# def home():
#     current_prostorija_id = request.args.get('current_prostorija_id') 

#     if current_prostorija_id is None:
#         return redirect(url_for('home', current_prostorija_id=0))
    
#     current_prostorija = -4818
#     if current_prostorija_id != '-4818':
#         current_prostorija = Prostorija.query.get(current_prostorija_id)
    
#     prev_prostorija = current_prostorija.naziv_prostorije if current_prostorija else None
#     return render_template("homepage.html", prev_prostorija=prev_prostorija, current_prostorija_id=current_prostorija_id)

@app.route('/')
def home():
    current_prostorija_id = request.args.get('current_prostorija_id') 

    if current_prostorija_id is None:
        return redirect(url_for('home', current_prostorija_id=1))
    
    current_prostorija = -4818
    if current_prostorija_id != '-4818':
        current_prostorija = Prostorija.query.get(current_prostorija_id)
    
    prev_prostorija = current_prostorija.naziv_prostorije if current_prostorija else None

    return render_template("homepage.html", prev_prostorija=prev_prostorija, current_prostorija_id=current_prostorija_id, selected_date=selected_date, selected_time=selected_time)


@app.route('/register', methods=['POST', 'GET'])
def register():
    error = None
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm-password')
        user_type_id = data.get('user_type')

        if not email or not password or not confirm_password or not user_type_id:
            error = 'Email, password, confirm password, and user type are required!'
        elif password != confirm_password:
            error = 'Passwords do not match!'
        else:
            existing_user = Korisnik.query.filter_by(email=email).first()
            if existing_user:
                error = 'User already exists!'
            else:
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                new_user = Korisnik(email=email, password=hashed_password, tip_korisnika_id=user_type_id)
                db.session.add(new_user)
                db.session.commit()

                session['logged_in'] = True
                session['user_id'] = new_user.id

                # Redirect based on the user role
                if new_user.tip_korisnika.naziv_tipa_korisnika == 'Guest':
                    return redirect(url_for("home"))
                elif new_user.tip_korisnika.naziv_tipa_korisnika == 'Restaurant Owner':
                    return redirect(url_for("owner_homepage"))

    tip_korisnici = TipKorisnika.query.all()
    return render_template('register.html', tip_korisnici=tip_korisnici, error=error)



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            error = 'Email and password are required!'
        else:
            user = Korisnik.query.filter_by(email=email).first()
            if not user:
                error = 'User does not exist!'
            else:
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                if hashed_password != user.password:
                    error = 'Invalid email or password!'
                else:
                    session['logged_in'] = True
                    session['user_id'] = user.id
                    # Redirect based on the user role
                    if user.tip_korisnika.naziv_tipa_korisnika == 'Guest':
                        return redirect(url_for("home"))
                    elif user.tip_korisnika.naziv_tipa_korisnika == 'Restaurant Owner':
                        return redirect(url_for("owner_homepage"))

    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/next')
def next_prostorija():
    current_prostorija_id = request.args.get('current_prostorija_id', 0, type=int)
    selected_date = request.args.get('date')
    selected_time = request.args.get('time')

    next_prostorija_id = current_prostorija_id + 1
    next_prostorija = Prostorija.query.get(next_prostorija_id)
    if next_prostorija:
        return redirect(url_for('home', current_prostorija_id=next_prostorija_id, date=selected_date, time=selected_time))
    else:
        return redirect(url_for('home', current_prostorija_id=current_prostorija_id, date=selected_date, time=selected_time))

@app.route('/prev')
def prev_prostorija():
    current_prostorija_id = request.args.get('current_prostorija_id', 0, type=int)
    selected_date = request.args.get('date')
    selected_time = request.args.get('time')

    prev_prostorija_id = current_prostorija_id - 1
    prev_prostorija = Prostorija.query.get(prev_prostorija_id)
    if prev_prostorija:
        return redirect(url_for('home', current_prostorija_id=prev_prostorija_id, date=selected_date, time=selected_time))
    else:
        return redirect(url_for('home', current_prostorija_id=current_prostorija_id, date=selected_date, time=selected_time))

@app.route('/reserve_table', methods=['POST'])
def reserve_table():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('rezervacija.action_view'))
    
@app.route('/owner')
def owner_homepage():
    current_prostorija_id = request.args.get('current_prostorija_id', None)
    
    if current_prostorija_id is None:
        return redirect(url_for('owner_homepage', current_prostorija_id=0))
    
    current_prostorija_id = int(current_prostorija_id)
    current_prostorija = Prostorija.query.get(current_prostorija_id)
    
    prev_prostorija = Prostorija.query.get(current_prostorija_id - 1) if current_prostorija_id > 0 else None
    next_prostorija = Prostorija.query.get(current_prostorija_id + 1)

    return render_template(
        "owner_homepage.html", 
        current_prostorija_id=current_prostorija_id,
        current_prostorija=current_prostorija,
        prev_prostorija=prev_prostorija,
        next_prostorija=next_prostorija
    )

@app.route('/owner_prev')
def owner_prev_prostorija():
    current_prostorija_id = request.args.get('current_prostorija_id', None)
    prev_prostorija_id = int(current_prostorija_id) - 1 if current_prostorija_id is not None else 0
    prev_prostorija = Prostorija.query.get(prev_prostorija_id)
    if prev_prostorija:
        return redirect(url_for('owner_homepage', current_prostorija_id=prev_prostorija_id))
    else:
        return redirect(url_for('owner_homepage', current_prostorija_id=current_prostorija_id or 0))

@app.route('/owner_next')
def owner_next_prostorija():
    current_prostorija_id = request.args.get('current_prostorija_id', None)
    next_prostorija_id = int(current_prostorija_id) + 1 if current_prostorija_id is not None else 1
    next_prostorija = Prostorija.query.get(next_prostorija_id)
    if next_prostorija:
        return redirect(url_for('owner_homepage', current_prostorija_id=next_prostorija_id))
    else:
        return redirect(url_for('owner_homepage', current_prostorija_id=current_prostorija_id or 0))
    
@app.route('/owner_administration')
def owner_administration():
    rooms = Prostorija.query.all()
    return render_template('owner_administration.html', rooms=rooms)

@app.route('/room/add', methods=['POST'])
def add_room():
    name = request.form.get('name')
    if name:
        restoran = Restoran.query.first()
        new_room = Prostorija(naziv_prostorije=name, restoran_id = restoran.id)
        db.session.add(new_room)
        db.session.commit()
    return redirect(url_for('owner_administration'))

@app.route('/table/add', methods=['POST'])
def add_table():
    room_id = request.form.get('room_id')
    number = request.form.get('number')
    seats = request.form.get('seats')
    if room_id and number and seats:
        new_table = Stol(prostorija_id=room_id, broj_stola=number, broj_mjesta=seats)
        db.session.add(new_table)
        db.session.commit()
    return redirect(url_for('owner_administration'))

@app.route('/table/update/<int:room_id>/<int:table_id>', methods=['POST'])
def update_table(room_id, table_id):
    table = Stol.query.get_or_404(table_id)
    room = Prostorija.query.get_or_404(room_id)
    table.broj_mjesta = request.form.get('seats')
    table.available = request.form.get('available') == 'true'
    db.session.commit()
    return render_template('partials/table_edit.html', table=table, room=room)

@app.route('/room/<int:room_id>/tables')
def get_tables(room_id):
    room = Prostorija.query.get_or_404(room_id)
    return render_template('partials/tables.html', room=room)

@app.route('/room/<int:room_id>/guest_layout', methods=['GET'])
def guest_layout(room_id):
    room = Prostorija.query.get_or_404(room_id)
    return render_template('partials/table_selector.html', room=room)

@app.route('/room/<int:room_id>/layout', methods=['GET'])
def room_layout(room_id):
    room = Prostorija.query.get_or_404(room_id)
    return render_template('layout.html', room=room)

@app.route('/room/<int:room_id>/layout/save', methods=['POST'])
def save_layout(room_id):
    room = Prostorija.query.get_or_404(room_id)
    layout_data = request.json.get('layout')
    for table_data in layout_data:
        table = Stol.query.get_or_404(table_data['id'])
        table.x = table_data['x']
        table.y = table_data['y']
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        tip_guest = TipKorisnika(naziv_tipa_korisnika='Guest')
        tip_restaurant_owner = TipKorisnika(naziv_tipa_korisnika='Restaurant Owner')

        # Create instances of Restoran
        restoran = Restoran(naziv_restorana='The Fiume')
        db.session.add_all([tip_guest, tip_restaurant_owner, restoran])
        db.session.commit()

        # Create instances of Prostorija
        prostorija1 = Prostorija(naziv_prostorije='Ulaz', restoran_id=restoran.id)
        prostorija2 = Prostorija(naziv_prostorije='Prostorija za ručak', restoran_id=restoran.id)
        db.session.add_all([prostorija1, prostorija2])
        db.session.commit()

        db.session.add_all([tip_guest, tip_restaurant_owner])
        db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=4000)