from flask import Flask, render_template
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

import logging
from logging import Formatter, FileHandler
from dotenv import load_dotenv
import dateutil.parser
import babel

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Enable CSRF protection
csrf = CSRFProtect(app)

moment = Moment(app)

# Configurations
app.config.from_object('config')

# Define database object to be imported by modules and controllers
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
# Error Handlers
# ----------------------------------------------------------------------------#


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

# ----------------------------------------------------------------------------#
# Register blueprint
# ----------------------------------------------------------------------------#


from app.core.controllers import core_module as core  # noqa: E302

app.register_blueprint(core)

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')
