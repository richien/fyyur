import json
from flask import (
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    Blueprint
)

from app import csrf
from app.core.models import (
    Venue,
    Artist
)
from app.core.forms import (
    VenueForm,
    ArtistForm,
    ShowForm
)

from app.core.helpers.database import DBApi

core_module = Blueprint('core', __name__, url_prefix='/')


@core_module.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@core_module.route('/venues')
def venues():
    try:
        data = DBApi.get_venues()
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template('pages/venues.html', areas=data, count=len(data))


@core_module.route('/venues/search', methods=['POST'])
def search_venues():
    # search on venues with partial string search.
    search_term = request.form.get('search_term', '')
    try:
        response = DBApi.search_venues_or_artists(Venue, search_term)
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=search_term)


@core_module.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    try:
        data = DBApi.get_by_id(Venue, venue_id)
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@core_module.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    try:
        form.genres.choices = DBApi.get_genres()
        form.state.choices = DBApi.get_states()
    except Exception:
        flash('Oops something went wrong', 'error')
    return render_template('forms/new_venue.html', form=form)


@core_module.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form = VenueForm(request.form)
        form.genres.choices = DBApi.get_genres()
        form.state.choices = DBApi.get_states()
        if form.validate():
            DBApi.create(Venue, form)
            flash('Venue ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except Exception as e:
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.', 'error')
    return render_template('forms/new_venue.html', form=form)


@core_module.route('/venues/<int:venue_id>', methods=['DELETE'])
@csrf.exempt
def delete_venue(venue_id):
    try:
        DBApi.delete_venue(venue_id)
    except Exception:
        flash('An error occurred. \nUnable to delete venue!', 'error')
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@core_module.route('/artists')
def artists():
    try:
        data = DBApi.get_artists()
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template('pages/artists.html', artists=data, count=len(data))


@core_module.route('/artists/search', methods=['POST'])
def search_artists():
    # Search on artists with partial string search.
    search_term = request.form.get('search_term', '')
    try:
        response = DBApi.search_venues_or_artists(Artist, search_term)
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=search_term)


@core_module.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    try:
        data = DBApi.get_by_id(Artist, artist_id)
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@core_module.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    try:
        artist = DBApi.get_by_id(Artist, artist_id)
        genre_choices = DBApi.get_genres()
        state_choices = DBApi.get_states()
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    # Prepare the form for editing
    form = ArtistForm()
    form.genres.choices = genre_choices
    form.state.choices = state_choices
    form.name.default = artist['name']
    form.phone.default = artist['phone']
    form.genres.default = artist['genres']
    form.state.default = artist['state']
    form.city.default = artist['city']
    form.facebook_link.default = artist['facebook_link']
    form.image_link.default = artist['image_link']
    form.website.default = artist['website']
    form.seeking_description.default = artist['seeking_description']
    form.seeking_venue.default = artist['seeking_venue']
    form.process()
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@core_module.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # update existing artist record with ID <artist_id> using
    # the new attributes
    try:
        form = ArtistForm(request.form)
        form.genres.choices = DBApi.get_genres()
        form.state.choices = DBApi.get_states()
        if form.validate_on_submit():
            DBApi.edit(Artist, form, artist_id)
            flash('Artist ' + form.name.data + ' was successfully updated!')
            return redirect(url_for('core.show_artist', artist_id=artist_id))
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(
                error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error'
            )
    except Exception:
        flash('An error occurred. Artist ' + form.name.data + ' could not be updated.', 'error')

    artist = dict(request.form)
    artist.update({'id': artist_id})
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@core_module.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    try:
        venue = DBApi.get_by_id(Venue, venue_id)
        genre_choices = DBApi.get_genres()
        state_choices = DBApi.get_states()
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    # Prepare the form for editing
    form = VenueForm()
    form.genres.choices = genre_choices
    form.state.choices = state_choices
    form.name.default = venue['name']
    form.phone.default = venue['phone']
    form.address.default = venue['address']
    form.genres.default = venue['genres']
    form.state.default = venue['state']
    form.city.default = venue['city']
    form.facebook_link.default = venue['facebook_link']
    form.image_link.default = venue['image_link']
    form.website.default = venue['website']
    form.seeking_description.default = venue['seeking_description']
    form.seeking_talent.default = venue['seeking_talent']
    form.process()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@core_module.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        form = VenueForm(request.form)
        form.genres.choices = DBApi.get_genres()
        form.state.choices = DBApi.get_states()
        if form.validate_on_submit():
            DBApi.edit(Venue, form, venue_id)
            flash('Venue ' + form.name.data + ' was successfully updated!')
            return redirect(url_for('core.show_venue', venue_id=venue_id))
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(
                error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error'
            )
    except Exception as e:
        flash('An error occurred. Venue ' + form.name.data + ' could not be updated.', 'error')
    venue = dict(request.form)
    venue.update({'id': venue_id})
    return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------


@core_module.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    form.genres.choices = DBApi.get_genres()
    form.state.choices = DBApi.get_states()
    return render_template('forms/new_artist.html', form=form)


@core_module.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        form = ArtistForm(request.form)
        form.genres.choices = DBApi.get_genres()
        form.state.choices = DBApi.get_states()
        if form.validate_on_submit():
            DBApi.create(Artist, form)
            flash('Artist ' + form.name.data + ' was successfully listed!')
            return render_template('pages/home.html')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except Exception:
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')
    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@core_module.route('/shows')
def shows():
    # displays list of shows at /shows
    try:
        data = DBApi.get_shows()
    except Exception:
        flash('Oops something went wrong.', 'error')
        return render_template('pages/home.html')
    return render_template('pages/shows.html', shows=data)


@core_module.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@core_module.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        form = ShowForm(request.form)
        if form.validate():
            DBApi.create_show(form)
            flash('Show was successfully listed!')
            return render_template('pages/home.html')
        for error in form.errors:
            error_message = str(form.errors[error][0])
            flash(error.capitalize().replace('_', ' ') + ' - ' + error_message.strip('(\'.,)'), 'error')
    except ValueError as error:
        error_message = error.args[0].strip('(\'.,)')
        flash(error_message, 'error')
    except Exception:
        flash('An error occurred. Show could not be listed.', 'error')
    return render_template('forms/new_show.html', form=form)
