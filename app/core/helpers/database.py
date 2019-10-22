'''
Helpers for Venue database operations
'''
from ..helpers import *
from datetime import datetime
from sqlalchemy import desc


class DBApi:

    @staticmethod
    def get_genres():
        result = []
        try:
            result = [(genre.name, genre.name) for genre in Genre.query.order_by('name')]
            return result
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def get_states():
        result = []
        try:
            result = [(state.code, state.code) for state in State.query.order_by('code')]
            return result
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def get_venues():
        try:
            venues = Venue.query.all()
            # Generate a unique set of city names
            # and group the venues by city
            cities = set()
            for venue in venues:
                cities.update([venue.address.city.name])
            data = []
            for city in cities:
                tmp = {'city': city, 'venues': []}
                for venue in venues:
                    if venue.address.city.name == city:
                        tmp.update({'state': venue.address.city.state.code})
                        shows = db.session.query(
                            show.c.artist_id.label('artist_id'),
                            Artist.name.label('artist_name'),
                            Artist.image_link.label('artist_image_link'),
                            show.c.start_time.label('start_time')).join(
                                Artist, Artist.id == show.c.artist_id).filter(
                                    show.c.venue_id == venue.id).all()
                        upcoming_shows = [
                            show
                            for show in shows if show.start_time > datetime.now()
                        ]
                        tmp['venues'].append({
                            'id': venue.id,
                            'name': venue.name,
                            "num_upcoming_shows": len(upcoming_shows)})
                data.append(tmp)
            return data
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def get_by_id(cls, _id):
        try:
            instance = cls.query.get(_id)
            data = {
                'id': instance.id,
                'name': instance.name,
                'genres': [genre.name for genre in instance.genres],
                'phone': instance.phone,
                'website': instance.website,
                'facebook_link': instance.facebook_link,
                'seeking_description': instance.seeking_description,
                'image_link': instance.image_link
            }
            if cls is Venue:
                data.update({
                    'city': instance.address.city.name,
                    'state': instance.address.city.state.code,
                    'seeking_talent': instance.seeking_talent,
                    'address': '{} {}'.format(
                        instance.address.house_number, instance.address.street)
                })
                shows = db.session.query(
                    show.c.artist_id.label('artist_id'),
                    Artist.name.label('artist_name'),
                    Artist.image_link.label('artist_image_link'),
                    show.c.start_time.label('start_time')).join(
                        Artist, Artist.id == show.c.artist_id).filter(
                            show.c.venue_id == _id).all()
                past_shows = [
                    {
                        'artist_id': show.artist_id,
                        'artist_name': show.artist_name,
                        'artist_image_link': show.artist_image_link,
                        'start_time': str(show.start_time)
                    }
                    for show in shows if show.start_time <= datetime.now()
                ]
                upcoming_shows = [
                    {
                        'artist_id': show.artist_id,
                        'artist_name': show.artist_name,
                        'artist_image_link': show.artist_image_link,
                        'start_time': str(show.start_time)
                    }
                    for show in shows if show.start_time > datetime.now()
                ]

            if cls is Artist:
                data.update({
                    'city': instance.city.name,
                    'state': instance.city.state.code,
                    'seeking_venue': instance.seeking_venue
                })
                shows = db.session.query(
                    show.c.venue_id.label('venue_id'),
                    Venue.name.label('venue_name'),
                    Venue.image_link.label('venue_image_link'),
                    show.c.start_time.label('start_time')).join(
                        Venue, Venue.id == show.c.venue_id).filter(
                            show.c.artist_id == _id).all()
                past_shows = [
                    {
                        'venue_id': show.venue_id,
                        'venue_name': show.venue_name,
                        'venue_image_link': show.venue_image_link,
                        'start_time': str(show.start_time)
                    }
                    for show in shows if show.start_time <= datetime.now()
                ]
                upcoming_shows = [
                    {
                        'venue_id': show.venue_id,
                        'venue_name': show.venue_name,
                        'venue_image_link': show.venue_image_link,
                        'start_time': str(show.start_time)
                    }
                    for show in shows if show.start_time > datetime.now()
                ]

            data.update({
                'past_shows': past_shows,
                'upcoming_shows': upcoming_shows,
                'past_shows_count': len(past_shows),
                'upcoming_shows_count': len(upcoming_shows),
            })
            return data
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def create(cls, form):
        try:
            state = db.session.query(
                State.id
            ).filter(
                State.code == form.state.data
            ).one()
            city = City.query.filter(
                db.func.lower(City.name) == db.func.lower(form.city.data),
                City.state_id == state.id
            ).first()
            if city is None:
                city = City(name=form.city.data, state_id=state.id)
                db.session.add(city)
                db.session.flush()

            if cls is Venue:
                instance = Venue(
                    name=form.name.data,
                    facebook_link=form.facebook_link.data,
                    image_link=form.image_link.data,
                    website=form.website.data,
                    phone=form.phone.data)
                db.session.add(instance)
                db.session.flush()

                addressList = form.address.data.split(' ', 1)
                house_number = addressList[0]
                street = addressList[1]
                address = Address.query.filter(
                    Address.house_number == house_number,
                    db.func.lower(Address.street) == db.func.lower(street),
                    Address.city_id == city.id
                ).first()

                if address:
                    raise Exception('Invalid address')
                address = Address(
                    house_number=house_number,
                    street=street,
                    city_id=city.id,
                    venue_id=instance.id)
                db.session.add(address)
                db.session.flush()

                for name in form.genres.data:
                    genre = db.session.query(
                        Genre.id
                    ).filter(
                        Genre.name == name
                    ).one()
                    add_genre_to_venue = genre_venue.insert(
                    ).values(
                        venue_id=instance.id,
                        genre_id=genre.id)
                    db.session.execute(add_genre_to_venue)
            if cls is Artist:
                instance = Artist(
                    name=form.name.data,
                    facebook_link=form.facebook_link.data,
                    image_link=form.image_link.data,
                    website=form.website.data,
                    phone=form.phone.data,
                    city_id=city.id)
                db.session.add(instance)
                db.session.flush()

                for name in form.genres.data:
                    genre = db.session.query(
                        Genre.id
                    ).filter(
                        Genre.name == name
                    ).one()
                    add_genre_to_artist = genre_artist.insert(
                    ).values(
                        artist_id=instance.id,
                        genre_id=genre.id)
                    db.session.execute(add_genre_to_artist)
            db.session.commit()
            return True
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def edit(cls, form, _id):
        try:
            state = db.session.query(
                State.id
            ).filter(
                State.code == form.state.data
            ).one()
            city = City.query.filter(
                db.func.lower(City.name) == db.func.lower(form.city.data),
                City.state_id == state.id
            ).first()
            if city is None:
                city = City(
                    name=form.city.data,
                    state_id=state.id)
                db.session.add(city)
                db.session.flush()
            if cls is Venue:
                addressList = form.address.data.split(' ', 1)
                house_number = addressList[0]
                street = addressList[1]
                # check if the input address exists
                address = Address.query.filter(
                    Address.house_number == house_number,
                    db.func.lower(Address.street) == db.func.lower(street),
                    Address.city_id == city.id
                ).first()

                if not address:
                    # delete the venue's old address
                    Address.query.filter(
                        Address.venue_id == _id
                    ).delete()
                    # add the venue's new address
                    address = Address(
                        house_number=house_number,
                        street=street,
                        city_id=city.id,
                        venue_id=_id)
                    db.session.add(address)
                    db.session.flush()
                if address.venue_id != _id:
                    raise Exception('Invalid address')

            instance = cls.query.get(_id)
            instance.name = form.name.data
            instance.phone = form.phone.data
            genres = [
                Genre.query.filter(Genre.name == genre).one()
                for genre in form.genres.data
            ]
            instance.genres = genres
            instance.image_link = form.image_link.data
            instance.facebook_link = form.facebook_link.data
            if cls is Venue:
                instance.seeking_talent = form.seeking_talent.data
                instance.address = address
            if cls is Artist:
                instance.seeking_venue = form.seeking_venue.data
            instance.seeking_description = form.seeking_description.data
            instance.website = form.website.data
            db.session.add(instance)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def delete_venue(venue_id):
        try:
            venue = Venue.query.get(venue_id)
            db.session.delete(venue)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def get_artists():
        try:
            data = []
            artists = db.session.query(
                Artist.id,
                Artist.name).order_by(
                    desc('updated_at')).all()
            for artist in artists:
                data.append({
                    'id': artist.id,
                    'name': artist.name
                })
            return data
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def search_venues_or_artists(cls, search_term):
        search_format = '%{}%'.format(search_term)
        try:
            instances = cls.query.filter(
                db.func.lower(cls.name).like(search_format.lower())
            ).all()
            data = {
                'count': len(instances),
                'data': []
            }
            for instance in instances:
                if cls is Venue:
                    upcoming_shows = db.session.query(
                        db.func.count().label('count')
                    ).filter(
                        show.c.start_time > datetime.now(),
                        show.c.venue_id == instance.id
                    ).all()
                    data['data'].append({
                        'id': instance.id,
                        'name': instance.name,
                        'upcoming_shows': upcoming_shows[0].count
                    })
                if cls is Artist:
                    upcoming_shows = db.session.query(
                        db.func.count().label('count')
                    ).filter(
                        show.c.start_time > datetime.now(),
                        show.c.artist_id == instance.id
                    ).all()
                    data['data'].append({
                        'id': instance.id,
                        'name': instance.name,
                        'upcoming_shows': upcoming_shows[0].count
                    })
            return data
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def create_show(form):
        try:
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
                return True
            raise ValueError('Invalid Artist ID or Venue ID supplied')
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()

    @staticmethod
    def get_shows():
        try:
            shows = db.session.query(
                Venue.name.label('venue'),
                Artist.name.label('artist'),
                Artist.image_link,
                show.c.venue_id,
                show.c.artist_id,
                show.c.start_time
            ).join(
                Venue,
                show.c.venue_id == Venue.id
            ).join(
                Artist,
                show.c.artist_id == Artist.id
            ).order_by(
                desc(show.c.start_time)
            ).all()
            data = []
            for booking in shows:
                data.append({
                    'venue_id': booking.venue_id,
                    'venue_name': booking.venue,
                    'artist_id': booking.artist_id,
                    'artist_name': booking.artist,
                    'artist_image_link': booking.image_link,
                    'start_time': str(booking.start_time)
                })
            return data
        except Exception as error:
            db.session.rollback()
            raise error
        finally:
            db.session.close()
