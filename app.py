#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import traceback
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from sqlalchemy import *
from models import db, Artist, Venue, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  VENUES
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
 
  data = []
  areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

  for area in areas:
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venues = []
    for venue in area_venues:
      venues.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all())
      })

    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venues
    })
  
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  data = []
  search_input = request.form.get('search_term')
  search = Venue.query.filter(Venue.name.ilike(f'%{search_input}%')).all()

  for result in search:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  response={
    "count": len(search),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  
  venue = Venue.query.get(venue_id)

  if not venue:
    return render_template('errors/404.html')
  
  get_upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  get_past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in get_upcoming_shows:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name":show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  

  for show in get_past_shows:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
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
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
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
  venue_form = VenueForm(request.form)
  
  try:
    venue = Venue(
      name = venue_form.name.data,
      city = venue_form.city.data,
      state = venue_form.state.data,
      address = venue_form.address.data,
      phone = venue_form.phone.data,
      genres = ','.join(venue_form.genres.data),
      image_link = venue_form.image_link.data,
      facebook_link = venue_form.facebook_link.data,
      website = venue_form.website_link.data,
      seeking_talent = venue_form.seeking_talent.data,
      seeking_description = venue_form.seeking_description.data
    )

    db.session.add(venue)
    db.session.commit()
    print(venue)
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue_form.name.data + ' could not be listed.')
    traceback.print_exc()

  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  venue = Venue.query.get(venue_id)
  
  if not venue:
    return render_template('errors/404.html')
    
  try:
    db.session.delete(venue)
    db.session.commit()

    flash('Venue ' + venue.name + ' was successfully deleted')
    
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted')
  finally:
    db.session.close()
  
    return redirect(url_for("index"))
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = Artist.query.all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  data = []
  search_input = request.form.get('search_term')
  search = Artist.query.filter(Artist.name.ilike(f'%{search_input}%')).all()

  for result in search:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })

  response={
    "count": len(search),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  if not artist:
    return render_template('errors/404.html')

  get_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  get_past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in get_upcoming_shows:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name":show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  

  for show in get_past_shows:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

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
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = Artist.query.get(artist_id)
  if artist:
    artist_data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres.split(','),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website_link": artist.website,
      "facebook_link": artist.facebook_link,
      "image_link": artist.image_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
    }
    form = ArtistForm(data=artist_data)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = Artist.query.get(artist_id)

  try:
    
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = ','.join(form.genres.data)
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    db.session.commit()
    flash(f'Artist {artist.name} was successfully edited!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be edited.')
    traceback.print_exc()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)

  if venue:
    venue_data = {
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
    "image_link": venue.image_link
  }

  form = VenueForm(data=venue_data)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.filter_by(id=venue_id).one()

  try:
    
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.genres = ','.join(form.genres.data)
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully edited!')
  except:
    db.session.rollback()
    print(json.dumps(request.form))

    flash(f'An error occurred. Venue {venue.seeking_talent} could not be edited.')
    traceback.print_exc()
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

  try:
    artist = Artist(
      name = artist_form.name.data,
      city = artist_form.city.data,
      state = artist_form.state.data,
      phone = artist_form.phone.data,
      genres = ','.join(artist_form.genres.data),
      facebook_link = artist_form.facebook_link.data,
      image_link = artist_form.image_link.data,
      website = artist_form.website_link.data,
      seeking_venue = artist_form.seeking_venue.data,
      seeking_description = artist_form.seeking_description.data
    )
    db.session.add(artist)
    db.session.commit()
  
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist_form.name.data + ' could not be listed.')
    traceback.print_exc()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  
  data = []
  shows = Show.query.join(Artist).join(Venue).all()
  
  for show in shows:
    data.append({
      "id": show.id,
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
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

  try:
    show = Show(
      artist_id = show_form.artist_id.data,
      venue_id = show_form.venue_id.data,
      start_time = show_form.start_time.data
    )

    db.session.add(show)
    db.session.commit()
    
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
    traceback.print_exc()

  
  return render_template('pages/home.html')


@app.route('/shows/search', methods=['POST'])
def search_shows():

  data = []
  search_input = request.form.get('search_term')
  search = db.session.query(Show).join(Venue, Artist).filter(or_(Artist.name.ilike(f'%{search_input}%'), Venue.name.ilike(f'%{search_input}%'))).all()
  
  for result in search:
    data.append({
      "id": result.id,
      "venue_id": result.venue_id,
      "venue_name": result.venue.name,
      "artist_id": result.artist_id,
      "artist_name": result.artist.name,
      "artist_image_link": result.artist.image_link,
      "start_time": result.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  response={
    "count": 3,
    "data": data
  }
  return render_template('pages/show.html', results=response, search_term=request.form.get('search_term', ''))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
