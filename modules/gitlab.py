import requests
from datetime import datetime, timedelta
import settings
import logging

logger = logging.getLogger(__name__)

class GitLab():

  def __init__(self):
    self.api = settings.GITLAB_API_URL    # instance variable unique to each instance
    self.gl_session = requests.Session()
    self.gl_session.headers = {
      'PRIVATE-TOKEN': settings.GITLAB_TOKEN
    }
    self.gl_session.verify=True

  # We want to see the last 2 weeks
  def timespan(self):
    return datetime.now() - timedelta(days=14)

  def get_request(self, endpoint):
    url = self.api + endpoint
    logger.debug('GitLab request: ' + url)  
    response = self.gl_session.get(url = url)

    if response.status_code != 200:
      logger.error('{}: {}'.format(endpoint, response.text))
    return response

  def get_all_pages(self, endpoint):
    retval = []
    query_separator = '&' if endpoint.find('?') != -1 else '?'

    page_index = 1
    next = True
    while next == True:
      
      response = self.get_request(endpoint + query_separator + 'page={}&per_page=100'.format(page_index) )
      retval = retval + response.json()

      if 'X-Next-Page' in response.headers and not response.headers['X-Next-Page']:
        next = False
      if 'X-Next-Page' in response.headers and response.headers['X-Next-Page']:
        if int(response.headers['X-Next-Page']) <= page_index:
          next = False
      if 'X-Next-Page' not in response.headers:
        next = False
      page_index = page_index + 1
    return retval

  ##########################################################

  def get_group_name(self, group_id):
    response = self.get_request('/groups/{}'.format(group_id))
    if response.status_code == 200:
      return response.json()['name']
    return ''

  def get_project_name(self, project_id):
    response = self.get_request('/projects/{}'.format(project_id))
    if response.status_code == 200:
      return response.json()['name']
    return ''

  ##########################################################

  def get_commits(self, project_id, ref_name):
    issues = self.get_all_pages('/projects/{}/repository/commits?ref_name={}&since={}'.format(project_id, ref_name, self.timespan()))
    retval = [dict(issue, **{'project_id': project_id}) for issue in issues]
    return retval

  ##########################################################

  def get_issues(self, group_id, search):
    return self.get_all_pages('/groups/{}/issues?{}&scope=all'.format(group_id, search))

  ##########################################################

  def get_weights(self, group_id, search):
    issues = self.get_issues(group_id, search)
    
    total_issue_weight = 0
    closed_issue_weight = 0
    for issue in issues:
      issue_id = issue['id']
      issue_state = issue['state']

      # Weights
      issue_weight = (issue['weight'] if issue['weight'] is not None else 0)
      total_issue_weight += issue_weight
      if issue_state == 'closed' and issue_weight > 0:
        closed_issue_weight += issue_weight
    return { 'total': total_issue_weight, 'closed': closed_issue_weight }

  def no_upcoming_milestones_predicate(self, milestone):
    today = datetime.now().strftime("%Y-%m-%d")
    return (milestone['due_date'] >= today and milestone['start_date'] <= today) or milestone['state'] == 'closed'
    
  def sort_by_milestone_title(self, milestone):
    return milestone['title']

  def get_milestones(self, group_id):
    milestones = self.get_all_pages('/groups/{}/milestones?search=Sprint'.format(group_id))
    if len(milestones) == 0:
      return []

    milestones = list(filter(self.no_upcoming_milestones_predicate, milestones))
    milestones.sort(key=self.sort_by_milestone_title)
    milestones = milestones[-5:]

    retval = []
    for milestone in milestones:
      milestone_id = str(milestone['id'])
      issues = self.get_all_pages('/groups/{}/milestones/{}/issues'.format(group_id, milestone_id))
      if len(issues) > 0:
        retval = retval + issues
    return retval

  ##########################################################

  def get_pipelines(self, project_id, ref_name):
    pipelines = self.get_all_pages('/projects/{}/pipelines?ref={}&scope=finished&updated_after={}'.format(project_id, ref_name, self.timespan()))
    
    retval = []
    for pipeline in pipelines:
      pipeline_id = pipeline['id']       
      pipeline_details = pipeline.copy()

      response = self.get_request('/projects/{}/pipelines/{}'.format(project_id, pipeline_id))
      detail = response.json() if response.status_code == 200 else None

      response = self.get_request('/projects/{}/pipelines/{}/test_report'.format(project_id, pipeline_id))
      test_report = response.json() if response.status_code == 200 else None

      # Add project id
      pipeline_details.update({'project_id': project_id})

      # Add coverage details
      if detail is not None:
        coverage = detail['coverage'] if detail['coverage'] is not None else 0
        pipeline_details.update({'duration':'{}'.format(detail['duration'])})
        pipeline_details.update({'coverage': float(coverage)})

      # Add test report details
      if test_report is not None:
        pipeline_details.update({'total_time': test_report['total_time']})
        pipeline_details.update({'total_count': test_report['total_count']})
        pipeline_details.update({'success_count': test_report['success_count']})
        pipeline_details.update({'failed_count': test_report['failed_count']})
        pipeline_details.update({'total_time': test_report['total_time']})
        pipeline_details.update({'skipped_count': test_report['skipped_count']})
        pipeline_details.update({'error_count': test_report['error_count']})
      else:
        pipeline_details.update({'total_time': 0})
        pipeline_details.update({'total_count': 0})
        pipeline_details.update({'success_count': 0})
        pipeline_details.update({'failed_count': 0})
        pipeline_details.update({'total_time': 0})
        pipeline_details.update({'skipped_count': 0})
        pipeline_details.update({'error_count': 0})
      
      retval.append(pipeline_details)

    return retval

  ##########################################################

  def get_deployments(self, project_id):
    deployments = self.get_all_pages('/projects/{}/deployments?&updated_after={}&status=success'.format(project_id, self.timespan()))
    retval = [dict(deployment, **{'project_id': project_id}) for deployment in deployments]
    return retval