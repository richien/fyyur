# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from dotenv import load_dotenv
from sqlalchemy import desc
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
load_dotenv()
app = Flask(__name__)
csrf = CSRFProtect(app)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


show = db.Table(
    'Show',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), nullable=False),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), nullable=False),
    db.Column('start_time', db.DateTime, nullable=False),
    db.Column('id', db.Integer, primary_key=True)
)

genre_artist = db.Table(
    'GenreArtist',
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
)

genre_venue = db.Table(
    'GenreVenue',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
)


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String())
    facebook_link = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now())


class Venue(Base):
    __tablename__ = 'Venue'

    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String())
    address_id = db.Column(db.Integer, db.ForeignKey('Address.id'), nullable=False)
    genres = db.relationship('Genre', secondary=genre_venue, lazy=True, backref=db.backref('venues', lazy=True))


class Artist(Base):
    __tablename__ = 'Artist'

    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String())
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    venues = db.relationship('Venue', secondary=show, lazy=True, backref=db.backref('artists', lazy=True))
    genres = db.relationship('Genre', secondary=genre_artist, lazy=True, backref=db.backref('artists', lazy=True))


class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class State(db.Model):
    __tablename__ = 'State'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(2), unique=True, nullable=False)
    cities = db.relationship('City', backref='state', lazy=True)


class City(db.Model):
    __tablename__ = 'City'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    addresses = db.relationship('Address', backref='city', lazy=True)
    state_id = db.Column(db.Integer, db.ForeignKey('State.id'), nullable=False)
    artists = db.relationship('Artist', backref='city', lazy=True)


class Address(db.Model):
    __tablename__ = 'Address'

    id = db.Column(db.Integer, primary_key=True)
    house_number = db.Column(db.Integer, nullable=False)
    street = db.Column(db.String(120), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    venue = db.relationship('Venue', backref='address', uselist=False, lazy=True)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO:
    # num_shows should be aggregated based on number of upcoming shows per
    # venue.
    try:
        venues = db.session.query(
            Venue.name,
            Venue.id,
            Address.city_id).join(
                Address,
                Address.id == Venue.address_id
        ).subquery()

        query_result = db.session.query(
            City.name.label('city'),
            State.code.label('state'),
            venues.c.id,
            venues.c.name
        ).join(
            City, State.id == City.state_id
        ).join(
            venues, City.id == venues.c.city_id
        ).all()
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()

    cities = set()
    for item in query_result:
        cities.update([item.city])

    data = []

    for city in cities:
        tmp = {'city': city, 'venues': []}
        for item in query_result:
            if item.city == city:
                tmp.update({'state': item.state})
                tmp['venues'].append({'id': item.id, 'name': item.name})
        data.append(tmp)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"
    response = {
        "count": 1,
        "data": [{
            "id": 2,
            "name": "The Dueling Pianos Bar",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    try:
        genres_result = db.session.query(
            Genre.name).join(genre_venue, genre_venue.c.genre_id == Genre.id).filter(
                genre_venue.c.venue_id == venue_id).all()

        venue_result = db.session.query(
            Venue,
            Address.house_number,
            Address.street,
            City.name.label('city'),
            State.code.label('state')).join(
                Address, Address.id == Venue.address_id).join(
                    City, City.id == Address.city_id).join(
                        State, State.id == City.state_id).filter(
                            Venue.id == venue_id).one()

        shows_result = db.session.query(
            show.c.artist_id.label('artist_id'),
            Artist.name.label('artist_name'),
            Artist.image_link.label('artist_image_link'),
            show.c.start_time.label('start_time')).join(
                Artist, Artist.id == show.c.artist_id).filter(
                    show.c.venue_id == venue_id).all()
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()

    past_shows = [
        {
            'artist_id': show.artist_id,
            'artist_name': show.artist_name,
            'artist_image_link': show.artist_image_link,
            'start_time': str(show.start_time)
        }
        for show in shows_result if show.start_time <= datetime.now()
    ]
    upcoming_shows = [
        {
            'artist_id': show.artist_id,
            'artist_name': show.artist_name,
            'artist_image_link': show.artist_image_link,
            'start_time': str(show.start_time)
        }
        for show in shows_result if show.start_time > datetime.now()
    ]

    data = {
        'id': venue_result.Venue.id,
        'name': venue_result.Venue.name,
        'genres': [genre.name for genre in genres_result],
        'address': '{} {}'.format(venue_result.house_number, venue_result.street),
        'city': venue_result.city,
        'state': venue_result.state,
        'phone': venue_result.Venue.phone,
        'website': venue_result.Venue.website,
        'facebook_link': venue_result.Venue.facebook_link,
        'seeking_talent': venue_result.Venue.seeking_talent,
        'seeking_description': venue_result.Venue.seeking_description,
        'image_link': venue_result.Venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    form.genres.choices = [(genre.name, genre.name) for genre in Genre.query.order_by('name')]
    form.state.choices = [(state.code, state.code) for state in State.query.order_by('code')]
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm(request.form)
        form.genres.choices = [(genre.name, genre.name) for genre in Genre.query.order_by('name')]
        form.state.choices = [(state.code, state.code) for state in State.query.order_by('code')]
        if form.validate():
            state = db.session.query(State.id).filter(State.code == form.state.data).one()
            city = City.query.filter(db.func.lower(City.name) == db.func.lower(form.city.data), City.state_id == state.id).first()
            if city is None:
                city = City(name=form.city.data, state_id=state.id)
                db.session.add(city)
                db.session.flush()

            addressList = form.address.data.split(' ', 1)
            house_number = addressList[0]
            street = addressList[1]
            address = Address.query.filter(
                Address.house_number == house_number,
                db.func.lower(Address.street) == db.func.lower(street)).first()
            if not address:
                address = Address(house_number=house_number, street=street, city_id=city.id)
                db.session.add(address)
                db.session.flush()

            venue = Venue(
                name=form.name.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website.data,
                phone=form.phone.data,
                address_id=address.id)
            db.session.add(venue)
            db.session.flush()

            for name in form.genres.data:
                genre = db.session.query(Genre.id).filter(Genre.name == name).one()
                add_genre_to_venue = genre_venue.insert().values(venue_id=venue.id, genre_id=genre.id)
                db.session.execute(add_genre_to_venue)

            db.session.commit()
            flash('Venue ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.', 'error')
    finally:
        db.session.close()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the
    # homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    try:
        data = db.session.query(
            Artist.id,
            Artist.name).order_by(
                desc('updated_at')).all()
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 1,
        "data": [{
            "id": 4,
            "name": "Guns N Petals",
            "num_upcoming_shows": 0,
        }]
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get(
            'search_term',
            ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    try:
        genres_result = db.session.query(
            Genre.name).join(genre_artist, genre_artist.c.genre_id == Genre.id).filter(
                genre_artist.c.artist_id == artist_id).all()

        artist_result = db.session.query(
            Artist,
            City.name.label('city'),
            State.code.label('state')).join(
                City, City.id == Artist.city_id).join(
                    State, State.id == City.state_id).filter(
                        Artist.id == artist_id).one()

        shows_result = db.session.query(
            show.c.venue_id.label('venue_id'),
            Venue.name.label('venue_name'),
            Venue.image_link.label('venue_image_link'),
            show.c.start_time.label('start_time')).join(
                Venue, Venue.id == show.c.venue_id).filter(
                    show.c.artist_id == artist_id).all()
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()

    past_shows = [
        {
            'venue_id': show.venue_id,
            'venue_name': show.venue_name,
            'venue_image_link': show.venue_image_link,
            'start_time': str(show.start_time)
        }
        for show in shows_result if show.start_time <= datetime.now()
    ]
    upcoming_shows = [
        {
            'venue_id': show.venue_id,
            'venue_name': show.venue_name,
            'venue_image_link': show.venue_image_link,
            'start_time': str(show.start_time)
        }
        for show in shows_result if show.start_time > datetime.now()
    ]

    data = {
        'id': artist_result.Artist.id,
        'name': artist_result.Artist.name,
        'genres': [genre.name for genre in genres_result],
        'city': artist_result.city,
        'state': artist_result.state,
        'phone': artist_result.Artist.phone,
        'website': artist_result.Artist.website,
        'facebook_link': artist_result.Artist.facebook_link,
        'seeking_venue': artist_result.Artist.seeking_venue,
        'seeking_description': artist_result.Artist.seeking_description,
        'image_link': artist_result.Artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    try:
        artist_data = db.session.query(
            Artist,
            City.name.label('city'),
            State.code.label('state')
        ).join(
            City,
            City.id == Artist.city_id
        ).join(
            State,
            State.id == City.state_id
        ).filter(
            Artist.id == artist_id
        ).first()
        artist = {
            'id': artist_data.Artist.id,
            'name': artist_data.Artist.name,
            'genres': artist_data.Artist.genres,
            'city': artist_data.city,
            'state': artist_data.state,
            'phone': artist_data.Artist.phone,
            'website': artist_data.Artist.website,
            'facebook_link': artist_data.Artist.facebook_link,
            'seeking_venue': artist_data.Artist.seeking_venue,
            'seeking_description': artist_data.Artist.seeking_description,
            'image_link': artist_data.Artist.image_link
        }

    except Exception:
        db.session.rollback()
    finally:
        db.session.close()

        genres = []
    form = ArtistForm()
    form.genres.choices = [
        (genre.name, genre.name)
        for genre in Genre.query.order_by('name')
    ]
    form.state.choices = [
        (state.code, state.code)
        for state in State.query.order_by('code')
    ]
    form.name.default = artist['name']
    form.phone.default = artist['phone']
    for genre in artist['genres']:
        genres.append(genre.name)
    form.genres.default = genres
    form.state.default = artist['state']
    form.city.default = artist['city']
    form.facebook_link.default = artist['facebook_link']
    form.image_link.default = artist['image_link']
    form.website.default = artist['website']
    form.seeking_description.default = artist['seeking_description']
    form.seeking_venue.default = artist['seeking_venue']
    form.process()

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        form = ArtistForm(request.form)
        form.genres.choices = [
            (genre.name, genre.name)
            for genre in Genre.query.order_by('name')
        ]
        form.state.choices = [
            (state.code, state.code)
            for state in State.query.order_by('code')
        ]
        if form.validate_on_submit():
            state = db.session.query(
                State.id
            ).filter(
                State.code == form.state.data
            ).one()
            city = City.query.filter(
                db.func.lower(City.name) == db.func.lower(form.city.data),
                City.state_id == state.id).first()
            if city is None:
                city = City(name=form.city.data, state_id=state.id)
                db.session.add(city)
                db.session.flush()

            artist = Artist.query.get(artist_id)
            artist.name = form.name.data
            artist.phone = form.phone.data
            artist.city = city
            genres = [
                Genre.query.filter(Genre.name == genre).one()
                for genre in form.genres.data
            ]
            artist.genres = genres
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            artist.website = form.website.data
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + form.name.data + ' was successfully updated!')
            return redirect(url_for('show_artist', artist_id=artist_id))
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(
                error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error'
            )
    except Exception:
        flash('An error occurred. Artist ' + form.name.data + ' could not be updated.', 'error')
        db.session.rollback()
    finally:
        db.session.close()
    artist = dict(request.form)
    artist.update({'id': artist_id})
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    try:
        venue_data = db.session.query(
            Venue,
            City.name.label('city'),
            State.code.label('state'),
            Address.house_number,
            Address.street
        ).join(
            Address,
            Address.id == Venue.address_id
        ).join(
            City,
            City.id == Address.city_id
        ).join(
            State, State.id == City.state_id
        ).filter(
            Venue.id == venue_id
        ).first()
        venue = {
            'id': venue_data.Venue.id,
            'name': venue_data.Venue.name,
            'genres': venue_data.Venue.genres,
            'address': str(venue_data.house_number) + ' ' + venue_data.street,
            'city': venue_data.city,
            'state': venue_data.state,
            'phone': venue_data.Venue.phone,
            'website': venue_data.Venue.website,
            'facebook_link': venue_data.Venue.facebook_link,
            'seeking_talent': venue_data.Venue.seeking_talent,
            'seeking_description': venue_data.Venue.seeking_description,
            'image_link': venue_data.Venue.image_link
        }
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()
    genres = []
    form = VenueForm()
    form.genres.choices = [
        (genre.name, genre.name)
        for genre in Genre.query.order_by('name')
    ]
    form.state.choices = [
        (state.code, state.code)
        for state in State.query.order_by('code')
    ]
    form.name.default = venue['name']
    form.phone.default = venue['phone']
    form.address.default = venue['address']
    for genre in venue['genres']:
        genres.append(genre.name)
    form.genres.default = genres
    form.state.default = venue['state']
    form.city.default = venue['city']
    form.facebook_link.default = venue['facebook_link']
    form.image_link.default = venue['image_link']
    form.website.default = venue['website']
    form.seeking_description.default = venue['seeking_description']
    form.seeking_talent.default = venue['seeking_talent']
    form.process()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm(request.form)
        form.genres.choices = [
            (genre.name, genre.name)
            for genre in Genre.query.order_by('name')
        ]
        form.state.choices = [
            (state.code, state.code)
            for state in State.query.order_by('code')
        ]
        if form.validate_on_submit():
            state = db.session.query(State.id).filter(
                State.code == form.state.data).one()
            city = City.query.filter(
                db.func.lower(City.name) == db.func.lower(form.city.data),
                City.state_id == state.id).first()
            if city is None:
                city = City(name=form.city.data, state_id=state.id)
                db.session.add(city)
                db.session.flush()

            addressList = form.address.data.split(' ', 1)
            house_number = addressList[0]
            street = addressList[1]
            address = Address.query.filter(
                Address.house_number == house_number,
                db.func.lower(Address.street) == db.func.lower(street)).first()
            if not address:
                address = Address(
                    house_number=house_number,
                    street=street,
                    city_id=city.id)
                db.session.add(address)
                db.session.flush()
            venue = Venue.query.get(venue_id)
            venue.name = form.name.data
            venue.phone = form.phone.data
            genres = [
                Genre.query.filter(Genre.name == genre).one()
                for genre in form.genres.data
            ]
            venue.genres = genres
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.website = form.website.data
            venue.address = address
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + form.name.data + ' was successfully updated!')
            return redirect(url_for('show_venue', venue_id=venue_id))
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(
                error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error'
            )
    except Exception as e:
        flash('An error occurred. Venue ' + form.name.data + ' could not be updated.', 'error')
        db.session.rollback()
    finally:
        db.session.close()
    venue = dict(request.form)
    venue.update({'id': venue_id})
    return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    form.genres.choices = [(g.name, g.name) for g in Genre.query.order_by('name')]
    form.state.choices = [(s.code, s.code) for s in State.query.order_by('code')]
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        form = ArtistForm(request.form)
        form.genres.choices = [(g.name, g.name) for g in Genre.query.order_by('name')]
        form.state.choices = [(s.code, s.code) for s in State.query.order_by('code')]
        if form.validate():
            state = db.session.query(State.id).filter(State.code == form.state.data).one()
            city = City.query.filter(
                db.func.lower(City.name) == db.func.lower(form.city.data),
                City.state_id == state.id).first()
            if city is None:
                city = City(name=form.city.data, state_id=state.id)
                db.session.add(city)
                db.session.flush()

            artist = Artist(
                name=form.name.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website.data,
                phone=form.phone.data,
                city_id=city.id)
            db.session.add(artist)
            db.session.flush()

            for name in form.genres.data:
                genre = db.session.query(Genre.id).filter(Genre.name == name).one()
                add_genre_to_artist = genre_artist.insert().values(artist_id=artist.id, genre_id=genre.id)
                db.session.execute(add_genre_to_artist)

            db.session.commit()
            flash('Artist ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except Exception:
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')
    finally:
        db.session.close()
    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO:
    # num_shows should be aggregated based on number of upcoming shows per
    # venue.
    try:
        query_result = db.session.query(
            Venue.name.label('venue'),
            Artist.name.label('artist'),
            Artist.image_link,
            show.c.venue_id,
            show.c.artist_id,
            show.c.start_time).join(
                Venue,
                show.c.venue_id == Venue.id).join(
                    Artist,
                    show.c.artist_id == Artist.id).order_by(
                        desc(show.c.start_time)).all()
    except Exception:
        db.session.rollback()
    finally:
        db.session.close()

    data = []
    for item in query_result:
        data.append({
            'venue_id': item.venue_id,
            'venue_name': item.venue,
            'artist_id': item.artist_id,
            'artist_name': item.artist,
            'artist_image_link': item.image_link,
            'start_time': str(item.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        form = ShowForm(request.form)
        if form.validate():
            artist = db.session.query(Artist.id).filter(
                Artist.id == form.artist_id.data).first()
            venue = db.session.query(Venue.id).filter(
                Venue.id == form.venue_id.data).first()
            if venue and artist:
                new_show = show.insert().values(
                    venue_id=venue.id,
                    artist_id=artist.id,
                    start_time=form.start_time.data)
                db.session.execute(new_show)
                db.session.commit()
                flash('Show was successfully listed!')
                return render_template('pages/home.html')
            flash('Invalid Artist ID or Venue ID supplied', 'error')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.', 'error')
    finally:
        db.session.close()
    return render_template('forms/new_show.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
