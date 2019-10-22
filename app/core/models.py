from app import db


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
    address = db.relationship('Address', uselist=False, cascade="all, delete-orphan, delete", back_populates="venue", lazy=True)
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
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', onupdate="CASCADE"), nullable=False)
    venue = db.relationship('Venue', back_populates="address", lazy=True)
