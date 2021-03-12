#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from datetime import datetime
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = Venue.query.distinct(
        Venue.city, Venue.state).order_by('state').all()

    data = []

    for area in areas:
        venues = Venue.query.filter_by(state=area.state).filter_by(
            city=area.city).order_by('name').all()

        venue_data = []

        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_data
        })

        for venue in venues:
            upcoming_shows = db.session.query(Artist, Show). \
                join(Show).join(Venue). \
                filter(
                Show.venue_id == venue.id,
                Show.artist_id == Artist.id,
                Show.start_time > datetime.now()
            ). \
                all()

            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    search_results = Venue.query.filter(
        Venue.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(search_results),
        "data": [{
            "id": search_result.id,
            "name": search_result.name,
            "num_upcoming_shows": len(db.session.query(Artist, Show).
                                      join(Show).join(Venue).
                                      filter(
                Show.venue_id == search_result.id,
                Show.artist_id == Artist.id,
                Show.start_time > datetime.now()
            ).
                all())
        } for search_result in search_results]
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first_or_404()

    past_shows = db.session.query(Artist, Show). \
        join(Show).join(Venue). \
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time < datetime.now()
    ). \
        order_by(Show.start_time.desc()). \
        all()

    upcoming_shows = db.session.query(Artist, Show). \
        join(Show).join(Venue). \
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.now()
    ). \
        order_by(Show.start_time.desc()). \
        all()

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': [{
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in past_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows': [{
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in upcoming_shows],
        'upcoming_shows_count': len(upcoming_shows)
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
    form = VenueForm(request.form)

    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        address = form.address.data
        phone = form.phone.data
        genres = form.genres.data
        facebook_link = form.facebook_link.data
        image_link = form.image_link.data
        website = form.website.data
        seeking_talent = form.seeking_talent.data
        seeking_description = form.seeking_description.data

        venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            website=website,
            image_link=image_link,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )

        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first_or_404()

        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. This venue could not be deleted.')
    finally:
        db.session.close()

    return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term', '')
    search_results = Artist.query.filter(
        Artist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(search_results),
        "data": [{
            "id": search_result.id,
            "name": search_result.name,
            "num_upcoming_shows": len(db.session.query(Artist, Show).
                                      join(Show).join(Venue).
                                      filter(
                Show.venue_id == Venue.id,
                Show.artist_id == search_result.id,
                Show.start_time > datetime.now()
            ).
                all())
        } for search_result in search_results]
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first_or_404()

    past_shows = db.session.query(Venue, Show). \
        join(Show).join(Artist). \
        filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist_id,
        Show.start_time < datetime.now()
    ). \
        order_by(Show.start_time.desc()). \
        all()

    upcoming_shows = db.session.query(Venue, Show). \
        join(Show).join(Artist). \
        filter(
        Show.venue_id == Venue.id,
        Show.artist_id == artist_id,
        Show.start_time > datetime.now()
    ). \
        order_by(Show.start_time.desc()). \
        all()

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': [{
            'venue_id': artist.id,
            'venue_name': artist.name,
            'venue_image_link': artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in past_shows],
        'past_shows_count': len(past_shows),
        'upcoming_shows': [{
            'venue_id': artist.id,
            'venue_name': artist.name,
            'venue_image_link': artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in upcoming_shows],
        'upcoming_shows_count': len(upcoming_shows)
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    form = ArtistForm(request.form)

    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    form = VenueForm(request.form)

    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website = form.website.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)

    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        facebook_link = form.facebook_link.data
        image_link = form.image_link.data
        website = form.website.data
        seeking_venue = form.seeking_venue.data
        seeking_description = form.seeking_description.data

        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            website=website,
            image_link=image_link,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )

        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + artist.name + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []

    shows = Show.query.order_by(Show.start_time.desc()).all()

    for show in shows:
        for artist, venue in db.session.query(Artist, Venue). \
            filter(
            Venue.id == show.venue_id,
            Artist.id == show.artist_id,
        ) \
                .all():
            data.append({
                "venue_id": show.venue_id,
                "artist_id": show.artist_id,
                "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S"),
                "venue_name": venue.name,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
            })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)

    try:
        artist_id = form.artist_id.data
        venue_id = form.venue_id.data
        start_time = form.start_time.data

        show = Show(
            artist_id=artist_id,
            venue_id=venue_id,
            start_time=start_time
        )

        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/shows/search', methods=['POST'])
def search_shows():
    search_term = request.form.get('search_term', '')

    search_results = db.session.query(Show). \
        join(Artist). \
        join(Venue). \
        filter(
        (Artist.name.ilike(f'%{search_term}%')
         | Venue.name.ilike(f'%{search_term}%'))
    ). \
        order_by(Show.start_time.desc()). \
        all()

    data = []

    for search_result in search_results:
        data.append({
            "venue_id": search_result.venue_id,
            "artist_id": search_result.artist_id,
            "start_time": search_result.start_time.strftime("%m/%d/%Y, %H:%M:%S"),
            "venue_name": search_result.venue.name,
            "artist_name": search_result.artist.name,
            "artist_image_link": search_result.artist.image_link,
        })

    return render_template('pages/shows.html', shows=data, search_term=search_term)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
