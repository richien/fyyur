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

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
load_dotenv()
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


show = db.Table(
    'Show',
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), nullable=False),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), nullable=False),
    db.Column('start_time', db.DateTime),
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

    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate


class Artist(Base):
    __tablename__ = 'Artist'

    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String())
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    venues = db.relationship('Venue', secondary=show, lazy=True, backref=db.backref('artists', lazy=True))
    genres = db.relationship('Genre', secondary=genre_artist, lazy=True, backref=db.backref('artists', lazy=True))
    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate


class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)


class State(db.Model):
    __tablename__ = 'State'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(2), nullable=False)
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

# TODO Implement Show and Artist models, and complete all model
# relationships and properties, as a database migration.

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
    except:
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


@app.route('/venues/<int:venue_id>')
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
    except:
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
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


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
    except:
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
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
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
    except:
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
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be
    # listed.')
    return render_template('pages/home.html')


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
                    show.c.artist_id == Artist.id).all()
    except:
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
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


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
