# Third party imports
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Local application imports
import settings

projects = settings.GITLAB_PROJECT_IDS['projects'] if 'projects' in settings.GITLAB_PROJECT_IDS else None
if projects is None:
  raise Exception("No GitLab projects available")

def render_empty_card_layout():
  return [dbc.CardBody([
    html.H2("No matching data found", className="mb-2", style={'text-align': 'center'})
  ])], 'secondary'

def __card_layout(project_id):
  card_name = 'card-{}'.format(project_id)
  return dbc.Col(dbc.Card(
    id=card_name,
    children=[],
    color="secondary",
    inverse=True,
    className="mt-4"), width=3)

def __serve_cards_layout():
  cards = []
  [cards.append(__card_layout(project['id'])) for project in projects]
  return cards

serve_layout = [
  html.Div(html.H2(settings.APP_NAME)),    
  dbc.Container(id='project', children=dbc.Row(__serve_cards_layout()), fluid=True)
]