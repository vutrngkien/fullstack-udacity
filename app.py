# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String())
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='venues')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='artists')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)


with app.app_context():
    db.create_all()
# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


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
    data = []
    venue_group = db.session.query(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    for venue in venue_group:
        venue_dict = {}
        venue_dict['city'] = venue[0]
        venue_dict['state'] = venue[1]
        result_venue = db.session.query(Venue.id, Venue.name).filter(
            Venue.city == venue_dict['city']).all()
        venues = []
        for el in result_venue:
            venue = {}
            venue['id'] = el[0]
            venue['name'] = el[1]
            venue['num_upcoming_shows'] = len(db.session.query(Show.start_time).filter(
                Show.venue_id == venue['id'], Show.start_time >= func.NOW()).all())
            venues.append(venue)
        venue_dict['venues'] = venues
        data.append(venue_dict)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    venues = Venue.query.filter(Venue.name.ilike(
        "%{}%".format(request.form.get('search_term', '')))).all()
    response = {
        "data": [],
        "count": len(venues),
    }
    for v in venues:
        response["data"].append({
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": len(db.session.query(Show.start_time).filter(Show.venue_id == v.id, Show.start_time >= func.NOW()).all())
        })
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue_dict = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
    }

    venue_dict["past_shows_count"] = Show.query.filter(
        Show.venue_id == venue_id, Show.start_time < func.NOW()).count()
    venue_dict["upcoming_shows_count"] = Show.query.filter(
        Show.venue_id == venue_id, Show.start_time >= func.NOW()).count()
    upcoming_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id, Show.start_time >= func.NOW())
    past_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id, Show.start_time < func.NOW())
    for show in upcoming_shows:
        artist = db.session.get(Artist, show.artist_id)
        venue_dict["upcoming_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    for show in past_shows:
        artist = db.session.get(Artist, show.artist_id)
        venue_dict["past_shows"].append({
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    return render_template('pages/show_venue.html', venue=venue_dict)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    venue_form = VenueForm(request.form)
    new_venue = Venue(
        name=venue_form.name.data,
        city=venue_form.city.data,
        state=venue_form.state.data,
        address=venue_form.address.data,
        phone=venue_form.phone.data,
        image_link=venue_form.image_link.data,
        facebook_link=venue_form.facebook_link.data,
        genres=','.join(venue_form.genres.data),
        website=venue_form.website_link.data,
        seeking_talent=venue_form.seeking_talent.data,
        seeking_description=venue_form.seeking_description.data,
    )
    try:
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] +
              ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = db.session.get(Venue, venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + 'was successfully deleted!')
    except:
        db.session.rollback()
        flash('please try again. Venue ' +
              venue.name + ' could not be deleted.')
    finally:
        db.session.close()
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = []
    artists = db.session.query(Artist.id, Artist.name).all()
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name,
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    artists = Artist.query.filter(Artist.name.ilike(
        "%{}%".format(request.form.get('search_term', '')))).all()
    response = {
        "data": [],
        "count": len(artists),
    }
    for a in artists:
        response["data"].append({
            "id": a.id,
            "name": a.name,
            "num_upcoming_shows": len(db.session.query(Show.start_time).filter(Show.artist_id == a.id, Show.start_time >= func.NOW()).all())
        })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = db.session.get(Artist, artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
    }
    upcoming_shows = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time >= func.NOW())
    for s in upcoming_shows:
        venue = db.session.get(Venue, s.venue_id)
        data["upcoming_shows"].append({
            "venue_id": s.venue_id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": s.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    past_shows = db.session.query(Show).join(Artist).filter(
        Show.artist_id == artist_id, Show.start_time < func.NOW())
    for s in past_shows:
        venue = db.session.get(Venue, s.venue_id)
        data["past_shows"].append({
            "venue_id": s.venue_id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": s.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    data["past_shows_count"] = Show.query.filter(
        Show.artist_id == artist_id, Show.start_time < func.NOW()).count()
    data["upcoming_shows_count"] = Show.query.filter(
        Show.artist_id == artist_id, Show.start_time >= func.NOW()).count()
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if not artist:
        return render_template('errors/404.html'), 404
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website_link.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    edit_artist = ArtistForm(request.form)
    try:
        artist = db.session.get(Artist, artist_id)
        artist.name = edit_artist.name.data
        artist.city = edit_artist.city.data
        artist.state = edit_artist.state.data
        artist.phone = edit_artist.phone.data
        artist.facebook_link = edit_artist.facebook_link.data
        artist.genres = ''.join(edit_artist.genres.data)
        artist.website = edit_artist.website_link.data
        artist.image_link = edit_artist.image_link.data
        artist.seeking_venue = edit_artist.seeking_venue.data
        artist.seeking_description = edit_artist.seeking_description.data
        db.session.commit()
        flash('Artist ' + request.form['name'] +
              ' was successfully edited!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be edited.')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = db.session.get(Venue, venue_id)
    if not venue:
        return render_template('errors/404.html'), 404
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    edit_venue = VenueForm(request.form)
    try:
        venue = db.session.get(Venue, venue_id)
        venue.name = edit_venue.name.data
        venue.city = edit_venue.city.data
        venue.state = edit_venue.state.data
        venue.address = edit_venue.address.data
        venue.phone = edit_venue.phone.data
        venue.image_link = edit_venue.image_link.data
        venue.facebook_link = edit_venue.facebook_link.data
        venue.genres = ','.join(edit_venue.genres.data)
        venue.website = edit_venue.website_link.data
        venue.seeking_talent = edit_venue.seeking_talent.data
        venue.seeking_description = edit_venue.seeking_description.data
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be edited.')
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
    artist_form = ArtistForm(request.form)
    new_artist = Artist(
        name=artist_form.name.data,
        city=artist_form.city.data,
        state=artist_form.state.data,
        phone=artist_form.phone.data,
        facebook_link=artist_form.facebook_link.data,
        genres=','.join(artist_form.genres.data),
        website=artist_form.website_link.data,
        image_link=artist_form.image_link.data,
        seeking_venue=artist_form.seeking_venue.data,
        seeking_description=artist_form.seeking_description.data,
    )
    try:
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] +
              ' was successfully listed!')
    except:
        db.session.rollback()
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
    shows = db.session.query(Show)
    for s in shows:
        venue = db.session.get(Venue, s.venue_id)
        artist = db.session.get(Artist, s.artist_id)
        data.append({
            "venue_id": s.venue_id,
            "venue_name": venue.name,
            "artist_id": s.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": s.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    show_form = ShowForm(request.form)
    if db.session.get(Artist, show_form.artist_id.data) and db.session.get(Venue, show_form.venue_id.data):
        new_show = Show(
            artist_id=show_form.artist_id.data,
            venue_id=show_form.venue_id.data,
            start_time=show_form.start_time.data,
        )
        try:
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        flash("An error occurred. the provided IDs don't exist, Show could not be listed.")
    return render_template('pages/home.html')


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
