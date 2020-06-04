# Standard library imports
import uuid

# Third party imports
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

# Local application imports
from modules.gitlab import GitLab
import settings

projects = settings.GITLAB_PROJECT_IDS['projects'] if 'projects' in settings.GITLAB_PROJECT_IDS else None
if projects is None:
  raise Exception("No GitLab projects available")

gl = GitLab()
group_name = gl.get_group_name(settings.GITLAB_GROUP_ID)

def render_empty_plot_layout(title, height):
  return go.Figure(layout=go.Layout(
    title=go.layout.Title(text=title),
    paper_bgcolor='rgba(0, 0, 0, 0)',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    height=height,
    xaxis_visible=False,
    yaxis_visible=False,
    annotations=[
      dict(
        xref='paper',
        yref='paper',
        text='No matching data found',
        showarrow=False,
        font=dict(
          size=18,
          color='grey'
        )
      )
    ]
  ))

def __tab_layout(project_id):
  content = dbc.Card(dbc.CardBody([
    dbc.Row([          
      dbc.Col(id='project-{}-badges'.format(project_id), width='auto')
    ]),
    
    dbc.Row([
      dbc.Col(dcc.Loading(children=[
        html.Div(dcc.Graph(
          id='project-{}-deployments'.format(project_id),
          figure=render_empty_plot_layout("Deployments by date", 400),
          style={ 'height': '400px' }), style={ 'height': '400px' }),
          html.Div(id='project-{}-deployments-details'.format(project_id))
        ], type='default'),
        width=4
      ),
      dbc.Col(dcc.Loading(children=[
        html.Div(dcc.Graph(
          id='project-{}-pipelines'.format(project_id),
          figure=render_empty_plot_layout("Pipelines runs by date", 400), 
          style={ 'height': '400px' }), style={ 'height': '400px' })
        ], type='default'),
        width=4
      ),
      dbc.Col(dcc.Loading(children=[
        html.Div(dcc.Graph(
          id='project-{}-commits'.format(project_id),
          figure=render_empty_plot_layout("Commits by date", 400),
          style={ 'height': '400px' }), style={ 'height': '400px' })
        ], type='default'),
        width=4
      ),
    ]),

    dbc.Row([        
      dbc.Col(dcc.Loading(children=[
        html.Div(dcc.Graph(
          id='project-{}-coverage'.format(project_id),
          figure=render_empty_plot_layout("Coverage by date", 500), 
          style={ 'height': '500px' }), style={ 'height': '500px' })
        ], type='default'),
        width=6
      ),          
      dbc.Col(dcc.Loading(children=[
        html.Div(dcc.Graph(
          id='project-{}-testreport'.format(project_id),
          figure=render_empty_plot_layout("Tests by date", 500),
          style={ 'height': '500px' }), style={ 'height': '500px' })
        ], type='default'),
        width=6
      ),
    ])
  ]))
  return content

def __serve_projects_layout():
  tabs = []
  [tabs.append(dbc.Tab(
    __tab_layout(project['id']),
    label=gl.get_project_name(project['id']),
    tab_id='tab-{}'.format(project['id']))) for project in projects]
  return tabs

def __serve_group_layout():
  return [dbc.Row(dbc.Col(html.Div(html.H3('Group ({})'.format(group_name))), width="auto")),
          dbc.Row([
            dbc.Col(dcc.Loading(children=[
              html.Div(dcc.Graph(
                id='graph_group_velocity',
                figure=render_empty_plot_layout("Velocity", 450)))    
              ], type='default'),
              width=6
            ),
            dbc.Col(dcc.Loading(children=[
              html.Div(dcc.Graph(
                id='graph_group_issues',
                figure=render_empty_plot_layout("Issues", 450)))
              ], type='default'),
              width=6
            ),
          ]),
        ]

serve_layout = [
  # Header
  dbc.Row(dbc.Col(html.Div(html.H2(settings.APP_NAME)), width="auto")),
  
  # Group
  html.Div(id='group', children=__serve_group_layout()),

  # Projects
  html.Div(id='project', children=[
    dbc.Tabs(id='project-tabs', card=True, children=__serve_projects_layout()),
    dbc.CardBody(dcc.Loading(children=[html.P(id="project-card-content")], type="circle")),
  ]),
]