from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from os import environ
from flask import flash
import hashlib
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms import StringField, TimeField, PasswordField, IntegerField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import TextInput
from wtforms.validators import ValidationError
from datetime import timedelta
from wtforms import Field
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.sql import func, and_, or_

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

@event.listens_for(Prostorija, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.naziv_prostorije = target.naziv_prostorije.lower()

@event.listens_for(Prostorija, 'before_update')
def receive_before_update(mapper, connection, target):
    target.naziv_prostorije = target.naziv_prostorije.lower()

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
    datum = db.Column(db.Date, nullable=False)
    vrijeme_rezervacije = db.Column(db.Time, nullable=False)
    trajanje_rezervacije = db.Column(db.Float, nullable=False)
    korisnik = db.relationship('Korisnik', backref=db.backref('rezervacije', lazy=True))
    stol = db.relationship('Stol', backref=db.backref('rezervacije', lazy=True))

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
    datum = DateField('Datum', format='%Y-%m-%d', validators=[DataRequired()])
    vrijeme_rezervacije = TimeField('Vrijeme Rezervacije', validators=[DataRequired()])
    trajanje_rezervacije = SelectField('Trajanje Rezervacije', choices=[(0.5, '0.5 hours'), (1, '1 hour'), (1.5, '1.5 hours'), (2, '2 hours'), (2.5, '2.5 hours'), (3, '3 hours'), (3.5, '3.5 hours'), (4, '4 hours')], coerce=float, validators=[DataRequired()])
    phone = StringField('My number (optional)')
    number_of_persons = IntegerField('Number of persons', validators=[DataRequired()])

# Custom Admin View for Rezervacija
class RezervacijaAdmin(ModelView):
    form = RezervacijaForm

    def on_model_change(self, form, model, is_created):
        model.korisnik_id = form.korisnik.data.id
        model.stol_id = form.stol.data.id
        model.datum = form.datum.data


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

def is_overlapping(reservation, selected_datetime):
    start_time = reservation.vrijeme_rezervacije
    end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=reservation.trajanje_rezervacije) + timedelta(minutes=30)).time()
    selected_time = selected_datetime.time()
    return start_time <= selected_time < end_time
    
@app.route('/')
def home():
    current_prostorija_id = request.args.get('current_prostorija_id', 1, type=int)
    selected_date = request.args.get('date')
    selected_time = request.args.get('time')

    current_prostorija = Prostorija.query.get(current_prostorija_id)
    prev_prostorija = current_prostorija.naziv_prostorije if current_prostorija else None

    return render_template(
        "homepage.html", 
        prev_prostorija=prev_prostorija, 
        current_prostorija_id=current_prostorija_id, 
        selected_date=selected_date, 
        selected_time=selected_time
    )


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
                    session['user_role'] = user.tip_korisnika.naziv_tipa_korisnika
                    return redirect(url_for("home"))

    return render_template('login.html', error=error)

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
                session['user_role'] = new_user.tip_korisnika.naziv_tipa_korisnika

                return redirect(url_for("home"))

    tip_korisnici = TipKorisnika.query.all()
    return render_template('register.html', tip_korisnici=tip_korisnici, error=error)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

@app.route('/next')
def next_prostorija():
    current_prostorija_id = request.args.get('current_prostorija_id', 1, type=int)
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
    current_prostorija_id = request.args.get('current_prostorija_id', 1, type=int)
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
    current_prostorija_id = request.args.get('current_prostorija_id', 1)
    
    if current_prostorija_id is None:
        return redirect(url_for('owner_homepage', current_prostorija_id=1))
    
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
    name = request.form.get('name').strip().lower()
    if name:
        existing_room = Prostorija.query.filter(Prostorija.naziv_prostorije.ilike(name)).first()
        if existing_room:
            flash('A room with this name already exists.', 'danger')
            return redirect(url_for('owner_administration'))
        restoran = Restoran.query.first()
        new_room = Prostorija(naziv_prostorije=name, restoran_id=restoran.id)
        db.session.add(new_room)
        db.session.commit()
        flash('Room sucesfully added.', 'success')
    else:
        flash('Name is required.', 'danger')
    return redirect(url_for('owner_administration'))

@app.route('/table/add', methods=['POST'])
def add_table():
    room_id = request.form.get('room_id')
    number = request.form.get('number')
    seats = request.form.get('seats')
    
    # Validate that seats is a positive integer and within the limit (1 to 20)
    try:
        seats = int(seats)
        if seats <= 0 or seats > 20:
            flash('Number of seats must be between 1 and 20.', 'danger')
            return redirect(url_for('owner_administration'))
    except ValueError:
        flash('Invalid number of seats entered.', 'danger')
        return redirect(url_for('owner_administration'))

    if room_id and number:
        new_table = Stol(prostorija_id=room_id, broj_stola=number, broj_mjesta=seats)
        db.session.add(new_table)
        db.session.commit()
        flash('Table added successfully.', 'success')
    else:
        flash('Missing required fields (room_id, number).', 'error')

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
    selected_date = request.args.get('date')
    selected_time = request.args.get('time')

    if selected_date and selected_time:
        selected_datetime = datetime.strptime(f"{selected_date} {selected_time}", '%Y-%m-%d %H:%M')
        time_before = (selected_datetime - timedelta(minutes=30)).time()
        time_after = (selected_datetime + timedelta(minutes=30)).time()
    else:
        selected_datetime = None
        time_before = None
        time_after = None

    if selected_date and selected_time:
        reservations = Rezervacija.query.filter(
            Rezervacija.stol.has(prostorija_id=room_id),
            Rezervacija.datum == selected_date
        ).all()
        filtered_reservations = [res for res in reservations if is_overlapping(res, selected_datetime)]
    else:
        filtered_reservations = []
    return render_template('partials/table_selector.html', room=room, reservations=filtered_reservations)

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

@app.route('/table/remove', methods=['POST'])
def remove_table():
    room_id = request.form.get('room_id')
    table_id = request.form.get('table_id')
    
    table = Stol.query.get_or_404(table_id)
    db.session.delete(table)
    db.session.commit()
    
    flash("Table removed successfully.", "success")
    return redirect(url_for('owner_administration'))

@app.route('/notifications')
def notification():
    return render_template('notifications.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    restoran = Restoran.query.first()
    radno_vrijeme = RadnoVrijeme.query.filter_by(restoran_id=restoran.id).all()
    
    if request.method == 'POST':
        restoran_name = request.form.get('restoranName')
        if restoran_name:
            restoran.naziv_restorana = restoran_name
            db.session.commit()

        days_of_week = [
            {'id': 1, 'naziv_dana': 'Mon'},
            {'id': 2, 'naziv_dana': 'Tue'},
            {'id': 3, 'naziv_dana': 'Wed'},
            {'id': 4, 'naziv_dana': 'Thu'},
            {'id': 5, 'naziv_dana': 'Fri'},
            {'id': 6, 'naziv_dana': 'Sat'},
            {'id': 7, 'naziv_dana': 'Sun'}
        ]

        for day in days_of_week:
            closed = request.form.get(f'closed_{day["id"]}') == 'on'
            start_time = request.form.get(f'start_{day["id"]}')
            end_time = request.form.get(f'end_{day["id"]}')
            rv = next((rv for rv in radno_vrijeme if rv.dan_id == day['id']), None)

            if closed:
                if rv:
                    db.session.delete(rv)
            else:
                if rv:
                    if start_time and end_time:
                        rv.pocetak_radnog_vremena = datetime.strptime(start_time, '%H:%M').time()
                        rv.kraj_radnog_vremena = datetime.strptime(end_time, '%H:%M').time()
                else:
                    if start_time and end_time:
                        new_rv = RadnoVrijeme(
                            pocetak_radnog_vremena=datetime.strptime(start_time, '%H:%M').time(),
                            kraj_radnog_vremena=datetime.strptime(end_time, '%H:%M').time(),
                            restoran_id=restoran.id,
                            dan_id=day['id']
                        )
                        db.session.add(new_rv)
            db.session.commit()

        flash('Profile updated successfully')
        return redirect(url_for('profile'))

    days_of_week = [
        {'id': 1, 'naziv_dana': 'Mon'},
        {'id': 2, 'naziv_dana': 'Tue'},
        {'id': 3, 'naziv_dana': 'Wed'},
        {'id': 4, 'naziv_dana': 'Thu'},
        {'id': 5, 'naziv_dana': 'Fri'},
        {'id': 6, 'naziv_dana': 'Sat'},
        {'id': 7, 'naziv_dana': 'Sun'}
    ]

    return render_template('profile.html', restoran=restoran, radno_vrijeme=radno_vrijeme, days_of_week=days_of_week)

@app.route('/make_reservation/<int:table_id>', methods=['GET', 'POST'])
def make_reservation(table_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    user = Korisnik.query.get(session['user_id'])
    if user.tip_korisnika.naziv_tipa_korisnika != 'Guest':
        flash('Restaurant Owners cannot reserve tables.')
        return redirect(url_for('home'))

    table = Stol.query.get_or_404(table_id)
    room = table.prostorija
    form = RezervacijaForm()

    if request.method == 'POST':
        reservation = Rezervacija(
            korisnik_id=user.id,
            stol_id=table_id,
            datum=form.datum.data,
            vrijeme_rezervacije=form.vrijeme_rezervacije.data,
            trajanje_rezervacije=form.trajanje_rezervacije.data
        )
        db.session.add(reservation)
        db.session.commit()
        flash('Table reserved successfully.', 'success')
        return render_template('partials/reserve_partial.html', form=form, room=room, table=table, user=user)

    form.korisnik.data = user
    form.stol.data = table
    form.number_of_persons.data = table.broj_mjesta

    return render_template('reserve.html', form=form, room=room, table=table, user=user)

@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    reservation = Rezervacija.query.get_or_404(reservation_id)
    user = Korisnik.query.get(session['user_id'])
    
    if user.id != reservation.korisnik_id:
        flash('You are not authorized to edit this reservation.', 'danger')
        return redirect(url_for('profile'))

    table = reservation.stol
    room = table.prostorija
    form = RezervacijaForm(obj=reservation)

    if request.method == 'POST':
        reservation.datum = form.datum.data
        reservation.vrijeme_rezervacije = form.vrijeme_rezervacije.data
        reservation.trajanje_rezervacije = form.trajanje_rezervacije.data
        db.session.commit()
        flash('Reservation updated successfully.', 'success')
        return render_template('partials/edit_reservation_partial.html', form=form, room=room, table=table, user=user, reservation=reservation)

    form.korisnik.data = user
    form.stol.data = table
    form.number_of_persons.data = table.broj_mjesta

    return render_template('edit_reservation.html', form=form, room=room, table=table, user=user, reservation=reservation)

@app.route('/get-time-options')
def get_time_options():
    selected_date = request.args.get('date')
    day_of_week = datetime.strptime(selected_date, '%Y-%m-%d').weekday() + 1  # Monday is 0 and Sunday is 6

    # Fetch working hours for the selected day
    working_hours = RadnoVrijeme.query.filter_by(dan_id=day_of_week).first()
    if not working_hours:
        return jsonify([])

    start_time = working_hours.pocetak_radnog_vremena
    end_time = working_hours.kraj_radnog_vremena

    # Adjust start and end times
    adjusted_start_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=30)).time()
    adjusted_end_time = (datetime.combine(datetime.today(), end_time) - timedelta(hours=1)).time()

    # Generate time slots between adjusted_start_time and adjusted_end_time at 30-minute intervals
    time_slots = []
    current_time = datetime.combine(datetime.today(), adjusted_start_time)
    end_time = datetime.combine(datetime.today(), adjusted_end_time)
    while current_time <= end_time:
        time_slots.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=30)

    return jsonify(time_slots)

@app.route('/get-available-times/<int:table_id>', methods=['GET'])
def get_available_times(table_id):
    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify([])

    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    day_of_week = selected_date.weekday() + 1  # Monday is 0 and Sunday is 6

    # Fetch working hours for the selected day
    working_hours = RadnoVrijeme.query.filter_by(dan_id=day_of_week).first()
    if not working_hours:
        return jsonify([])

    start_time = working_hours.pocetak_radnog_vremena
    end_time = working_hours.kraj_radnog_vremena

    # Adjust start and end times
    adjusted_start_time = (datetime.combine(selected_date, start_time) + timedelta(minutes=30)).time()
    adjusted_end_time = (datetime.combine(selected_date, end_time) - timedelta(hours=1)).time()

    # Generate a list of all possible times in 30-minute increments within working hours
    current_time = datetime.combine(selected_date, adjusted_start_time)
    end_time = datetime.combine(selected_date, adjusted_end_time)
    possible_times = []
    while current_time <= end_time:
        possible_times.append(current_time)
        current_time += timedelta(minutes=30)

    # Get all reservations for the selected date and table
    reservations = Rezervacija.query.filter_by(stol_id=table_id, datum=selected_date).all()

    # Remove times that overlap with existing reservations and the 30-minute buffer after them
    available_times = []
    for time in possible_times:
        is_available = True
        for reservation in reservations:
            reservation_start = datetime.combine(selected_date, reservation.vrijeme_rezervacije)
            reservation_end = reservation_start + timedelta(hours=reservation.trajanje_rezervacije)
            buffer_end = reservation_end + timedelta(minutes=30)  # 30 minutes buffer after reservation end
            if time < buffer_end and (time + timedelta(minutes=30)) > reservation_start:
                is_available = False
                break
        if is_available:
            available_times.append(time.strftime('%H:%M'))

    return jsonify(available_times)

@app.route('/get-available-days', methods=['GET'])
def get_available_days():
    available_days = RadnoVrijeme.query.all()
    available_day_ids = [day.dan_id for day in available_days]
    return jsonify(available_day_ids)

@app.route('/guest_profile', methods=['GET'])
def guest_profile():
    user_id = session['user_id'] # Assuming you're using Flask-Login to manage user sessions
    reservations = Rezervacija.query.filter_by(korisnik_id=user_id).all()
    return render_template('guest_profile.html', reservations=reservations)

@app.route('/all_reservations', methods=['GET'])
def all_reservations():
    user = Korisnik.query.get(session['user_id'])
    if user.tip_korisnika.naziv_tipa_korisnika != 'Restaurant Owner':
        flash('You are not authorized to access this page.', 'danger')
        return redirect(url_for('home'))

    reservations = Rezervacija.query.all()
    return render_template('all_reservations.html', reservations=reservations)

if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()  # Ukloni ili komentiraj ovu liniju
        db.create_all()
        if Datum.query.count() == 0:
            days_of_week = [
                {'id': 1, 'naziv_dana': 'Mon', 'datum_dana': datetime(2023, 1, 2)},
                {'id': 2, 'naziv_dana': 'Tue', 'datum_dana': datetime(2023, 1, 3)},
                {'id': 3, 'naziv_dana': 'Wed', 'datum_dana': datetime(2023, 1, 4)},
                {'id': 4, 'naziv_dana': 'Thu', 'datum_dana': datetime(2023, 1, 5)},
                {'id': 5, 'naziv_dana': 'Fri', 'datum_dana': datetime(2023, 1, 6)},
                {'id': 6, 'naziv_dana': 'Sat', 'datum_dana': datetime(2023, 1, 7)},
                {'id': 7, 'naziv_dana': 'Sun', 'datum_dana': datetime(2023, 1, 8)}
            ]
            for day in days_of_week:
                datum = Datum(id=day['id'], naziv_dana=day['naziv_dana'], datum_dana=day['datum_dana'])
                db.session.add(datum)
            db.session.commit()
        
        if TipKorisnika.query.count() == 0:
            tip_guest = TipKorisnika(naziv_tipa_korisnika='Guest')
            tip_restaurant_owner = TipKorisnika(naziv_tipa_korisnika='Restaurant Owner')
            db.session.add_all([tip_guest, tip_restaurant_owner])
            db.session.commit()

        if Restoran.query.count() == 0:
            restoran = Restoran(naziv_restorana='The Fiume')
            db.session.add(restoran)
            db.session.commit()

        if Prostorija.query.count() == 0:
            prostorija1 = Prostorija(naziv_prostorije='Ulaz', restoran_id=restoran.id)
            prostorija2 = Prostorija(naziv_prostorije='Prostorija za ručak', restoran_id=restoran.id)
            db.session.add_all([prostorija1, prostorija2])
            db.session.commit()

    app.run(debug=True, host='0.0.0.0', port=4000)