# Standard library imports
import logging

# Third party imports
import dash
import dash_bootstrap_components as dbc
from flask_caching import Cache
import plotly.io as pio

# Local application imports
import settings

# Initialize logging mechanism
logging.basicConfig(level=settings.LOGLEVEL, format=settings.LOGFORMAT)
logger = logging.getLogger(__name__)

# App Instance
app = dash.Dash(__name__,   
  suppress_callback_exceptions=True,
  external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = settings.APP_NAME
cache = Cache(app.server, config={
  # Note that filesystem cache doesn't work on systems with ephemeral
  # filesystems like Heroku.
  'CACHE_TYPE': 'filesystem',
  'CACHE_DIR': 'cache-directory',

  # should be equal to maximum number of users on the app at a single time
  # higher numbers will store more data in the filesystem / redis cache
  'CACHE_THRESHOLD': 200
})

pio.templates.default = "plotly_dark"