# Standard library imports
from datetime import datetime, timedelta
import json
import logging

# Third party imports
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
from pandas import json_normalize

# Local application imports
from app import app
from modules.gitlab import GitLab
import settings
from . import layouts

logger = logging.getLogger(__name__)

projects = settings.GITLAB_PROJECT_IDS['projects'] if 'projects' in settings.GITLAB_PROJECT_IDS else None
if projects is None:
  raise Exception("No GitLab projects available")

gl = GitLab()

def register_callbacks():
  """Register application callbacks"""  
  [__register_project_callbacks(project['id'], project['ref_name'] if 'ref_name' in project else 'master')
  for project in projects]

def __get_pipeline_data(project_id, ref_name):
  return gl.get_latest_pipeline(project_id, ref_name)

def __get_active_jobs_data(project_id, pipeline_id):
  return gl.get_active_jobs(project_id, pipeline_id)

def __get_inactive_jobs_data(project_id, pipeline_id):
  return gl.get_inactive_jobs(project_id, pipeline_id)

def __get_test_report_data(project_id, pipeline_id):
  return gl.get_test_report(project_id, pipeline_id)

def __register_project_callbacks(project_id, ref_name):
  """Register project specific callbacks"""
  logger.info('Register project ({}) callbacks'.format(project_id))

  @app.callback(
    [Output('card-{}'.format(project_id), 'children'),
     Output('card-{}'.format(project_id), 'color')],
    [Input('session-update-build', 'n_intervals')])
  def render_card(n):
    color = 'secondary'
    data = __get_pipeline_data(project_id, ref_name)    

    if data is None:
      return layouts.render_empty_card_layout()

    pipeline_id = data['id']
    name = data['project_name']
    status = data['status']
    coverage = data['coverage']
    duration = data['duration']
    url = data['web_url']    
    test_report = []

    if 'success' == status:
      color = 'success'
    elif 'running' == status:
      color = 'warning'
    elif 'failed' == status:
      color = 'danger'

    joint_jobs = ''
    if 'failed' == status or 'canceled' == status:
      inactive_jobs = __get_inactive_jobs_data(project_id, pipeline_id)      
      for job in inactive_jobs:
        job_name = job['name']
        if joint_jobs == '':
          joint_jobs = job_name
        else:
          joint_jobs = joint_jobs + ', ' + job_name
    elif 'running' == status or 'manual' == status:
      active_jobs = __get_active_jobs_data(project_id, pipeline_id)      
      for job in active_jobs:
        job_name = job['name']
        if joint_jobs == '':
          joint_jobs = job_name
        else:
          joint_jobs = joint_jobs + ', ' + job_name

    test_details = ''
    if 'failed' == status:
      test_report = __get_test_report_data(project_id, pipeline_id)
      if 'total_count' in test_report and test_report['total_count'] > 0:
        test_details = 'Total ({}): Success ({}), Skipped ({}), Failed ({})'.format(
          test_report['total_count'],
          test_report['success_count'],
          test_report['skipped_count'],
          test_report['failed_count'])

    return [dbc.CardHeader(name),
            dbc.CardBody([
              html.H2(status.upper(), className="mb-2", style={'text-align': 'center'}),
              html.Div(str(timedelta(seconds=duration)), className="mb-2", style={'text-align': 'center'}),
              html.Div(joint_jobs, className="mb-2", style={'text-align': 'center'}),
              html.Div(test_details, className="mb-2", style={'text-align': 'center'}),
              html.Span([
                dbc.Button(
                  "Coverage: {:.2f} %".format(coverage),
                  color="dark", size="sm", className="mr-1", outline=True
                )]),              
              ],              
            ),
            dbc.CardFooter("{} ({})".format(project_id, ref_name))
          ], color