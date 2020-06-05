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

@cache.memoize(timeout=3600)
def __get_milestone_data():
  logger.info('Get milestone data for dashboard')
  retval = gl.get_milestones(settings.GITLAB_GROUP_ID)
  logger.info('Finished composing milestone data for dashboard')
  return retval

@cache.memoize(timeout=3600)
def __get_pipeline_data():
  logger.info('Get pipeline data for dashboard')
  
  retval = []
  [retval.extend(gl.get_pipelines(project['id'], 
      project['ref_name'] if 'ref_name' in project else 'master'))
  for project in projects]
  logger.info('Finished composing pipeline data for dashboard')
  return retval

@cache.memoize(timeout=3600)
def __get_deployment_data():
  logger.info('Get deployment data for dashboard')
  retval = []
  for project in projects:
    retval.extend(gl.get_deployments(project['id']))
  logger.info('Finished composing deployment data for dashboard')
  return retval

@cache.memoize(timeout=3600)
def __get_commit_data():
  logger.info('Get commit data for dashboard')
  retval = []
  for project in projects:
    ref_name = project['ref_name'] if 'ref_name' in project else 'master'
    retval.extend(gl.get_commits(project['id'], ref_name))
  logger.info('Finished composing commit data for dashboard')
  return retval

#######

@app.callback(
  Output('memory-pipelines', 'data'),
  [Input('session-update-hourly', 'n_intervals')])
def signal_pipelines(n_intervals):
  return __get_pipeline_data()

@app.callback(
  Output('memory-commits', 'data'),
  [Input('session-update-hourly', 'n_intervals')])
def signal_commits(n_intervals):
  return __get_commit_data()

@app.callback(
  Output('memory-deployments', 'data'),
  [Input('session-update-hourly', 'n_intervals')])
def signal_deployments(n_intervals):
  return __get_deployment_data()

@app.callback(
  Output('memory-milestones', 'data'),
  [Input('session-update-hourly', 'n_intervals')])
def signal_milestones(n_intervals):
  return __get_milestone_data()