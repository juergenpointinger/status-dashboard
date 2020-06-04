# Standard library imports
from datetime import datetime, timedelta
import json
import logging

# Third party imports
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import pandas as pd
from pandas import json_normalize
import plotly.graph_objects as go

# Local application imports
from app import app
from modules.gitlab import GitLab
import settings
from . import layouts, signals

logger = logging.getLogger(__name__)

projects = settings.GITLAB_PROJECT_IDS['projects'] if 'projects' in settings.GITLAB_PROJECT_IDS else None
if projects is None:
  raise Exception("No GitLab projects available")

gl = GitLab()

def normalize_session_hourly_data():
  logger.debug('Normalize hourly data')
  data = signals.get_session_hourly_data()
  if data is None:
    logger.debug('[ISSUES] No data available, prevent update for now')
    raise PreventUpdate
  elif 'milestones' not in data:
    logger.warning('[ISSUES] No milestone data available, prevent update for now')
    raise PreventUpdate
  if len(data['milestones']) == 0:
    logger.warning('[ISSUES] Empty milestone data, prevent update for now')
    raise PreventUpdate
  normalized_data = json_normalize(data['milestones'])
  return normalized_data

def normalize_session_short_data(data_type, project_id):
  logger.debug('Normalize short data: ' + data_type)
  data = signals.get_session_short_data()
  if data is None or data_type not in data or len(data[data_type]) == 0:
    return []
  
  df = json_normalize(data[data_type])

  if 'project_id' not in df:
    return []

  retval = df[df['project_id'] == project_id]
  if len(retval) == 0:
    return []
  return retval

def register_callbacks():
  """Register application callbacks"""
  __register_group_callbacks()
  [__register_project_callbacks(project['id'], project['ref_name'] if 'ref_name' in project else 'master')
  for project in projects]

def __register_group_callbacks():
  """Register group specific callbacks"""
  logger.info('Register group callbacks')
  
  @app.callback(Output('graph_group_velocity', 'figure'),
    [Input('session-hourly', 'children')])
  def __render_velocity(signal):
    milestones = normalize_session_hourly_data()
    
    velocity_by_milestone = milestones.groupby('milestone.title')[['weight']].sum()
    closed_by_milestone = milestones.query('state=="closed"').groupby('milestone.title')[['weight']].sum()

    # Drop unnecessary columns
    # milestones = milestones[['id', 'title', 'total', 'closed']]

    return go.Figure(
      data=[
        go.Bar(
          name='Total',
          x=velocity_by_milestone.index, 
          y=velocity_by_milestone.weight,
          text=velocity_by_milestone.weight,
          textposition='auto',
          marker_color='rgb(168, 216, 234)',
          marker_line_color='rgba(0, 0, 0, 0)',
          opacity=0.5),
        go.Bar(
          name='Closed',
          x=closed_by_milestone.index, 
          y=closed_by_milestone.weight,
          text=closed_by_milestone.weight,
          textposition='auto',
          marker_color='rgb(95, 122, 209)',
          marker_line_color='rgba(0, 0, 0, 0)',
          opacity=0.5)
      ],
      layout=go.Layout(
        title=go.layout.Title(text="Velocity"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title='Weights'
      ))

  @app.callback(Output('graph_group_issues', 'figure'),
    [Input('session-hourly', 'children')])
  def __render_issues(signal):
    milestones = normalize_session_hourly_data()

    ts = pd.Timestamp
    milestones['issue_created'] = pd.to_datetime(milestones['created_at'])
    milestones['issue_created'] = pd.to_datetime(milestones['issue_created'], utc=True)
    milestones['issue_updated'] = pd.to_datetime(milestones['updated_at'])
    milestones['issue_updated'] = pd.to_datetime(milestones['issue_updated'], utc=True)
    milestones['milestone.started'] = pd.to_datetime(milestones['milestone.start_date'])
    milestones['milestone.started'] = pd.to_datetime(milestones['milestone.started'], utc=True)

    # Show created issues by milestone
    mask = milestones['issue_created'] > milestones['milestone.started']
    created_issues = milestones.loc[mask]
    created_by_milestone = created_issues.groupby('milestone.title')[['id']].count()
    created_by_milestone = created_by_milestone.rename(columns = {'id': 'issue_count'})

    # Show updated issues by milestone
    mask = milestones['issue_updated'] > milestones['milestone.started']
    updated_issues = milestones.loc[mask]
    udpated_by_milestone = updated_issues.groupby('milestone.title')[['id']].count()
    udpated_by_milestone = udpated_by_milestone.rename(columns = {'id': 'issue_count'})

    # Show defects
    defects_by_milestone = milestones[milestones['labels'].apply(lambda x: 'Bug::high' in x or 'Bug::medium' in x or 'Bug::low' in x)]
    defects_by_milestone= defects_by_milestone.groupby('milestone.title')[['id']].count()
    defects_by_milestone = defects_by_milestone.rename(columns = {'id': 'issue_count'})

    return go.Figure(
      data=[
        go.Bar(
          name='Created',
          x=created_by_milestone.index, 
          y=created_by_milestone.issue_count,
          text=created_by_milestone.issue_count,
          textposition='auto',
          marker_color='rgb(168, 216, 234)',
          marker_line_color='rgba(0, 0, 0, 0)',
          opacity=0.5),
        go.Bar(
          name='Updated',
          x=udpated_by_milestone.index, 
          y=udpated_by_milestone.issue_count,
          text=udpated_by_milestone.issue_count,
          textposition='auto',
          marker_color='rgb(95, 122, 209)',
          marker_line_color='rgba(0, 0, 0, 0)',
          opacity=0.5),
        go.Bar(
          name='Defects',
          x=defects_by_milestone.index, 
          y=defects_by_milestone.issue_count,
          text=defects_by_milestone.issue_count,
          textposition='auto',
          marker_color='rgb(227, 120, 104)',
          marker_line_color='rgba(0, 0, 0, 0)',
          opacity=0.5)
      ],
      layout=go.Layout(
        title=go.layout.Title(text="Issues"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title = 'Count'
      ))

def __register_project_callbacks(project_id, ref_name):
  """Register project specific callbacks"""
  logger.info('Register project ({}) callbacks'.format(project_id))

  ###############################################################
  ## Deployments

  @app.callback(
    [Output('project-{}-deployments'.format(project_id), 'figure'),
     Output('project-{}-deployments-details'.format(project_id), 'children')],
    [Input('session-short', 'children')])
  def __render_deployments(signal):
    deployments = normalize_session_short_data('deployments', project_id)

    if len(deployments) == 0:
      return layouts.render_empty_plot_layout("Deployments by date", 400), []
    
    deployments['date'] =  pd.to_datetime(deployments['created_at'])
    deployments['date'] =  pd.to_datetime(deployments['date'], utc=True)
    deployments['deployment_date'] = deployments['date'].dt.date

    # Drop unnecessary columns
    deployments = deployments[['id', 'deployment_date', 'status', 'environment.name']]

    # Show only successful deployments
    staging_deployments = deployments.query('`environment.name`=="staging"')
    staging_deployments_by_day = staging_deployments.groupby('deployment_date')[['id']].count()
    staging_deployments_by_day = staging_deployments_by_day.rename(columns = {'id': 'deployment_count'})

    production_deployments = deployments.query('`environment.name`=="production"')
    production_deployments_by_day = production_deployments.groupby('deployment_date')[['id']].count()
    production_deployments_by_day = production_deployments_by_day.rename(columns = {'id': 'deployment_count'})

    fig = go.Figure(
      data=[
        go.Scatter(
          name='Staging',
          x=staging_deployments_by_day.index, 
          y=staging_deployments_by_day.deployment_count,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(168, 216, 234, 0.5)',
        ),
        go.Scatter(
          name='Production',
          x=production_deployments_by_day.index, 
          y=production_deployments_by_day.deployment_count,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(76, 175, 80, 0.5)',
        )
      ],
      layout=go.Layout(
        title=go.layout.Title(text="Deployments by date"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title='Deployments',
        height=400
      ))
    
    details = html.Span([
      dbc.Button(
        ["Staging", dbc.Badge(len(staging_deployments), color="light", className="ml-1")],
        outline=True, color="info", size="sm", className="mr-1"
      ),
      dbc.Button(
        ["Production", dbc.Badge(len(production_deployments), color="light", className="ml-1")],
        outline=True, color="info", size="sm", className="mr-1"
      )])
    return fig, details

  ###############################################################
  ## Commits

  @app.callback(
    Output('project-{}-commits'.format(project_id), 'figure'),
    [Input('session-short', 'children')])
  def __render_commits(signal):
    commits = normalize_session_short_data('commits', project_id)

    if len(commits) == 0:
      return layouts.render_empty_plot_layout("Commits by date", 400)

    commits['date'] = pd.to_datetime(commits['created_at'])
    commits['date'] = pd.to_datetime(commits['date'], utc=True)
    commits['commit_date'] = commits['date'].dt.date

    # Drop unnecessary columns
    commits = commits[['short_id', 'author_name', 'commit_date']]

    commits_by_day = commits.groupby('commit_date')[['short_id']].count()
    commits_by_day = commits_by_day.rename(columns = {'short_id': 'commit_count'})

    return go.Figure(
      data=[go.Scatter(
        x=commits_by_day.index, 
        y=commits_by_day.commit_count, 
        text=commits_by_day.commit_count,
        mode='none',
        line_shape='spline',
        fill='tozeroy',
        fillcolor = 'rgba(168, 216, 234, 0.5)',
      )],
      layout=go.Layout(
        title=go.layout.Title(text="Commits by date"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title = 'Commits',
        height=400
      ))

  ###############################################################
  ## Pipelines

  @app.callback(
    Output('project-{}-pipelines'.format(project_id), 'figure'),
    [Input('session-short', 'children')])
  def __render_pipelines(signal):
    pipelines = normalize_session_short_data('pipelines', project_id)

    if len(pipelines) == 0:
      return layouts.render_empty_plot_layout("Pipeline runs by date", 400)

    pipelines['date'] = pd.to_datetime(pipelines['created_at'])
    pipelines['date'] = pd.to_datetime(pipelines['date'], utc=True)
    pipelines['pipeline_date'] = pipelines['date'].dt.date

    # Drop unnecessary columns
    pipelines = pipelines[['sha', 'pipeline_date', 'status', 'coverage']]

    success_by_date = pipelines.query('status=="success"').groupby('pipeline_date')[['sha']].count()
    success_by_date = success_by_date.rename(columns = {'sha': 'value'})

    failed_by_date = pipelines.query('status=="failed"').groupby('pipeline_date')[['sha']].count()
    failed_by_date = failed_by_date.rename(columns = {'sha': 'value'})

    return go.Figure(
      data=[
        go.Bar(
          name='Success',
          x=success_by_date.index, 
          y=success_by_date.value,
          text=success_by_date.value,
          textposition='auto',
          marker_color='rgba(76, 175, 80, 0.5)',
          marker_line_color='rgba(0, 0, 0, 0)'),
        go.Bar(
          name='Failed',
          x=failed_by_date.index,
          y=failed_by_date.value,
          text=failed_by_date.value,
          textposition='auto',
          marker_color='rgba(227, 120, 104, 0.5)',
          marker_line_color='rgba(0, 0, 0, 0)')
      ],
      layout=go.Layout(
        title=go.layout.Title(text="Pipeline runs by date"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title = 'Pipeline runs',
        height=400
      ))

  @app.callback(
    Output('project-{}-badges'.format(project_id), 'children'),
    [Input('session-short', 'children')])
  def __render_badges(signal):
    retval = []
    pipelines = normalize_session_short_data('pipelines', project_id)

    sort_by_id = pipelines
    if len(pipelines) > 0:
      sort_by_id = pipelines.sort_values('id')

    latest_status = 'unknown'
    latest_url = '#'
    latest_coverage = 0.0
    latest_tests_total = 0

    status_color = 'secondary'
    coverage_trend = 0
    coverage_trend_color = 'secondary'
    
    tests_total_trend = 0
    tests_total_trend_color = 'secondary' 

    first_pipeline = sort_by_id.iloc[0] if len(sort_by_id) > 0 else None
    latest_pipeline = sort_by_id.iloc[-1] if len(sort_by_id) > 0 else None
    if latest_pipeline is not None and first_pipeline is not None:
      latest_status = latest_pipeline['status']
      latest_url = latest_pipeline['web_url']
      latest_coverage = float(latest_pipeline['coverage'])
      coverage_trend = latest_coverage - float(first_pipeline['coverage'])
      if 'total_count' in latest_pipeline:
        latest_tests_total = float(latest_pipeline['total_count'])
        tests_total_trend = latest_tests_total - float(first_pipeline['total_count'])
      
    if 'success' == latest_status:
      status_color = 'success'
    elif 'failed' == latest_status:
      status_color = 'danger'
      
    if latest_coverage == 0:
      coverage_trend_color = 'danger'
    elif coverage_trend > 0:
      coverage_trend_color = 'success'
    else:
      coverage_trend_color = 'warning'

    if latest_tests_total == 0:
      tests_total_trend_color = 'danger'
    elif tests_total_trend > 0:
      tests_total_trend_color = 'success'
    else:
      tests_total_trend_color = 'warning'
    
    retval.append(
      html.H5(
        [
          dbc.Badge("pipeline: {}".format(latest_status), href=latest_url, color=status_color, className="mr-1"),
          dbc.Badge("coverage: {:.2f}% ({:+.2f}%)".format(latest_coverage, coverage_trend), href=latest_url, color=coverage_trend_color, className="mr-1"),
          dbc.Badge("tests: {:.0f} ({:+.0f})".format(latest_tests_total, tests_total_trend), href=latest_url, color=tests_total_trend_color, className="mr-1")
        ]))
    return retval

  @app.callback(
    Output('project-{}-coverage'.format(project_id), 'figure'),
    [Input('session-short', 'children')])
  def __render_coverage(signal):
    pipelines = normalize_session_short_data('pipelines', project_id)

    if len(pipelines) == 0:
      return layouts.render_empty_plot_layout("Coverage by date", 500)

    pipelines['date'] =  pd.to_datetime(pipelines['created_at'])
    pipelines['date'] =  pd.to_datetime(pipelines['date'], utc=True)
    pipelines['pipeline_date'] = pipelines['date'].dt.date

    # Drop unnecessary columns
    pipelines = pipelines[['sha', 'pipeline_date', 'status', 'coverage']]

    coverage_by_date = pipelines.groupby('pipeline_date')[['coverage']].agg(np.mean)
    coverage_by_date = coverage_by_date.rename(columns = {'coverage': 'coverage_agg'})

    return go.Figure(
      data=[go.Scatter(
        x=coverage_by_date.index, 
        y=coverage_by_date.coverage_agg,
        mode='none', # lines
        line_shape='spline',
        fill='tozeroy',
        fillcolor = 'rgba(168, 216, 234, 0.5)',
      )],
      layout=go.Layout(
        title=go.layout.Title(text="Coverage by date"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title = 'Coverage',
        height=500
      ))

  @app.callback(
    Output('project-{}-testreport'.format(project_id), 'figure'),
    [Input('session-short', 'children')])
  def __render_testreport(signal):
    pipelines = normalize_session_short_data('pipelines', project_id)

    if len(pipelines) == 0:
      return layouts.render_empty_plot_layout("Tests by date", 500)

    pipelines['date'] =  pd.to_datetime(pipelines['created_at'])
    pipelines['date'] =  pd.to_datetime(pipelines['date'], utc=True)
    pipelines['pipeline_date'] = pipelines['date'].dt.date

    # Drop unnecessary columns
    pipelines = pipelines[['sha', 'pipeline_date', 'total_time', 'total_count', 'success_count', 'failed_count', 'skipped_count', ]]

    total_by_date = pipelines.groupby('pipeline_date')[['total_count']].agg(np.mean)
    total_by_date = total_by_date.rename(columns = {'total_count': 'value'})

    success_by_date = pipelines.groupby('pipeline_date')[['success_count']].agg(np.mean)
    success_by_date = success_by_date.rename(columns = {'success_count': 'value'})

    skipped_by_date = pipelines.groupby('pipeline_date')[['skipped_count']].agg(np.mean)
    skipped_by_date = skipped_by_date.rename(columns = {'skipped_count': 'value'})

    failed_by_date = pipelines.groupby('pipeline_date')[['failed_count']].agg(np.mean)
    failed_by_date = failed_by_date.rename(columns = {'failed_count': 'value'})

    return go.Figure(
      data=[
        go.Scatter(
          name='Total',
          x=total_by_date.index, 
          y=total_by_date.value,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(168, 216, 234, 0.5)',
        ),
        go.Scatter(
          name='Success',
          x=success_by_date.index, 
          y=success_by_date.value,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(76, 175, 80, 0.5)',
        ),
        go.Scatter(
          name='Skipped',
          x=skipped_by_date.index, 
          y=skipped_by_date.value,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(255, 235, 59, 0.5)',
        ),
        go.Scatter(
          name='Failed',
          x=failed_by_date.index, 
          y=failed_by_date.value,
          mode='none', # lines
          line_shape='spline',
          fill='tozeroy',
          fillcolor = 'rgba(227, 120, 104, 0.5)',
        ),
      ],
      layout=go.Layout(
        title=go.layout.Title(text="Tests by date"),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        yaxis_title = 'Tests',
        height=500
      ))