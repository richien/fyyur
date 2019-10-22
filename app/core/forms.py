from datetime import datetime
from flask_wtf import Form
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
    ValidationError,
    IntegerField,
    BooleanField,
    TextAreaField)
from wtforms.validators import (
    DataRequired,
    AnyOf,
    URL,
    Length,
    Optional)
import phonenumbers


def validate_phone(form, field):
    try:
        input_number = phonenumbers.parse(field.data, 'US')
        if not phonenumbers.is_possible_number(input_number):
            raise ValidationError('Invalid phone number.')
    except Exception as e:
        raise ValidationError(e.args)


def validate_address(form, field):
    address = field.data.split(' ', 1)
    try:
        if len(address) < 2:
            raise ValidationError('Invalid address supplied. Expected format - House-number Street')
        try:
            int(address[0])
        except ValueError:
            raise ValidationError('House-number must be a number.')
    except Exception as e:
        raise ValidationError(e.args)


def validate_start_time(form, field):
    try:
        if field.data < datetime.now():
            raise ValidationError('Cannot create a show in the past')
    except Exception as e:
        raise ValidationError(e.args)


class ShowForm(Form):
    artist_id = IntegerField(
        'artist_id',
        validators=[DataRequired()]
    )
    venue_id = IntegerField(
        'venue_id',
        validators=[DataRequired()]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired(), validate_start_time],
        default=datetime.today()
    )


class VenueForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired(), Length(min=3, max=25)]
    )
    state = SelectField(
        'state', validators=[DataRequired()]
    )
    address = StringField(
        'address', validators=[DataRequired(), validate_address]
    )
    phone = StringField(
        'phone',
        validators=[validate_phone, Length(min=10, max=18)]
    )
    image_link = StringField(
        'image_link', validators=[URL(), Optional()]
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()]
    )
    website = StringField(
        'website', validators=[URL(), Optional()]
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL(), Optional()]
    )
    seeking_talent = BooleanField(
        'seeking_talent'
    )
    seeking_description = TextAreaField(
        'seeking_description'
    )


class ArtistForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired(), Length(min=3, max=25)]
    )
    state = SelectField(
        'state', validators=[DataRequired()]
    )
    phone = StringField(
        'phone',
        validators=[validate_phone, Length(min=10, max=18)]
    )
    image_link = StringField(
        'image_link', validators=[URL(), Optional()]
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()]
    )
    website = StringField(
        'website', validators=[URL(), Optional()]
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL(), Optional()]
    )
    seeking_venue = BooleanField(
        'seeking_venue'
    )
    seeking_description = TextAreaField(
        'seeking_description'
    )
