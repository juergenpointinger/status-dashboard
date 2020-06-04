# Standard library imports
import logging

# Third party imports
from dash.dependencies import Input, Output, State

# Local application imports
from app import app, cache
from modules.gitlab import GitLab
import settings

logger = logging.getLogger(__name__)

projects = settings.GITLAB_PROJECT_IDS['projects'] if 'projects' in settings.GITLAB_PROJECT_IDS else None
if projects is None:
  raise Exception("No GitLab projects available")

gl = GitLab()

#######

def query_milestone_data():
  logger.info('Query milestone data')
  return gl.get_milestones(settings.GITLAB_GROUP_ID)

def query_pipeline_data():
  logger.info('Query pipeline data')
  frames = []
  for project in projects:
    ref_name = project['ref_name'] if 'ref_name' in project else 'master'
    frames.extend(gl.get_pipelines(project['id'], ref_name))
  return frames

def query_deployment_data():
  logger.info('Query deployment data')
  frames = []
  for project in projects:
    frames.extend(gl.get_deployments(project['id']))
  return frames

def query_commit_data():
  logger.info('Query commit data')
  frames = []
  for project in projects:
    ref_name = project['ref_name'] if 'ref_name' in project else 'master'
    frames.extend(gl.get_commits(project['id'], ref_name))
  return frames

#######

@cache.cached(key_prefix='session_short')
def get_session_short_data():
  logging.info('Get short interval data')

  data = {}
  data.update({'pipelines': query_pipeline_data()})
  data.update({'commits': query_commit_data()})
  data.update({'deployments': query_deployment_data()})

  logging.info('Computed short interval data > Signal')
  return data

@app.callback(
  Output('session-short', 'children'),
  [Input('session-update-short', 'n_intervals')])
def signal_session_short(n):
  logging.info('Got short interval signal ({})'.format(str(n)))
  get_session_short_data()
  return n  

@cache.cached(key_prefix='session_hourly')
def get_session_hourly_data():
  logging.info('Get hourly interval data')

  data = {}
  data.update({'milestones': query_milestone_data()})  

  logging.info('Computed hourly interval data  > Signal')
  return data

@app.callback(
  Output('session-hourly', 'children'),
  [Input('session-update-hourly', 'n_intervals')])
def signal_session_hourly(n):
  logging.info('Got hourly interval signal ({})'.format(str(n)))
  get_session_hourly_data()
  return n