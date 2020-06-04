# Standard library imports
import uuid

# Third party imports
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Local application imports
from app import app
from apps import dashboard, monitor
import settings

server = app.server

app.layout = html.Div([
  # Current window location for multi-page application
  dcc.Location(id='url', refresh=False),
    
  # Session based id
  html.Div(str(uuid.uuid4()), id='session-id', style={'display': 'none'}),
  html.Div(id='session-short', style={'display': 'none'}),
  html.Div(id='session-hourly', style={'display': 'none'}),
  html.Div(id='session-daily', style={'display': 'none'}),

  # Page
  html.Div(id='page'),

  # Interval
  dcc.Interval(id='session-update-daily', interval=1*86400000, n_intervals=0),
  dcc.Interval(id='session-update-hourly', interval=1*3600000, n_intervals=0),
  dcc.Interval(id='session-update-short', interval=1*600000, n_intervals=0), # 10 minutes
  dcc.Interval(id='session-update-build', interval=1*30000, n_intervals=0), # 30 seconds
])

@app.callback(Output('page', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname == '/dashboard':
         return dashboard.layout
    elif pathname == '/monitor':
        return monitor.layout    
    else:
        return '404'

if __name__ == '__main__':
  app.run_server(debug=settings.DEBUG, host=settings.APP_HOST, port=settings.APP_PORT)